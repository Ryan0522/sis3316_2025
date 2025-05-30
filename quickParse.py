#!/usr/bin/env python
'''
Basic parsing and plotting
'''
import io
import tools.parse as parse
import matplotlib.pyplot as plt
import argparse
import numpy as np

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-f','--file', type=str, default='data/ch00.dat', help='default=data/ch00.dat')
    parser.add_argument('-v', '--verbose', action='store_true', help='Prints out many binary file components')
    parser.add_argument('-es', '--eventSpacing', action='store_true', help='Plot histogram of event spacing')
    parser.add_argument('-N', '--N', type=int, default = 0, help='Plots first [N] events in the data file')
    parser.add_argument('-adc', '--adc', action='store_true', help='ADC histogram')
    args = parser.parse_args()


    infile = io.open(args.file, 'rb')
    p = parse.Parse(infile)
    event_raw = []
    event_maw = []
    e_max = []
    timestamp = []
    true_time = []
    peak = []
    maw_max = []
    totalEvents = 0
    HARDCODED_STOP = 1000 # Prevents over plotting of raw adc scope signals
    
    for eventNum, event in enumerate(p):
        if args.N and eventNum >= args.N:
            break
        timestamp.append(event.ts)
        true_time.append( event.ts/(250_000_000) )
        totalEvents = eventNum
        if hasattr(event,'e_max'):
            e_max.append(event.e_max)
        if hasattr(event,'peak'):
            peak.append(event.peak)
        if hasattr(event,'maw_max'):
            maw_max.append(event.maw_max)
        if args.verbose and eventNum<HARDCODED_STOP:
            if hasattr(event,'fmt'):
                print('format', bin(event.fmt))
            if hasattr(event,'peak'):
                print('peak ',event.peak)
            if hasattr(event,'e_max'):
                print('e_max ',event.e_max)
            if hasattr(event, 'acc7'):
                print('acc7 ', event.acc7)
            if hasattr(event, 'acc8'):
                print('acc8 ', event.acc8)
            if hasattr(event,'maw_max'):
                print('maw_max ',event.maw_max)
        if eventNum<HARDCODED_STOP and hasattr(event,'raw'):
            event_raw.append( event.raw )
        if eventNum<HARDCODED_STOP and hasattr(event,'maw'):
            event_maw.append( event.maw )
    
    print('Total events: ', totalEvents+1)

    plt.figure()
    plt.title( 'Time hist' )
    timeHist, bin_edges = np.histogram( true_time, 
                                   range=[ int(true_time[0]), int(np.ceil(true_time[-1])) ],
                                   bins = int(np.ceil(true_time[-1]  ) ) )
    plt.step( (bin_edges[1:] + bin_edges[:-1])/2 , timeHist )
    
    if event_raw: 
        plt.figure()
        plt.title('raw')
        plt.xlabel('Clock ticks')
        for i, raw in enumerate(event_raw):
            plt.plot(raw, color=f'C{i%10}')
    
    if event_maw:
        plt.figure()
        plt.title('maw')
        plt.xlabel('Clock ticks')
        for i, maw in enumerate(event_maw):
            plt.plot(maw, color=f'C{i%10}')
        plt.axhline(400+0x800_0000, color='black')
 
    if args.eventSpacing:
        plt.figure()
        plt.title('Event spacing')
        plt.xlabel('timestamp2 - timestamp1 [clock ticks]')
        plt.ylabel('Num events')
        spacing = np.subtract(timestamp[1:], timestamp[:-1])
        eventSpacingHist, bin_edges = np.histogram(spacing, range=[ 0, 100000], 
                                                    bins=10000)
        
        # print( 'number of events where spacing is between [1000,2000] clock ticks')
        # print( ((1000 < spacing) & (spacing < 2000)).sum() )
        plt.plot( (bin_edges[1:] + bin_edges[:-1])/2 , eventSpacingHist )
        #plt.axvline(1000, label='Trigger window length (1000)', color='gray')
        # plt.xlim(0, np.amax(spacing))
        # plt.ylim(0)
        #plt.legend()

        print('Average event spacing ', np.mean(spacing))


    if maw_max:
        plt.figure()
        plt.title('MAW max')
        plt.xlabel('Maw max')
        plt.ylabel('Num events')
        plt.hist(maw_max, range=[ np.amin(maw_max), np.amax(maw_max)], bins=int(np.amax(maw_max)-np.amin(maw_max)) )
        plt.xlim(np.amin(maw_max), np.amax(maw_max))
    
    # plt.figure()
    # plt.ylabel('timestamp [seconds]')
    # plt.xlabel('Event')
    # plt.scatter(np.divide(timestamp,250_000_000))

    if peak and args.adc:
        plt.figure()
        plt.title('sis3316 peak max')
        plt.ylabel('Num events')
        # plt.hist(peak, range=[ np.amin(peak), int(np.ceil(np.amax(peak))) ],  bins=int(np.ceil(np.amax(peak))-np.amin(peak)) )
        plt.hist(peak, range=[ 0, 2**14 ],  bins=10000 )
        # plt.yscale('log')
        # plt.hist(peak, range=[ 8800, 9500],  bins=700 )
    
    if e_max:
        plt.figure()
        plt.title('sis3316 E_max')
        plt.ylabel('Num events')
        plt.hist(e_max, range=[ np.amin(e_max), np.amax(e_max)],  bins=int(np.amax(e_max)-np.amin(e_max)) )
        # plt.hist(e_max, range=[ np.amin(e_max), np.amax(e_max)],  bins=1000 )

    
    plt.show()
    return

if __name__ == "__main__":
    main()
