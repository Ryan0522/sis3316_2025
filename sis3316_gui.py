#!/usr/bin/env python

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, pyqtSlot, QUrl
import sys, os, zmq, time
from QTfiles.mainwindow import Ui_MainWindow
import json, re
import numpy as np
from datetime import datetime, date
from collections.abc import Iterable
from pathlib import Path

import socket, select, struct

from functools import reduce

from zmqGlobals import *
from readoutServer import genFileNames

def add_extension(filename, extension):
    '''Adds filename extension if user did not specify.
    filename and ext should be outputs from QFileDialog functions'''
    ext = re.search(r'\(\*(\.\w+)\)', extension)
    if ext == None:
        raise Exception(f'Incorrect input {extension}')
    else:
        ext = ext.group(1)

    if filename[-len(ext):].find(ext) != -1:
        # if extension is in the filename
        return filename
    else:
        return filename + ext

def get_list(x):
    if isinstance(x, list):
        return x
    else:
        return [x]

class MainWindowUIClass( QtWidgets.QMainWindow, Ui_MainWindow ):
    DEFAULT_CONFIG = 'defaults.in'

    def __init__( self ):
        '''Initialize the super class
        '''
        super().__init__()
        self.setupUi(self)
        
    def setupUi( self, MW ):
        '''setup user interface
        '''
        super().setupUi( MW )
        #ZMQ communication
        self.context = zmq.Context.instance()
        self.client = self.context.socket(zmq.ROUTER)
        self.client.bind(f"tcp://*:{TCP_SOCKET}")
        
        # Load initial settings
        self.stopButton.setEnabled(False) # Disable STOP button
        self.loadDefaults( self.DEFAULT_CONFIG, self.frame_channels )
        self.lineEdit_ip.setText( self.ip )
        self.lineEdit_config.setText( self.config )
        self.lineEdit_folder.setText( self.outputFolder )
        self.textBrowser_help.setSource( QUrl('README.md') ) # Load documentation into help tab
        self.printMsg('Initializing...')
        time.sleep(1)
        self.loadConfig()

    def sendCmd(self, msg):
        '''Sends command to sis3316 server'''
        toSend = [SERVER_ID]
        toSend.extend( get_list(msg) ) 
        self.client.send_multipart( toSend )

    def startLivePlotter(self, infiles):
        '''Send filenames to liveplotter'''
        toSend = [PLOTTER_ID, b'FILES']
        toSend.extend( f.encode('utf-8') for f in get_list(infiles) )
        self.client.send_multipart( toSend )

    def stopLivePlotter(self):
        self.client.send_multipart( [PLOTTER_ID, b'DONE'] )

    def errorWindow(self, msg, details = None):
        '''Throws an error window on the gui'''
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(msg)
        if details is not None:
            msgBox.setDetailedText(details)
        msgBox.exec_()
    
    def loadDefaults( self, filename, checkBoxFrame):
        '''Loads default settings from filename'''
        self.config = None
        self.ip = IP_ADDRESS
        self.outputFolder = None
        self.settings = None
        self.lastChannel = 0 # Used for saveChannelTab()
        
        try:
            with open(filename) as json_file:
                defaults = json.load(json_file)
            self.config = defaults['config']
            if defaults['outputFolder'][-1] != '/':
                self.outputFolder = defaults['outputFolder'] + '/'
            else:
                self.outputFolder = defaults['outputFolder'] 
            self.printMsg(f'Loaded GUI defaults from "{filename}"')
        
            # Set checkbox states for active channels
            for widget in checkBoxFrame.children():
                if isinstance(widget, QtWidgets.QCheckBox):
                    channelName = re.search(r'\d+$', widget.objectName())
                    if channelName is not None:
                        widget.setCheckState( defaults['channels'][0][channelName.group(0)] )
        except Exception as error:
            self.printMsg(f'Error loading gui defaults file "{filename}"')
            self.printMsg(error)



    def loadConfig( self ):
        '''Loads config file self.config into an internal dictionary self.settings'''
        
        self.printMsg( f"Loading config file: {self.config}" )
        self.destination = None
        try:
            with open(self.config) as json_file:
                self.settings = json.load(json_file)
            self.sendCmd( [b'CONFIG', self.config.encode()] )
        except Exception as error:
            self.printMsg(f'Unable to load {self.config}')
            self.printMsg(error)
            self.settings = None
            self.config = None


    def saveChannelTab( self, channel ):
        '''Saves channel tab settings to self.settings dictionary'''
        if os.path.exists(self.config)==False or self.settings==None:
            raise Exception("No config file currently loaded")
        
        threshold = int(self.lineEdit_threshold.text())
        group = channel // 4
        if threshold <= 0:
            threshold = self.settings['triggers'][f'{channel}'].get(f'threshold')
            raise Exception("Invalid threshold value")
        else:
            threshold = threshold + 0x800_0000
        self.settings['triggers'][f'{channel}']['threshold'] = threshold
        # print(f'threshold: {threshold - 0x800_0000}')

        if self.checkBox_adcRaw.checkState():
            raw_window = self.settings['groups'][f'{group}'].get('gate_window')
        else:
            raw_window = 0
        self.settings['groups'][f'{group}']['raw_window'] = raw_window
        # print(f'raw_window: {raw_window}')

        flags = self.settings['channels'][f'{channel}'].get('flags')
        if self.checkBox_invert.checkState():
            if not isinstance(flags, list):
                flags = ['invert']
            elif 'invert' not in flags:
                flags.append('invert')
            self.settings['channels'][f'{channel}']['flags'] = flags
        elif isinstance(flags, list) and ('invert' in flags):
            flags.remove('invert')
            self.settings['channels'][f'{channel}']['flags'] = flags
        # print(f'flags: {flags}')

        event_format_mask = self.settings['channels'][f'{channel}'].get('event_format_mask')
        if self.checkBox_peakMax.checkState():
            if event_format_mask == None:
                event_format_mask = 0b1
            else:
                event_format_mask = event_format_mask | 0b1
            self.settings['channels'][f'{channel}']['event_format_mask'] = event_format_mask
        elif (event_format_mask != None) and (event_format_mask & 0b1):
            event_format_mask = event_format_mask ^ 0b1
            self.settings['channels'][f'{channel}']['event_format_mask'] = event_format_mask
        # print(f'event_format: {event_format_mask}')

        if self.radio_gain5V.isChecked():
            gain = 0
        elif self.radio_gain2V.isChecked():
            gain = 1
        elif self.radio_gain19V.isChecked():
            gain = 2
        else:
            gain = None
            raise Exception("Invalid gain value")
        self.settings['channels'][f'{channel}']['gain'] = gain
        # print(f'gain: {gain}')


    def loadChannelTab( self, channel ):
        '''Display channel settings on the channel tab'''
        if os.path.exists(self.config)==False or self.settings==None:
            self.label_channel.setText(f"-- No config file loaded --")
            self.channelConfigButton.setEnabled(False)
            return
        
        self.label_channel.setText(f"-- Channel {channel} --")
        self.channelConfigButton.setEnabled(True)
        group = channel // 4
        self.label_raw.setText(f"Read raw waveform (ch {group*4} - {group*4 + 3})")
        
        gain = self.settings['channels'][f'{channel}'].get('gain')
        threshold = self.settings['triggers'][f'{channel}'].get('threshold')
        event_format_mask = self.settings['channels'][f'{channel}'].get('event_format_mask')
        raw_window = self.settings['groups'][f'{group}'].get('raw_window')
        flags = self.settings['channels'][f'{channel}'].get('flags')
        
        if threshold:
            self.lineEdit_threshold.setText( str(threshold - 0x800_0000) )
        else:
            self.lineEdit_threshold.setText( 'None' )
        # print(f'threshold: {threshold - 0x800_0000}')

        if raw_window:
            self.checkBox_adcRaw.setCheckState(True)
        else:
            self.checkBox_adcRaw.setCheckState(False)
        # print(f'raw_window: {raw_window}')
        
        if event_format_mask and (event_format_mask & 0b1):
            self.checkBox_peakMax.setCheckState(True)
        else:
            self.checkBox_peakMax.setCheckState(False)

        if 'invert' in flags:
            self.checkBox_invert.setCheckState(True)
        else:
            self.checkBox_invert.setCheckState(False)
        # print(f'flags: {flags}')

        if gain == 0:
            self.radio_gain5V.setChecked(True)
        elif gain == 1:
            self.radio_gain2V.setChecked(True)
        elif gain == 2:
            self.radio_gain19V.setChecked(True)
        # print(f'gain: {gain}')

        return

    def getActiveCheckboxes(self, checkBoxFrame):
        '''Loops over the layout Frame containing widgets, returns list of active checkboxes
        Requires the last characters of the check box name to be an integer
        '''
        activeChannels = []
        for widget in checkBoxFrame.children():
            if isinstance(widget, QtWidgets.QCheckBox) and widget.checkState():
                match = re.search(r'\d+$', widget.objectName())
                if match is not None:
                    activeChannels.append(int(match.group(0)))
        return np.sort(activeChannels).tolist()

    def printMsg( self, msg ):
        '''Print message in the text Browser in gui
        '''
        self.textBrowser.append(str(msg) )

    ####################
    ### ACTION SLOTS ###
    ####################
    @QtCore.pyqtSlot()
    def slotIpAddress(self):
        ''' Called when the user enters a string in the IP address line and
        presses the ENTER key.
        '''
        # self.ip =  self.lineEdit_ip.text()
        # self.printMsg( f"IP Address set: {self.ip}" )
        self.lineEdit_ip.setText(self.ip)


    @QtCore.pyqtSlot()
    def slotIpConnect(self):
        ''' Called when the user presses the Ip check connection button.
        '''
        # self.ip =  self.lineEdit_ip.text()
        # self.printMsg( f"IP Address set: {self.ip}" )
        self.printMsg( "Sent PING to sis3316 zmq server" )
        self.sendCmd( b"PING")

    @QtCore.pyqtSlot()
    def slotBrowseConfig(self):
        ''' Called when the user presses the Load Config button.
        '''
        folderLaunch = ""
        options = QtWidgets.QFileDialog.DontUseNativeDialog
        fileFormats = "JSON(*.json);;Text(*.txt)"
        filename, ext = QtWidgets.QFileDialog.getOpenFileName(None,
                        "Load sis3316 config file", 
                        folderLaunch,
                        fileFormats,
                        options=options)
        if not filename:
            return
        
        self.config = filename
        self.lineEdit_config.setText( self.config )
        self.loadConfig()
        

    @QtCore.pyqtSlot()
    def slotBrowseOutput(self):
        ''' Called when the user presses the Browse Output Folder button.
        '''
        folderLaunch = str(Path(self.outputFolder).parent)
        options = QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontUseNativeDialog
        dirpath = str(QtWidgets.QFileDialog.getExistingDirectory(None,"Select directory", folderLaunch, options))
        if not dirpath:
            return       

        self.outputFolder = dirpath
        self.lineEdit_folder.setText( self.outputFolder )
        self.printMsg( f"Output directory: {self.outputFolder}" )
    
    @QtCore.pyqtSlot()
    def slotConfig(self):
        ''' Called when the user enters a string in the Config file line and
        presses the ENTER key.
        '''
        self.config = self.lineEdit_config.text()
        self.loadConfig()
    
    @QtCore.pyqtSlot()
    def slotOutput(self):
        ''' Called when the user enters a string in the output folder line and
        presses the ENTER key.
        '''
        self.outputFolder = self.lineEdit_folder.text()
        self.printMsg( f"Output directory: {self.outputFolder}" )
    
    @QtCore.pyqtSlot()
    def slotStart(self):
        ''' Called when the user presses the Start button.
        '''
        activeChannels = self.getActiveCheckboxes(self.frame_channels)
        dateStr = ''.join([s.replace('-','') for s in date.today().isoformat()])
        runCounter = 1

        # don't override previous runs
        while os.path.isdir(self.outputFolder + f'{dateStr}_run{runCounter}'):
            runCounter += 1

        self.destination = self.outputFolder + f'{dateStr}_run{runCounter}'
         
        try:
            _, outfiles = genFileNames(self.destination, activeChannels)
        except Exception as error:
            self.printMsg( "File exists error. Start signal not sent" )
            self.errorWindow("Error: File already exists. Specify a new folder", 
                                details=str(error))
            return
            

        self.printMsg( f"Start data collection\n{datetime.now()}")
        self.printMsg( f"Writing to folder {self.destination}")
        self.printMsg( f"Active channels: {activeChannels}" )
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.ipConnectButton.setEnabled(False)
        cmd = [b'START', self.destination.encode(), str(activeChannels).encode()]
        # print(cmd)
        self.sendCmd(cmd)

        # log start time in attribute file
        with open(f'{self.destination}/{ATTR_FILE}', 'a') as attrFile:
            attrFile.write(f'start={datetime.now()}\n') 

        self.startLivePlotter( outfiles )

    @QtCore.pyqtSlot()
    def slotStop(self):
        ''' Called when the user presses the Stop button.
        '''
        self.printMsg( f"Stop data collection\n{datetime.now()}")
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.ipConnectButton.setEnabled(True)
        self.sendCmd(b'STOP')
        
        # log stop time in attribute file, dump config to file
        if self.destination:
            with open(f'{self.destination}/{ATTR_FILE}', 'a') as attrFile:
                attrFile.write(f'end={datetime.now()}\n') 
            with open(f'{self.destination}/config.json','w') as json_file:
                json.dump(self.settings, json_file, indent=2)

        self.stopLivePlotter()

    
    @QtCore.pyqtSlot()
    def slotChannelConfig(self):
        ''' Called when user presses the "Apply settings" button on the channel tab
        '''
        chanNum = self.comboBox_channel.currentIndex()
        try:
            self.saveChannelTab(chanNum)
        except Exception as error:
            self.errorWindow("Invalid channel settings", details=str(error))
            self.loadChannelTab(chanNum)
            return
        
        folderLaunch = ""
        options = QtWidgets.QFileDialog.DontUseNativeDialog
        fileFormats = "JSON(*.json);;Text(*.txt);;Input(*.in)"
        filename, ext = QtWidgets.QFileDialog.getSaveFileName(None,
                        "Save new config file", 
                        folderLaunch,
                        fileFormats,
                        options=options)
        if not filename:
            return
        # Add file extension if user did not specify
        filename = add_extension(filename, ext)
        self.config = filename

        # Save current channel settings
        with open(filename,'w') as json_file:
            json.dump(self.settings, json_file, indent=2)
        
        self.lineEdit_config.setText( self.config )
        self.printMsg("New config settings applied")
        self.loadConfig()

    
    @QtCore.pyqtSlot()
    def slotChannelChange(self):
        ''' Called when user changes the channel selector on the Channel tab
        '''
        chanNum = self.comboBox_channel.currentIndex()
        try:
            self.saveChannelTab(self.lastChannel)
        except Exception as error:
            self.errorWindow("Invalid channel settings", details=str(error))
        
        self.loadChannelTab(chanNum)
        self.lastChannel = chanNum

    @QtCore.pyqtSlot()
    def slotTabChanged(self):
        ''' Called when user changes the tab
        '''
        if self.tabWidget.currentWidget().objectName() == 'channelTab':
            chanNum = self.comboBox_channel.currentIndex()
            self.loadChannelTab(chanNum)

def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindowUIClass()
    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
