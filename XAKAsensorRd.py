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


# TCP connection: 
TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 20  # Normally 1024, but we want fast response
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
        sizer = wx.GridSizer(len(LABEL_LIST)+1, 2, 4, 4)
        sizer.Add(wx.Button(bgPanel, label='ParameterName ', size=(195, 18), style = wx.BU_LEFT, name='num'))
        sizer.Add(wx.Button(bgPanel, label='Value ', size=(195, 18), style = wx.BU_LEFT, name='num'))
        for i in range(len(LABEL_LIST)):
            sizer.Add(wx.StaticText(bgPanel, -1, LABEL_LIST[i]))
            datalabel = wx.StaticText(bgPanel, -1, str(self.dataList[i]))
            self.valueDispList.append(datalabel)
            sizer.Add(datalabel)
        bgPanel.SetSizer(sizer)
        # Init the TCP server thread
        self.thread1 = commThread(1, "Thread-1", 1)
        self.thread1.start()
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
                #for i in range(37):
                #    data = item[i*4:i*4+4]
                #    val = unpack('i', data) if i == 0 or i == 1 else unpack('<f',data) # get the ID and parameter number 
                #    self.dataList.append(val[0])
        # Update the UI. 
        for i in range(len(self.valueDispList)): 
            self.valueDispList[i].SetLabel(str(self.dataList[i]))
        # Send the message to TCP server. 
        msg = '-'.join((str(self.dataList[0]), format(self.dataList[4], '0.2f'), format(self.dataList[27], '0.2f'))) 
        self.thread1.updateMsg(str(msg).encode('utf-8'))

#-----------------------------------------------------------------------------
    def periodicOld(self, event):
        output = self.ser.read(4)
        if output == b'XAKA':
            print(self.dataList)
            self.dataList = []
            output = self.ser.read(4)
            print(output)
            devId = unpack('i', output)[0]
            if devId != 202: 
                print("Device ID invalid"+str(devId))
                return
            self.dataList.append(devId)

            output = self.ser.read(4)
            floatDataNum = unpack('i', output)[0]
            if floatDataNum != 35: 
                print("missing data ID invalid"+str(floatDataNum))
                return

            self.dataList.append(floatDataNum)
            print(floatDataNum)
            for i in range(floatDataNum):
                output = self.ser.read(4)
                data = unpack('<f',output)
                self.dataList.append(data[0])
            
            for i in range(len(self.valueDispList)): 
                self.valueDispList[i].SetLabel(str(self.dataList[i]))
        return
        header = b'\x44\x7C\x86\x77'
        end1= b'\x43\x7F\x41\x48'
        ledID = pack('<f', 16)
        #ledID = b'\x41\x80\x00\x00'
        #ledID = b'\x40\x00\x00\x00'
        ledon = pack('<f', self.ledtg)
        #ledon = b'\x40\xA9\x99\x9A'
        end2= b'\x43\x7F\x41\x48'
        msg = header+ledID+ledon+end1+end2
        msg = b'\xBF\x80\x00\x00'+'\n\r'
        print(str(msg))
        self.ser.write(msg)
        #self.ledtg = abs(1-self.ledtg)

#-----------------------------------------------------------------------------
    def OnClose(self, event):
        #self.ser.close()
        self.thread1.stop()
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
