#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        XAKAsensor reader.py
#
# Purpose:     This function is used to read the data from XAKA people counting
#              sensor and show the data in the UI list.
#              - register the sensor to the server.
#
# Author:      Yuancheng Liu
#
# Created:     2019/03/27
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------

import os, platform
import io
import wx # use wx to build the UI.
import time
import serial, string
from struct import *
import threading
from functools import partial
import firmwTLSclient as SSLC
import firmwMsgMgr

# TCP connection: 
SERVER_CHOICE = {
    "LocalDefault [127.0.0.1]"  : ('127.0.0.1', 5006),
    "Server_1 [192.168.0.100]"  : ('192.168.0.100', 5006),
    "Server_2 [192.168.0.101]"  : ('192.168.0.101', 5006)
}

BUFFER_SIZE = 1024  # Normally 1024, but we want fast response
# People counting sensor message labels
LABEL_LIST = [
    'Seonsor ID: ',
    'Parameter Count:',
    'Presence Info:',
    '00: Sequence',
    '01: Idx People count',
    '02: Reserved',
    '03: Reserved',
    '04: Human Presence',
    '05: Program Version',
    '06: ShortTerm avg',
    '07: LongTerm avg',
    '08: EnvMapping rm T',
    '09: Radar Map rm T',
    '10: Idx for radar mapping',
    '11: Num of ppl for radar map',
    '12: Device ID',
    '13: Start Rng',
    '14: End Rng',
    '15: Reserved',
    '16: LED on/off',
    '17: Trans period',
    '18: Calib factor',
    '19: Tiled Angle',
    '20: Radar Height',
    '21: Avg size',
    '22: Presence on/off',
    '23: Reserved',
    '24: Final ppl num',
    '25: Radar MP val',
    '26: Env MP val',
    '27: serial num_1',
    '28: serial num_2',
    '29: serial dist1',
    '30: serial dist2',
    '31: Reserved',
    '32: Reserved',
    '33: Reserved'
]

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class SensorReaderFrame(wx.Frame):
    """ XAKA people counting sensor reader with sensor registration function. """
    def __init__(self, parent, id, title):
        """ Init the UI and parameters """
        wx.Frame.__init__(self, parent, id, title, size=(400, 750))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        # Init parameters.
        self.senId = self.version = self.sensorType = ''
        self.activeFlag = False  # whether we active the sensor data reading.
        self.dataList = []      # List to store the sensor data.
        self.valueDispList = []
        # Init the UI.
        self.bgPanel = wx.Panel(self)
        self.bgPanel.SetBackgroundColour(wx.Colour(200, 210, 200))
        sizer = self.buildUISizer(self.bgPanel)
        self.bgPanel.SetSizer(sizer)
        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText('Regist the connected sensor first.')
        # Init the SSL client to TLS connection.
        self.sslClient = SSLC.TLS_sslClient(self)  # changed to ssl client.
        # Init the message manager.
        self.msgMgr = firmwMsgMgr.msgMgr(self)  # create the message manager.
        # Init the serial reader
        #self.ser = serial.Serial('/dev/ttyUSB0', 115200, 8, 'N', 1, timeout=1)
        self.ser = serial.Serial('COM3', 115200, 8, 'N', 1, timeout=1) if platform.system() == 'Windows' \
            else serial.Serial('/dev/ttyUSB0', 115200, 8, 'N', 1, timeout=1)
        # Init the recall future.
        # when did we last call periodic?             # track periodic timing
        self.lastPeriodicTime = time.time()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.periodic)
        self.timer.Start(500)  # every 500 ms
        # Add Close event here.
        self.Bind(wx.EVT_CLOSE, self.OnClose)

#-----------------------------------------------------------------------------
    def buildUISizer(self, bgPanel):
        """ build the UI sizer for the background panel."""
        sizer = wx.GridSizer(len(LABEL_LIST)+2, 2, 4, 4)
        # Add the title line.
        sizer.Add(wx.Button(bgPanel, label='ParameterName ',
                            size=(195, 18), style=wx.BU_LEFT, name='ParameterName'))
        sizer.Add(wx.Button(bgPanel, label='FeedbackValue ', size=(
            195, 18), style=wx.BU_LEFT, name='Value'))
        # Add the display area.
        for item in LABEL_LIST:
            sizer.Add(wx.StaticText(bgPanel, -1, item))
            datalabel = wx.StaticText(bgPanel, -1, '--')
            self.valueDispList.append(datalabel)
            sizer.Add(datalabel)
        # Add the server selection and regist button.
        self.serverchoice = wx.Choice(
            bgPanel, -1, size=(190, 23), choices=list(SERVER_CHOICE.keys()), name='Server')
        self.serverchoice.SetSelection(0)
        sizer.Add(self.serverchoice)
        self.regBt = wx.Button(bgPanel, label='Sensor registration.', size=(190, 23))
        self.regBt.Bind(wx.EVT_BUTTON, self.logtoServer)
        sizer.Add(self.regBt)
        return sizer

#-----------------------------------------------------------------------------
    def logtoServer(self, event):
        """ Login to the server and register the sensor."""
        try:
            # Connect to the selected server. 
            ServerName = self.serverchoice.GetString(
            self.serverchoice.GetSelection())
            ip, port = SERVER_CHOICE[ServerName]
            self.sslClient.connect((ip, port))
            # send connect request cmd.
            self.sslClient.send(self.msgMgr.dumpMsg(action='CR'))
            dataDict = self.msgMgr.loadMsg(self.sslClient.recv(BUFFER_SIZE))
            if dataDict['act'] == 'HB' and dataDict['lAct'] == 'CR' and dataDict['state']:
                print("SConnetion: Connect to the server succesfully.")
            else:
                print("SConnetion: Connection request denied by server.")
                return
            print("SConnetion: start register to server")
            # Register the sensor.
            # Temporary hard code the sigature for test.
            signature = '68660887dd982d9f859943deee6b55859a52731cfa9b9d64d2c304007d1c785467dcb9b1b14c06906ff122fd986b6afd78ea0dd294301511061ac758108d4dd6ee256abf4a204e0be6037eea812aebfc00ffa22932e0dea040661137afa1f6072e74be5e0b4ddca9b689c71bf54014db69c80643f3e690c0b9dbf60c1eb782c5e9bf1ef981f1e30e37310e769687682fe07226a4e0ec6ad7f4d3e1d6ac7b808ed6aa9340dd1f8ab5a6fe6e1d025109bcfd653f7471e99782c4a0b06aa260df95dcd2f14de4a1b2ba6c73181e703365975c6a71affe16c309cb3152a15b8e09a6d82298b76ff4398263c6c2b9c01a4bb3a5d5addfe172be8fd88230511b600414'
            data = (self.senId, self.sensorType, self.version, signature)
            self.sslClient.send(self.msgMgr.dumpMsg(action='RG', dataArgs=data))
            dataDict = self.msgMgr.loadMsg(self.sslClient.recv(BUFFER_SIZE))
            if dataDict['act'] == 'HB' and dataDict['lAct'] == 'RG' and dataDict['state']:
                #print("FirmwSign: The sensor is registered successfully.")
                self.statusbar.SetStatusText("Sensor registration done.")
                self.activeFlag = True
            # Logout after resigtered.
            datab = self.msgMgr.dumpMsg(action='LO')
            self.sslClient.send(datab)
            self.sslClient.close()
        except:
            print("Connect to server fail.")

#-----------------------------------------------------------------------------
    def periodic(self,event):
        """ read the data one time and find the correct string can be used. """
        output = self.ser.read(500)  # read 500 bytes and parse the data.
        bset = output.split(b'XAKA')  # begine byte of the bytes set.
        for item in bset:
            # 4Bytes*37 paramters make sure the not data missing.
            if len(item) == 148:
                self.dataList = []
                for idx, data in enumerate(iter(partial(io.BytesIO(item).read, 4), b'')):
                    val = unpack('i', data) if idx == 0 or idx == 1 else unpack(
                        '<f', data)  # get the ID and parameter number
                    self.dataList.append(val[0])
        self.senId, self.version = self.dataList[0], self.dataList[8]
        self.sensorType = 'XKAK_PPL_COUNT'
        # Update the UI if the sensor registed successfully.
        if not self.activeFlag: return
        for i in range(len(self.valueDispList)): 
            self.valueDispList[i].SetLabel(str(self.dataList[i]))
 
#-----------------------------------------------------------------------------
    def OnClose(self, event):
        self.ser.close()
        self.Destroy()

#-----------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        frame = SensorReaderFrame(None, -1, 'XAKA People Counting Sensor')
        frame.Show(True)
        return True

app = MyApp(0)
app.MainLoop()
