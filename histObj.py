import numpy as np
 
try:
    FAST_HIST_ENABLED = True
    from fast_histogram import histogram1d
except ImportError as e:
    print('Warning: No fast_histogram package found, using numpy to histogram')
    print('try: pip install fast_histogram --user')
    FAST_HIST_ENABLED = False
FAST_HIST_ENABLED = False

class time_hist:
    '''Implements a time series histogram with integer bins [seconds]
    that dynamically adds more time bins as you fill it'''

    def __init__(self, preallocate = 100):
        self.preallocate = preallocate              # Number of empty bins to add at a time
        self.hist = np.zeros(preallocate)
        self.min = None                             # Lowest time bin value
        self.max = None                             # Highest time bin value

    def fill(self, data):
        '''Fills data into histogram
        Assumes data is a list in ascending time order
        '''
        if not isinstance( data, list):
            raise TypeError('data must be a list in ascending time order')

        if self.min == None:
            self.min = int( np.floor(data[0]) )
            self.max = self.min + self.preallocate

        toPad = [0,0]
        # resize histogram as needed
        if data[0] < self.min:
            toPad[0] = self.min - int( np.floor(data[0]) )
            self.min = int( np.floor(data[0]) )
        if data[-1] > self.max:
            toPad[1] = int( np.ceil(data[-1]) ) - self.max + self.preallocate
            self.max = int( np.ceil(data[-1]) ) + self.preallocate
        if np.any( toPad ):
            self.hist = np.pad(self.hist, tuple(toPad), 'constant', constant_values=0)

        # Fill histogram
        if FAST_HIST_ENABLED:
            self.hist += histogram1d(data, bins= self.max-self.min, range=(self.min, self.max))
        else:
            tmp, _ = np.histogram(data, bins= self.max-self.min, range=(self.min, self.max))
            self.hist += tmp

    def get_binEdges(self):
        return np.arange( self.min, self.max + 1)

    def get_nevents(self):
        return np.sum( self.hist )

class hist:
    '''Histogram object'''
    def __init__( self, min, max, nbins):
        self.hist = np.zeros( nbins )
        self.min = min
        self.max = max
        self.nbins = nbins
        self.binEdges = np.histogram_bin_edges([], bins=self.nbins, range=(self.min, self.max))

    def fill(self, data):
        '''Fills data into histogram'''
        if not isinstance( data, list):
            raise TypeError('data must be a list')
        
        # Fill histogram
        if FAST_HIST_ENABLED:
            self.hist += histogram1d(data, bins= self.nbins, range=(self.min, self.max))
        else:
            tmp, _ = np.histogram(data, bins= self.nbins, range=(self.min, self.max))
            self.hist += tmp

    def get_binEdges(self):
        return self.binEdges
    
    def get_nevents(self):
        return np.sum( self.hist )
