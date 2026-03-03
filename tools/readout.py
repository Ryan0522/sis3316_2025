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

def readout_loop(dev, destinations, opts=None, quiet=False, print_stats=False,
                 # Swap policy knobs
                 use_fill_swap=True,
                 fill_frac=0.85,
                 use_idle_swap=True,
                 idle_swap_period_s=1.0,
                 idle_epsilon_words=0,
                 min_swap_period_s=0.2,
                 #Timing
                 loop_sleep_s=1.0,
                 ):
    """ 
    Perform endless readout loop. 
    
        destinations: 
            zip(channels, files)
        quiet:
            only errors in stderr
        print_stats:
            print bytes per channel to stderr (ignores `quiet`)
    
    *Note Mar 3, 2026:
        Preserves original printing/stat logic, but replaces unconditional mem_toggle()
        with:
        - Option A: swap when active-bank addr_actual is near addr_threshold
        - Option B: if idle (addr_actual not growing), swap every idle_swap_period_s
        Adds staged recovery on exceptions (arm failures).
    """
    if opts is None:
        opts = {}

    total_bytes = 0
    units = ( ('GB',1024**3), ('MB', 1024**2), ('KB', 1024), ('Bytes', 1))
    
    chan_list = [ch for (ch, _) in destinations]
    last_swap_t = 0.0

    out = ""

    while True:
        try:
            if not dev._readout_status().get("armed", False):
                dev.arm(0)

            now = time.monotonic()

            # poll active bank address counters (words) for the channels we are reading
            act = dev.poll_act(chan_list)  # :contentReference[oaicite:4]{index=4}

            should_swap_fill = False
            if use_fill_swap:
                for idx, ch in enumerate(chan_list):
                    w = act[idx]
                    if w is None:
                        continue
                    thr_bytes = dev.channels[ch].group.addr_threshold  # compared vs actual counter :contentReference[oaicite:5]{index=5}
                    if thr_bytes <= 0:
                        continue
                    thr_words = thr_bytes // 4
                    if thr_words > 0 and w >= int(fill_frac * thr_words):
                        should_swap_fill = True
                        break

            should_swap_periodic = False
            if use_idle_swap:  # reinterpret as "periodic swap"
                max_act = 0
                for w in act:
                    if w is not None and w > max_act:
                        max_act = w

                min_words_to_swap = 256  # tune
                if (now - last_swap_t) >= idle_swap_period_s and max_act >= min_words_to_swap:
                    should_swap_periodic = True

            should_swap = (should_swap_fill or should_swap_periodic)

            if should_swap and (now - last_swap_t) >= min_swap_period_s:
                dev.mem_toggle()  # disarm+arm opposite bank :contentReference[oaicite:6]{index=6}
                last_swap_t = now

            # ---- readout (same structure as original) ----
            recv_bytes = 0
            stats = []
            for ch, file_ in destinations:
                bytes_ = 0
                for ret in dev.readout_pipe(ch, file_, 0, opts ):  # per chunk
                    bytes_ += ret['transfered'] * 4  # words -> bytes               
                stats.append( (ch, bytes_) )    
                recv_bytes += bytes_
                
            total_bytes += recv_bytes
            
            # ---- printing (preserve original logic) ----
            if print_stats or not quiet:
                human_bytes = ''
                for unit, amount in units:
                    if total_bytes > amount:
                        human_bytes = "%d%s" % ((total_bytes)/amount, unit)
                        break

                bytes_str = '' if quiet else "total: %d (%s)      \n" % (total_bytes, human_bytes)
                stats_str = ""
                if print_stats:
                    stats_str = 'chan         bytes\n' + \
                                "\n".join(["%02d\t%10d" % (ch, b) for ch, b in stats])

                out = bytes_str + stats_str
                sys.stderr.write(out + "\033[F" * out.count('\n'))

            time.sleep(loop_sleep_s)

        except KeyboardInterrupt:
            sys.stderr.write('\n' * out.count('\n') + "\nInterrupted.\n")
            raise
            
        except Exception as e:
            _log_err(f"Err: {e}")
            try:
                _recover_adc_arm(dev)
                _log_err("Recovered: ADC re-armed successfully.")
            except Exception as e2:
                _log_err(f"Recovery failed: {e2}")
                time.sleep(0.5)
        
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
