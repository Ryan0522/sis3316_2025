#!/usr/bin/env python
'''
ZMQ Server for live plotter with pyqtgraph display
'''
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QObject, pyqtSlot, QUrl
import io, sys, os, zmq, time, argparse
from QTfiles.plotter import Ui_MainWindow
from QTfiles.axesDialog import Ui_Dialog
from multiprocessing import Process, Queue 
import numpy as np
import pyqtgraph as pg
import histObj as h

from zmqGlobals import *
from tools.parse import Parse
from ast import literal_eval

ADC_HIST_MIN = 0 
ADC_HIST_MAX = 2**14 # adc is 14 bit @ 250 Mhz
SAMPLING_RATE = 250_000_000 # [Mhz]

def zmqReceive(out_q):
    '''Listens to Dealer socket and puts messages into out_q'''
    #ZMQ communication setup
    print(f'{PLOTTER_ID} server online')
    context = zmq.Context.instance()
    worker = context.socket(zmq.DEALER)
    worker.setsockopt(zmq.IDENTITY, PLOTTER_ID)
    worker.connect(f"tcp://localhost:{TCP_SOCKET}")
    
    while True:
        msg = worker.recv_multipart()
        print(f'received {msg}')
        out_q.put(msg)

def fileParser(filename, nbins, timeHist, timeHist_bins, adcHist):
    '''Parses a file and makes histograms
    timeHist, timeHist_bins, adcHist are queues

    nbins only affects adcHist binning
    '''
    update_timeout = 0.8 # [sec] Roughly how often histograms get updated

    while not os.path.exists(filename):
        time.sleep(0.5)
    infile = io.open(filename,  'rb', buffering=0)
    print('file opened')
    
    p = Parse(infile)
    t = h.time_hist()
    adc = h.hist(min = ADC_HIST_MIN, max = ADC_HIST_MAX, nbins = nbins) # adc is 14 bit @ 250Mhz

    while True:
        tic = time.perf_counter()
        eventTime = []
        eventPeak = []
        while time.perf_counter() - tic < update_timeout:
            try:
                event = p.next()
                eventTime.append( event.ts/ SAMPLING_RATE)
                if hasattr(event, 'peak'):
                    eventPeak.append( event.peak )
                
            except StopIteration: # End of file
                time.sleep(0.5)
                break

        # update histograms after either timeout or EOF
        if eventTime:
            t.fill( eventTime )
            try:
                timeHist.put_nowait( t.hist )
                timeHist_bins.put_nowait( t.get_binEdges() )
            except Exception as e:
                pass
        if eventPeak:
            adc.fill( eventPeak )
            try:
                adcHist.put_nowait(adc.hist)
            except Exception:
                pass


class MainWindowUIClass( QtWidgets.QMainWindow, Ui_MainWindow ):
    updateRate = 0.5 # [s]

    def __init__( self, args):
        '''Initialize the super class
        '''
        super().__init__()
        self.infiles = args.infiles
        self.nbins = args.nbins 
        self.stopPlotting = False # flag for stopping liveplots
        self.restartPlotting = False # flag for restarting liveplots
        self.setupUi(self)
        
        
    def setupUi( self, MW ):
        '''setup user interface
        '''
        super().setupUi( MW )
       
        # Set up zmq server to listen to commands
        self.queue = Queue() # zmq server message queue
        self.zmqProcess = Process(target=zmqReceive, args=(self.queue,))
        self.zmqProcess.start()
        time.sleep(0.1)

        # Setup file parsing
        while not self.infiles:
            self.listen(timeout = 0.1)
        self.setupParsers() 

        # Initialize pyqtgraph widget
        self.setupPlots()
        
        # List file names in the combo box (triggers slotComboBox())
        self.showFile = None
        self.updateComboBox()

        # Start plotting
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect( self.updater )
        self.timer.start( int(self.updateRate * 1000) ) # Timer needs update rate in ms

    def setupPlots( self ):
        '''pyqtgraph widget setup'''
        self.adcPlot = self.customGraphWidget.addPlot(title='ADC spectrum',
                                                labels={'left':'Num events', 
                                                        'bottom':'Peak max [14 bit]'})
        self.adcPlot.setMenuEnabled(False)
        self.adcCurve = self.adcPlot.plot( fillLevel=0, brush=(255,255,255,150) ) # brush=(r, g, b, a)
        
        self.timePlot = self.customGraphWidget.addPlot(title='Events',
                                                labels={'bottom':'time [s]'})
        self.timePlot.setMenuEnabled(False)
        self.timeCurve = self.timePlot.plot( fillLevel=0, brush=(255,255,255,150) )

        # compute adc histogram bin edges
        self.adcHist_bins = np.histogram_bin_edges([], bins=self.nbins, range=(ADC_HIST_MIN, ADC_HIST_MAX))

    def setupParsers( self ):
        '''Listen for infiles from zmq port, initialize file parsers'''
        print(f'Launching parsers')
        self.stopPlotting = False

        self.parser = {}
        self.timeHist = {}
        self.timeHist_bins = {}
        self.adcHist = {}
        for infile in self.infiles:
            try:
                self.startParsing( infile )
            except Exception as e:
                self.infiles.remove( infile )
                print(e)

    def startParsing( self, infile ):
        '''Launches thread to parse infile'''

        self.timeHist[infile] = Queue(maxsize=1)
        self.timeHist_bins[infile] = Queue(maxsize=1)
        self.adcHist[infile] = Queue(maxsize=1)
        self.parser[infile] = Process( target=fileParser, 
                                        args=(infile,
                                              self.nbins,
                                              self.timeHist[infile],
                                              self.timeHist_bins[infile],
                                              self.adcHist[infile],
                                              ))
        self.parser[infile].start()
        time.sleep(0.1) # wait for thread to stabilize

    def stopParsing( self, infile ):
        '''Stops parsing infile'''
        if (infile in self.parser) and self.parser[infile].is_alive():
            self.parser[infile].terminate()
            print(f'Parser {infile} stopped')
        else:
            print(f'Parser {infile} was not running, cannot terminate')

    def stopParsingAll( self ):
        '''Terminates all parsing processes'''
        print('Stopping all file parsing')
        for key, process in self.parser.items():
            process.terminate()
        self.parser = {}
        print('Done')
                                            

    def updateComboBox( self ):
        '''Updates combo box to list self.infiles
        '''
        self.comboBox.clear()
        if not self.infiles:
            self.comboBox.setEnabled(False)
        else:
            self.comboBox.setEnabled(True)
        self.comboBox.addItems(self.infiles)

    def updater( self ):
        '''Updates plots. Called every timer loop'''
        # Check to see if stop plotting command was issued
        self.listen( block = False )

        if not self.infiles:
            return
        elif self.restartPlotting:
            self.restartPlotting = False
            self.setupParsers() 
            self.updateComboBox()
            return
        elif self.stopPlotting:
            self.stopParsingAll()
            self.infiles=[]
            self.showFile=None
            self.stopPlotting = False
            self.restartPlotting = True # need to restart parsers
            return
        
        # update plots if data available
        try:
            self.timeCurve.setData( self.timeHist_bins[self.showFile].get_nowait(), 
                                    self.timeHist[self.showFile].get_nowait(), 
                                    stepMode='center')
        except Exception as e:
            pass

        try:
            self.adcCurve.setData(  self.adcHist_bins,
                                    self.adcHist[self.showFile].get_nowait(),
                                    stepMode='center')
        except Exception as e:
            pass

    def listen( self , block = True, timeout =None):
        '''Checks message queue and parses arguments
        If block = True, waits until queue has something in it
        '''
        try:
            msg = self.queue.get(block = block, timeout = timeout)
        except Exception as e:
            return
        
        if msg[0] == b'FILES' and len(msg) > 1:
            # Expects [b'FILES', b'filename0', b'filename1'...]
            names = []
            for bitstring in msg[1:]:
                names.append( bitstring.decode('utf_8') )
            self.infiles = names

        elif msg[0] == b'DONE':
            self.stopPlotting = True

        else:
            print('Invalid message received')

    ###############################
    ### ACTION SLOTS AND EVENTS ###
    ###############################
    
    @QtCore.pyqtSlot()
    def slotAddChannel(self):
        '''Menu bar add channel button
        '''
        folderLaunch = ""
        options = QtWidgets.QFileDialog.DontUseNativeDialog
        fileFormats = "data(*.dat)"
        filename, ext = QtWidgets.QFileDialog.getOpenFileName(None,
                        "Load sis3316 output file", 
                        folderLaunch,
                        fileFormats,
                        options=options)
        if not filename or (filename in self.infiles):
            return

        self.infiles.append(filename)
        try:
            self.startParsing(filename)
        except Exception as e:
            self.infiles.remove(filename)
            print(e)

        self.updateComboBox()

    @QtCore.pyqtSlot()
    def slotDeleteChannel(self):
        '''Menu bar add channel button
        '''
        removeFile, ok = QtWidgets.QInputDialog.getItem(self, 
                                                    'Remove channel',
                                                    'channel',
                                                    self.infiles,
                                                    editable=False)

        if not ok: # if user hits cancel button
            return

        self.stopParsing( removeFile )
        self.infiles.remove( removeFile )
        self.updateComboBox()

    @QtCore.pyqtSlot()
    def slotAxes(self):
        '''Menu bar Axes -> Settings
        Edits all axes settings
        '''
        settings, ok = axesDialog.getAxesSettings()
        if not ok:
            return

        if settings['hist'] == 'ADC':
            plot = self.adcPlot
        elif settings['hist'] == 'Time':
            plot = self.timePlot
        else:
            print('Invalid histogram plot choice')
            return

        if settings['yScale'] == 'Log':
            plot.setLogMode(y = True)
        else:
            plot.setLogMode(y = False)

        if settings['auto']:
            plot.autoRange()
            plot.enableAutoRange()
        else:
            if None not in [settings['xmin'], settings['xmax']]:
                plot.setRange( xRange=(settings['xmin'], settings['xmax'] ) )
            if None not in [settings['ymin'], settings['ymax']]:
                plot.setRange( yRange=(settings['ymin'], settings['ymax'] ) )
            
    @QtCore.pyqtSlot()
    def slotComboBox(self):
        '''Triggered whenever combo box text is changed
        Note that this is triggered by updateComboBox
        '''
        self.showFile = self.comboBox.currentText()

    def closeEvent(self, event):
        '''On closing the GUI window'''
        self.stopParsingAll()
        self.zmqProcess.terminate()

class axesDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__( self ):
        super().__init__()
        self.setupUi(self)

    def parseFields( self ):
        settings = {}
        settings['hist'] = self.comboBox_hist.currentText()
        settings['yScale'] = self.comboBox_yscale.currentText()
        settings['auto'] = self.checkBox_auto.isChecked()
        
        settings['xmin'] = self.toFloat( self.lineEdit_xmin.text() )
        settings['xmax'] = self.toFloat( self.lineEdit_xmax.text() )
        settings['ymin'] = self.toFloat( self.lineEdit_ymin.text() )  
        settings['ymax'] = self.toFloat( self.lineEdit_ymax.text() )
        
        return settings 

    def toFloat( self, string, default = None):
        try:
            out = eval(string)
        except Exception as e:
            out = default
        return out

    @staticmethod
    def getAxesSettings():
        dialog = axesDialog()
        result = dialog.exec_()
        settings = dialog.parseFields()

        return (settings, result == QtGui.QDialog.Accepted )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--infiles', type = str, nargs='+', help='filename(s) for live plotting. Not specifying launches a zmq server that listens to the GUI')
    parser.add_argument('-nbins', '--nbins', type = int, help='Number of bins in ADC histogram', default = 2**14)
    parsed_args, unparsed_args = parser.parse_known_args()
   
    app = QtWidgets.QApplication(sys.argv[:1] + unparsed_args)
    ui = MainWindowUIClass(parsed_args)
    ui.show()
    sys.exit(app.exec_())
    

if __name__ == "__main__":
    main()
