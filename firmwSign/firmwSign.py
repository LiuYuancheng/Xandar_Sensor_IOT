#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:       firmwareSign.py
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
import time
import timeout_decorator
import hashlib
from datetime import datetime
import chilkat

SERVER_CHOICE = {
    "LocalDefault [127.0.0.1]"    : ('127.0.0.1', 5005),
    "Server_1 [192.168.0.100]"  : ('192.168.0.100', 5005),
    "Server_2 [192.168.0.101]"  : ('192.168.0.101', 5005)
}
BUFFER_SIZE = 1024
SENSOR_ID = '100'
ENCODE_MODE = 'hex'
CER_PATH = "C:\\Project\\testProgram\\IOT\\IOT\\firmwSign\\receivered.cer"


class FirmwareSignTool(wx.Frame):

    def __init__(self, parent, id, title):
        """ Init the UI. 
        """
        wx.Frame.__init__(self, parent, id, title, size=(450, 200))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        # init parameter here: 
        self.tcpClient = None 

        # Create the RSA encrypter
        self.rsaEncryptor = chilkat.CkRsa()
        if not self.rsaEncryptor.UnlockComponent("Anything for 30-day trial"):
            print("RSA component unlock failed")
            sys.exit()
        self.rsaEncryptor.put_EncodingMode(ENCODE_MODE)


        self.firmwarePath = "C:\\Project\\testProgram\IOT\IOT\\firmwSign\\firmwareSample"

        # Init the UI here. 
        sizer = wx.BoxSizer(wx.VERTICAL)
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        sizer.AddSpacer(5)
        hbox_1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox_1.Add(wx.StaticText(self, label='Server Selection: '),
                   flag=flagsR, border=2)
        self.serverchoice = wx.Choice(
            self, -1, choices=list(SERVER_CHOICE.keys()), name='Server')
        self.serverchoice.SetSelection(0)
        hbox_1.Add(self.serverchoice, flag=flagsR, border=2)
        self.connectBt = wx.Button(self, label='Connect', size=(70, 24))
        self.connectBt.Bind(wx.EVT_BUTTON, self.connectToServer)
        hbox_1.Add(self.connectBt, flag=flagsR, border=2)
        sizer.Add(hbox_1, flag=flagsR, border=2)
        sizer.AddSpacer(5)
        self.lgLb = wx.StaticText(self, label='Login [unconnected]: ')
        sizer.Add(self.lgLb, flag=flagsR, border=2)
        sizer.AddSpacer(5)
        hbox_2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox_2.Add(wx.StaticText(self, label=' '), flag=flagsR, border=2)
        self.userLb = wx.StaticText(self, label='UserName:')
        hbox_2.Add(self.userLb, flag=flagsR, border=2)
        self.userFI = wx.TextCtrl(self, -1, "", size=(100, -1), style=wx.TE_PROCESS_ENTER)
        #self.userFI.SetEditable(False)
        self.userFI.SetBackgroundColour(wx.Colour(200, 200, 200))
        hbox_2.Add(self.userFI, flag=flagsR, border=2)
        self.pwdLb = wx.StaticText(self, label='PassWord:')
        hbox_2.Add(self.pwdLb, flag=flagsR, border=2)
        self.pwdFI = wx.TextCtrl(self, -1, "", size=(100, -1), style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
        #self.pwdFI.SetEditable(False)
        self.pwdFI.SetBackgroundColour(wx.Colour(200, 200, 200))
        hbox_2.Add(self.pwdFI, flag=flagsR, border=2)
        self.lgBt = wx.Button(self, label='LogIn', size=(70, 24))
        self.lgBt.Bind(wx.EVT_BUTTON, self.loginServ)
        hbox_2.Add(self.lgBt, flag=flagsR, border=2)
        sizer.Add(hbox_2, flag=flagsR, border=2)
        sizer.AddSpacer(10)
        # Set the firmware file path: 
        hbox_3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox_3.Add(wx.StaticText(self, label='FirmwarePath:'), flag=flagsR, border=2)
        self.fmpath = wx.TextCtrl(self, -1, self.firmwarePath, size=(300, -1), style=wx.TE_PROCESS_ENTER)
        self.fmpath.SetBackgroundColour(wx.Colour(200, 210, 200))
        hbox_3.Add(self.fmpath, flag=flagsR, border=2)
        self.changeBt = wx.Button(self, label='change', size=(70, 24))
        hbox_3.Add(self.changeBt, flag=flagsR, border=2)
        sizer.Add(hbox_3, flag=flagsR, border=2)
        sizer.AddSpacer(5)
        self.signBt = wx.Button(self, label='Sign firmware', size=(100, 24))
        self.signBt.Bind(wx.EVT_BUTTON, self.signFirmware)
        self.signBt.Enable(False)
        sizer.Add(self.signBt, flag=flagsR, border=2)
        self.SetSizer(sizer)
        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText('Please select the server you want to connect')
        # Hide the not active widgets. 
        self.userLb.Hide()
        self.userFI.Hide()
        self.pwdLb.Hide()
        self.pwdFI.Hide()
        self.lgBt.Hide()
        self.Show()

    def connectToServer(self, event):
        key = self.serverchoice.GetString(self.serverchoice.GetSelection())
        ip, port = SERVER_CHOICE[key]
        try: 
            self.tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcpClient.connect((ip, port))
            self.tcpClient.send(b'login')
            data = self.tcpClient.recv(BUFFER_SIZE)            
            if data == b'Done':
                self.lgLb.SetLabel('Login [ '+ key +' ]')
                self.userLb.Show()
                self.userFI.Show()
                self.pwdLb.Show()
                self.pwdFI.Show()
                self.lgBt.Show()
            else:
                print("Login fail")
        except:
            print("TCP connection fault")
            self.tcpClient = None

    def loginServ(self, event):
        if self.tcpClient is None: return 
        user = self.userFI.GetLineText(0)
        pwd = self.pwdFI.GetLineText(0)
        loginStr = ";".join(['L', user, pwd])
        self.tcpClient.send(loginStr.encode('utf-8'))
        replay = self.tcpClient.recv(BUFFER_SIZE)
        if replay == b'Done':
            self.signBt.Enable(True)
            self.fetchCert()
            self.statusbar.SetStatusText("Login suscessful")
        else:
            self.signBt.Enable(False)
            self.statusbar.SetStatusText("UserName or password invalid")

        #self.statusbar.SetStatusText("No response to the server, please reconnect.")

    def fetchCert(self):
        self.tcpClient.send(b'Fetch')
        f = open("firmwSign\\receivered.cer", "wb")
        # here we assument the file not more than 4K 
        data = self.tcpClient.recv(4096)
        f.write(data)
        f.close()
        print ("got the file")

    def getMD5Hash(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def LoadCert(self):
        if not os.path.exists(CER_PATH):
            print("The certificate file is not exist")
            return
        cert = chilkat.CkCert()
        success = cert.LoadFromFile(CER_PATH)
        if not success:
            print(cert.lastErrorText())
            return
        pubKey = cert.ExportPublicKey()
        #xml = chilkat.CkXml()
        #xml.LoadXml(pubKey.getXml())

        success = self.rsaEncryptor.ImportPublicKey(pubKey.getXml())

    def sendEncryptedStr(self, dataStr):

        usePrivateKey = False
        encryptedStr = self.rsaEncryptor.encryptStringENC(dataStr, usePrivateKey)
        return encryptedStr

    def signFirmware(self, event): 
        print("sign the firmware")
        self.LoadCert()
        idStr = '202'
        md5str = str(self.getMD5Hash(self.firmwarePath))
        print("firare hash:" + md5str)
        now = datetime.now()
        dataStr = now.strftime("%d/%m/%Y")
        typeStr = 'XKAK_PPL_COUNT'
        version = '1.01'
        mapStr = ';'.join([idStr, md5str, dataStr, typeStr, version ])
        print("This is map string data: " + mapStr)
        sendStr = self.sendEncryptedStr(mapStr)
        print(sendStr)
        if self.tcpClient: 
            self.tcpClient.sendall(sendStr.encode('utf-8'))


#-----------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        frame = FirmwareSignTool(None, -1, 'XAKA firmware sign tool')
        frame.Show(True)
        return True

app = MyApp(0)
app.MainLoop()
