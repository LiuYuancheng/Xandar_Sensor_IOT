#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        XAKAsensor reader.py
#
# Purpose:     This function is used to read the data from XAKA people counting
#              sensor and show the data in the UI list.
#
# Author:      Yuancheng Liu
#
# Created:     2019/03/27
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------

import wx # use wx to build the UI.
import os
import io
import time
import serial, string
from struct import *
import threading
import socket
from functools import partial
import firmwTLSclient as SSLC
import firmwMsgMgr

# TCP connection: 
TCP_IP = '127.0.0.1'
TCP_PORT = 5006
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
    '0: Sequence',
    '1: Idx People count',
    '2: Reserved',
    '3: Reserved',
    '4: Human Presence',
    '5: Program Version',
    '6: ShortTerm avg',
    '7: LongTerm avg',
    '8: EnvMapping rm T',
    '9: Radar Map rm T',
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
    '33: Reserved',
]

#-----------------------------------------------------------------------------
class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        """ Init the UI. 
        """
        wx.Frame.__init__(self, parent, id ,title, size=(400, 750))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        self.dataList = [0] *len(LABEL_LIST)
        self.valueDispList = []
        bgPanel = wx.Panel(self)
        bgPanel.SetBackgroundColour(wx.Colour(200, 210, 200))
        sizer = wx.GridSizer(len(LABEL_LIST)+2, 2, 4, 4)
        sizer.Add(wx.Button(bgPanel, label='ParameterName ', size=(195, 18), style = wx.BU_LEFT, name='num'))
        sizer.Add(wx.Button(bgPanel, label='Value ', size=(195, 18), style = wx.BU_LEFT, name='num'))
        for i in range(len(LABEL_LIST)):
            sizer.Add(wx.StaticText(bgPanel, -1, LABEL_LIST[i]))
            datalabel = wx.StaticText(bgPanel, -1, str(self.dataList[i]))
            self.valueDispList.append(datalabel)
            sizer.Add(datalabel)
        
        self.serverchoice = wx.Choice(
            bgPanel, -1, choices=list(SERVER_CHOICE.keys()), name='Server')
        self.serverchoice.SetSelection(0)
        sizer.Add(self.serverchoice)

        self.regBt = wx.Button(bgPanel, label='Sensor registration.')
        self.regBt.Bind(wx.EVT_BUTTON, self.logtoServer)
        sizer.Add(self.regBt)

        bgPanel.SetSizer(sizer)
        # Init the TCP server thread
        #self.thread1 = commThread(1, "Thread-1", 1)
        #self.thread1.start()
        
        # Init the SSL client to TLS connection.  
        self.sslClient = SSLC.TLS_sslClient(self) # changed to ssl client.
        self.periodicCount = 0
        self.msgMgr= firmwMsgMgr.msgMgr(self) # create the message manager.
        
        self.senId = ''
        self.version = ''
        self.sensorType = ''
        self.active = False

        # Init the serial reader
        #self.ser = serial.Serial('/dev/ttyUSB0', 115200, 8, 'N', 1, timeout=1)
        self.ser = serial.Serial('COM3', 115200, 8, 'N', 1, timeout=1)
        self.dataList = []
        self.floatDataNum = 0
        self.ledtg = 0
        # Init the recall future. 
        self.lastPeriodicTime = time.time()   # when did we last call periodic?             # track periodic timing
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.periodic)
        self.timer.Start(500)  # every 50 ms
        # Add Close event here. 
        self.Bind(wx.EVT_CLOSE, self.OnClose)

#-----------------------------------------------------------------------------
    def periodic(self,event):
        """ read the data one time and find the correct string can be used. 
        """
        output = self.ser.read(500)
        bset = output.split(b'XAKA')
        for item in bset: 
            if len(item) == 148:
                self.dataList = []
                for idx, data in enumerate(iter(partial(io.BytesIO(item).read, 4), b'')):
                    val = unpack('i', data) if idx == 0 or idx == 1 else unpack(
                        '<f', data)  # get the ID and parameter number
                    self.dataList.append(val[0])
        # Update the UI.
        self.senId = self.dataList[0]
        self.version = self.dataList[8]
        self.sensorType = 'XKAK_PPL_COUNT'
        if not self.active: return
        for i in range(len(self.valueDispList)): 
            self.valueDispList[i].SetLabel(str(self.dataList[i]))
 
#-----------------------------------------------------------------------------
    def logtoServer(self, event):
        """ Login to the server and register the sensor."""
        try:
            ServerName = self.serverchoice.GetString(
            self.serverchoice.GetSelection())
            ip, port = SERVER_CHOICE[ServerName]
            self.sslClient.connect((ip, port))
            # Connect to the server. 
            connectRequest = self.msgMgr.dumpMsg(action='CR')
            self.sslClient.send(connectRequest)
            response = self.sslClient.recv(BUFFER_SIZE)                
            dataDict = self.msgMgr.loadMsg(response)
            if dataDict['act'] == 'HB' and dataDict['lAct'] == 'CR':
                if dataDict['state']:
                    print("Connect to the server succesfully.")
                else:
                    return
            print("start register to server")
            # Register the sensor.
            # Temporary hard code the sigature for test.
            signature = '68660887dd982d9f859943deee6b55859a52731cfa9b9d64d2c304007d1c785467dcb9b1b14c06906ff122fd986b6afd78ea0dd294301511061ac758108d4dd6ee256abf4a204e0be6037eea812aebfc00ffa22932e0dea040661137afa1f6072e74be5e0b4ddca9b689c71bf54014db69c80643f3e690c0b9dbf60c1eb782c5e9bf1ef981f1e30e37310e769687682fe07226a4e0ec6ad7f4d3e1d6ac7b808ed6aa9340dd1f8ab5a6fe6e1d025109bcfd653f7471e99782c4a0b06aa260df95dcd2f14de4a1b2ba6c73181e703365975c6a71affe16c309cb3152a15b8e09a6d82298b76ff4398263c6c2b9c01a4bb3a5d5addfe172be8fd88230511b600414'
            data = (self.senId, self.sensorType, self.version, signature)
            datab = self.msgMgr.dumpMsg(action='RG', dataArgs = data)
            self.sslClient.send(datab)
            response = self.sslClient.recv(BUFFER_SIZE)
            dataDict = self.msgMgr.loadMsg(response)
            if dataDict['act'] == 'HB' and dataDict['lAct'] == 'RG' and dataDict['state']:
                print("FirmwSign: The sensor is registered successfully.")
                self.active = True
            # Logout after resigtered.
            datab = self.msgMgr.dumpMsg(action='LO')
            self.sslClient.send(datab)
        except:
            print("Connect to server fail.")

#-----------------------------------------------------------------------------
    def OnClose(self, event):
        #self.ser.close()
        #self.thread1.stop()
        self.Destroy()

#-----------------------------------------------------------------------------

class commThread(threading.Thread):
    """ Add the TCP thread here: 
    """ 
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.terminate = False
        self.conn = None
        self.msg = b"test message"
        print("--Init the comm thread")
        # Init the TCP server
        try:
            self.tcpSer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcpSer.bind((TCP_IP, TCP_PORT))
            self.tcpSer.listen(1)
        except:
            print("TCP socket init error")
            raise

#-----------------------------------------------------------------------------
    def run(self):
        while not self.terminate:
            # Add the reconnection handling 
            self.conn, addr = self.tcpSer.accept()
            print('Connection address:'+str(addr))
            while not self.terminate:
                data = self.conn.recv(BUFFER_SIZE)
                if not data: break # get the ending message. 
                print("received data:"+str(data))
                self.conn.send(self.msg)  # echo
        print("TCP server terminat.")

#-----------------------------------------------------------------------------
    def updateMsg(self, msg):
        """ update the sending message.
        """
        if isinstance(msg, str): msg = msg.encode('utf-8')
        self.msg = msg

#-----------------------------------------------------------------------------
    def stop(self):
        self.terminate = True
        if self.conn: self.conn.close()

#-----------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, -1, 'XAKA People Counting Sensor')
        frame.Show(True)
        return True

app = MyApp(0)
app.MainLoop()
