#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read data from SIS3316. 
Write raw (binary) data to files (one file per channel).
"""

import sys,os
import argparse
import time
from time import sleep 
import io
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import sis3316

def _log_err(msg: str):
    timestr = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sys.stderr.write(f"\n{timestr} {msg}\n")

def _recover_adc_arm(dev, *, retries=3, retry_sleep_s=0.005, hard_reset=True):
    """
    Staged recovery:
    1) disarm -> short sleep -> arm (a few retries)
    2) if still failling: ADC-FPGA reset key -> disarm -> arm
    """    
    last_exc = None
    dev.cleanup_socket()
    _log_err("Socket cleaned. Attempting recovery...")

    # Stage 1: soft retries
    for _ in range(retries):
        try:
            dev.disarm()
            sleep(retry_sleep_s)
            dev.arm(0)
            if dev._readout_status().get("armed", False):
                return True
        except Exception as e:
            last_exc = e
            sleep(retry_sleep_s)

    if not hard_reset:
        raise last_exc if last_exc else RuntimeError("arm failed (no exception captured)")
    
    # Stage 2: ADC-FPGA reset (DDR3 + link interface)
    try:
        from sis3316.registers import SIS3316_KEY_ADC_FPGA_RESET
        dev.write(SIS3316_KEY_ADC_FPGA_RESET, 0)
        sleep(0.2)

        dev.disarm()
        sleep(retry_sleep_s)
        dev.arm(0)

        if dev._readout_status().get("armed", False):
            return True
        
        raise RuntimeError("arm still failed after ADC-FPGA reset")
    except Exception as e:
        raise e

def readout_loop(dev, destinations, opts={}, quiet=False, print_stats=False):
    """ 
    Perform endless readout loop. 
    
        destinations: 
            zip(channels, files)
        quiet:
            only errors in stderr
        print_stats:
            print bytes per channel to stderr (ignores `quiet`)
    
    *Note Mar 3, 2026:
        Changed bank swap frequency to 0.05s 
    """
    total_bytes = 0
    human_bytes = ''
    units = ( ('GB',1024**3), ('MB', 1024**2), ('KB', 1024), ('Bytes', 1))
    out = ''

    while True:
        try:
            # 1. Hardware Swap
            dev.mem_toggle()

            recv_bytes = 0
            stats = []

            # 2. Data Readout
            for ch, file_ in destinations:
                bytes_ = 0
                # Transfer from inactive bank
                for ret in dev.readout_pipe(ch, file_, 0, opts):
                    bytes_ += ret['transfered'] * 4
                
                stats.append((ch, bytes_))
                recv_bytes += bytes_

            total_bytes += recv_bytes

            # 3. Stats Generation 
            bytes_str = ''
            stats_str = ''

            if print_stats:
                # bytes per channel
                stats_str = 'chan         bytes\n' \
                    + "\n".join( ["%02d\t%10d" % (ch,b) for ch,b in stats] )
            
            if not quiet:
                # human-readable total_bytes
                for unit, amount in units:
                    if total_bytes > amount:
                        human_bytes = "%d%s" % ((total_bytes)/amount, unit)
                        break
                bytes_str = 'total: %d (%s)      \n' % (total_bytes, human_bytes)
                
            # 4. Progress Printing (Standard ANSI control for terminal)
            if print_stats or not quiet:
                out = bytes_str + stats_str
                # The \033[F moves the cursor up so the stats refresh in-place
                sys.stderr.write(out + "\033[F" * out.count('\n') ) 

            # Heartbeat: 0.05s allows up to 20 bank-swaps per second
            sleep(0.2)

        except KeyboardInterrupt:
            # Clean exit for terminal
            sys.stderr.write('\n' * out.count('\n') + "\nInterrupted.\n")
            return
            
        except Exception as e:
            # Automatic Recovery Trigger
            _log_err(f"Readout Error: {e}")
            try:
                _recover_adc_arm(dev)
            except Exception as recovery_error:
                _log_err(f"Critical Recovery Failure: {recovery_error}")
                sleep(0.5)
        
def makedirs(path):
    """ Create directories for `path` (like 'mkdir -p'). """
    if not path:
        return
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)


def main():
    # Defaults
    chunksize = 1024*1024  # how many bytes to request at once
    opts = {'chunk_size': chunksize/4 }
    OUTPATH = "data/raw-ch"
    OUTEXT = ".dat"
    PORT = 3333
    
    # Set the command line arguments
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
    
    parser.add_argument( 'host',
        type=str,
        help="hostname or ip address."
        )
    parser.add_argument('port',
        type=int,
        nargs='?',
        default=PORT,
        help="UDP port number, default is %d" % PORT
        )
    parser.add_argument('-c', '--channels',
        metavar='N',
        nargs='+',
        type=int,
        default=range(0,16),
        help="channels to read, from 0 to 15 (all by default). \n"\
        "Use shell expressionsto specify a range (like \"{0..7} {12..15}\")."
        )
    parser.add_argument('-o','--output',
        type=str,
        metavar='PATH',
        default=OUTPATH,
        help="a path for output, one file per channel."\
            "\ndefault: \"%s\"" % OUTPATH
        )
    parser.add_argument('-q', '--quiet',
        action='store_true',
        help="be quiet in stderr"
        )
    parser.add_argument('--stats',
        action='store_true',
        help="print statistics per channel (ignores --quiet)"
        )
    
            
    # Parse arguments
    args = parser.parse_args()
    #~ print args
    
    for x in args.channels:
        if not 0 <= x <= 15:
            sys.stderr.write("%d is not a valid channel number!\n" %x)
            exit(1)

    # --channels
    channels = sorted(set(args.channels)) # deduplicate

    # --output
    outpath = args.output
    makedirs(outpath)
    outfiles = [outpath + "%02d"%chan + OUTEXT for chan in channels]

    # check no overwrite
    for outfile in outfiles:
        if os.path.exists(outfile) \
        and os.path.getsize(outfile) != 0:
            sys.stderr.write("File \"%s\" exists and not empty! " \
                "Not going to overwrite it.\n" % outfile )
            exit(1)
    
    # Prepare device
    host,port = args.host, args.port
    dev = sis3316.Sis3316_udp(host, port)
    dev.open()
    if not dev.configure():  # set channel numbers and so on.
        sys.stderr.write('Warning: After configure(), dev.status = false\n')
    dev.disarm()
    dev.arm()
    dev.ts_clear()
    dev.mem_toggle()  # flush the device memory to not to read a large chunk of old data

    if not args.quiet:
        if 'jumbo_ena' in getattr(dev,'flags'):
            jumbo = True
        else:
            jumbo = False
        sys.stderr.write("ADC id: %s, serial: %s, temp: %d °C, jumbo_frame: %s" %( str(dev.id), hex(dev.serno), dev.temp, jumbo) + '\n' )
        sys.stderr.write( str(dev._readout_status()) + '\n')
        sys.stderr.write("---\n")

    # Open files
    files_ = [io.FileIO( name, 'w') for name in outfiles] 

    # Perform readout
    destinations = list(zip( get_iterable(channels), get_iterable(files_) ))  # Python3 has changed zip behavior, need to wrap in list()
    readout_loop(dev, destinations, opts, quiet=args.quiet, print_stats=args.stats)


def get_iterable(x):
    """ Allows lists of one object to be zipped """
    from collections.abc import Iterable
    if isinstance(x, Iterable):
        return x
    else:
        return(x,)

if __name__ == "__main__":
    main()
