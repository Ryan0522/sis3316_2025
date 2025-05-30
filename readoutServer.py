#!/usr/bin/env python
'''ZMQ server for sis3316 config loading and data readout'''
import os, sys, argparse, json, io, zmq, time
from multiprocessing import Process, Queue
import sis3316
#sys.path.append('./tools')
from tools.conf import conf_load
from tools.readout import readout_loop, get_iterable, makedirs


from zmqGlobals import *


def readout_process( dev, channels, outfiles ):
    '''Readout from sis3316. dev should be opened already
    '''

    # Prepare device
    if not dev.configure():  # set channel numbers and so on.
        sys.stderr.write('Warning: After configure(), dev.status = false\n')
    dev.disarm()
    dev.arm()
    dev.ts_clear()
    dev.mem_toggle()  # flush the device memory to not to read a large chunk of old data


    # Open files
    files_ = [io.FileIO( name, 'w') for name in outfiles] 

    # Perform readout
    chunksize = 1024*1024  # how many bytes to request at once
    opts = {'chunk_size': chunksize/4 }
    
    destinations = list(zip( get_iterable(channels), get_iterable(files_) ))  # Python3 has changed zip behavior, need to wrap in list()
    readout_loop(dev, destinations, opts, quiet=False, print_stats=True)



def genFileNames(outpath, channels):
    '''Configure file output
    channels= channels to read, from 0 to 15 (all by default). 
         Use shell expressions to specify a range (like {0..7} {12..15})
    outpath= a path for output
    '''
    if outpath[-1] == '/':
        output = outpath + OUTHEAD
    else:
        output = outpath + '/' + OUTHEAD

    for x in channels:
        if not 0 <= x <= 15:
            sys.stderr.write("%d is not a valid channel number!\n" %x)
            sys.exit()
    chans = sorted(set(channels)) #deduplicated

    # --output
    makedirs(output)
    outfiles = [output + "%02d"%chan + OUTEXT for chan in chans]
    
    # check no overwrite
    for outfile in outfiles:
        if os.path.exists(outfile) and os.path.getsize(outfile) != 0:
            raise FileExistsError(f"File {outfile} exists and not empty!")
    
    return channels, outfiles




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', type = str, default = IP_ADDRESS, help='UDP port number')
    parser.add_argument('--port', type = int, default = 1234, help='UDP port number')
    parser.add_argument('--maxRetries', type = int, default = 10, help='Max retries to connect with sis3316 before giving up')
    args = parser.parse_args()

    print(f'Starting {SERVER_ID} server')
    context = zmq.Context.instance()
    worker_in = context.socket(zmq.DEALER)
    worker_in.setsockopt(zmq.IDENTITY, SERVER_ID)
    worker_in.connect(f"tcp://localhost:{TCP_SOCKET}")
   

    worker_out = context.socket(zmq.PUSH)
    worker_out.setsockopt(zmq.LINGER,0)  # Don't linger on send()
    worker_out.connect(f"tcp://localhost:{PUSH_SOCKET}")
    
    print('Connecting to sis3316...')
    dev = sis3316.Sis3316_udp(args.host, args.port)
    for i in range(args.maxRetries):
        if i == args.maxRetries -1:
            print('Max retries reached')
            sys.exit()
        try:
            dev.open()
        except Exception as e:
            # print(e)
            print(f'Reponse timeout. Retried {i} times')
            print('Please check that the sis3316 is turned on...\n')
            worker_out.send(b"sis3316 is offline", zmq.NOBLOCK)
            time.sleep(3)
        else:
            if i > 0:
                print('WARNING: You may need to reload your config file in the GUI!!')
            break
   
    print('connected!')
    print(f'module id: {dev.id}')
    print(f'serial: {dev.serno}')
    print(f'temp: {dev.temp} \u2103')
    worker_out.send(b"sis3316 is online")

    
    while True:
        print('\nWaiting for commands')

        msg = worker_in.recv_multipart()
        print(f'Received: {msg}')
        if msg[0] == b'CONFIG' and len(msg) == 2:
            # Expect ['CONFIG', config_filename]
            configFile = msg[1].decode('utf_8')
            print(f'Loading config file {configFile}...', end='')
            try:
                with open(configFile, 'r') as json_file:
                    conf_load(dev, json.load(json_file))
                print('Done')
                worker_out.send(b'Config loaded')
            except Exception as e:
                print(e)
                continue
        elif msg[0] == b'SHUTDOWN':
            dev.close()
            worker_out.send(b"sis3316 server closed")
            print('Closing server')
            sys.exit()
        elif msg[0] == b'PING':
            print('sent PONG')
            worker_out.send(b"PONG")
        elif msg[0] == b'START' and len(msg) == 3:
            # Expect [b'START', b'outputFolder', b'[0,1,...]']
            try:
                outpath = msg[1].decode('utf_8')
                channels = eval( msg[2] )
                    
            except Exception as e:
                print(e)
                worker_out.send(b"Invalid command START format")
                print('Invalid command START format')
                continue
            
            try:
                channels, outfiles = genFileNames(outpath, channels)
            except Exception as e:
                print(e)
                worker_out.send(b"File exists error")
                continue

            
            process = Process( target = readout_process, 
                                args = (dev, channels, outfiles,))
            worker_out.send(b"sis3316 started")
            os.system('clear')
            process.start()
            
            while process.is_alive():
                if worker_in.recv() == b'STOP':
                    process.terminate()
                    os.system('clear')
                    worker_out.send(b"sis3316 stopped")
                else:
                    worker_out.send(b"Invalid command: send STOP first")

            print('Data collection stopped')
            print(f'module id: {dev.id}')
            print(f'serial: {dev.serno}')
            print(f'temp: {dev.temp} \u2103')

        elif msg[0] == b'STOP':
            print("Error: Data collection not started yet")
            worker_out.send(b"Cannot stop sis3316 when it hasn't started yet")
        
        else:
            worker_out.send(b"Invalid command")
            print('Invalid command received')
                
        
    return

if __name__ == "__main__":
    main()
