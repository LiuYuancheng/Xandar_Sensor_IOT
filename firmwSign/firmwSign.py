#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        firmwareSign.py
#
# Purpose:     This module is used to connect to the firmware sign server and:
#               - Login to authorize the user
#               - Download the sign sertificate and the swatt challenge string.
#               - Sign the file SWATT value and related informaiton and feed
#                 back the data to server to check.
# Author:      Yuancheng Liu
#
# Created:     2019/04/29
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------

import os
import wx # use wx to build the UI.
import sys
import time
import json
import socket
import hashlib
import platform
import chilkat # need to pip install this lib.
from functools import partial
from datetime import datetime
import IOT_Att as SWATT
import firmwMsgMgr
from OpenSSL import crypto

pyVersionStr = str(platform.python_version())
# TCP Server ip + port list:
SERVER_CHOICE = {
    "LocalDefault [127.0.0.1]"  : ('127.0.0.1', 5005),
    "Server_1 [192.168.0.100]"  : ('192.168.0.100', 5005),
    "Server_2 [192.168.0.101]"  : ('192.168.0.101', 5005)
}
# 
BUFFER_SIZE = 1024  # TCP buffer size.
SENSOR_ID   = 100 
SIGNER_ID   = 200
ENCODE_MODE = 'base64'
RSA_UNLOCK = "Anything for 30-day trial"
SWATT_ITER = 300 # Swatt calculation iteration count.
RAN_LEN = 4 # random byte length

dirpath = os.getcwd()
print("Current working directory is : %s" %dirpath)

CER_PATH = "".join([dirpath, "\\firmwSign\\receivered.cer"])
SCER_PATH = "".join([dirpath, "\\firmwSign\\receivered.pem"]) # Certificate path userd to sign the data. 
DEFUALT_FW = "".join([dirpath, "\\firmwSign\\firmwareSample"])

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class FirmwareSignTool(wx.Frame):

    def __init__(self, parent, id, title):
        """ Init the UI. """
        wx.Frame.__init__(self, parent, id, title, size=(450, 200))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        # init parameter here:
        self.tcpClient = None
        self.msgMgr= firmwMsgMgr.msgMgr(self) # create the message manager.
        self.saveCert = True # flag to specify wehter we save certificate in local.
        self.bIOhandler = None
        self.ownRandom = None
        self.serRandom = None
        self.priv_key = None

        self.swattHd = SWATT.swattCal()
        self.swattChaStr = 'Default Challenge String'
        # Create the RSA encrypter
        self.rsaEncryptor = chilkat.CkRsa()
        if not self.rsaEncryptor.UnlockComponent(RSA_UNLOCK):
            print("RSA component unlock failed")
            sys.exit()
        self.rsaEncryptor.put_EncodingMode(ENCODE_MODE)
        self.firmwarePath = DEFUALT_FW
        # Init the UI here.
        self.hidenWidgetList = []
        mainUISizer = self.buildUISizer()
        self.SetSizer(mainUISizer)
        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText(
            'Please select the server you want to connect')
        # Hide the not active widgets.
        self.hideWidgets(hide=True)
        self.Show()

#-----------------------------------------------------------------------------
    def buildUISizer(self):
        """ Build the main UI sizer.  """
        sizer = wx.BoxSizer(wx.VERTICAL)
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        sizer.AddSpacer(5)
        # row idx = 1 server selection:
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
        # row idx = 2 user login area:
        hbox_2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox_2.Add(wx.StaticText(self, label=' '), flag=flagsR, border=2)
        self.userLb = wx.StaticText(self, label='UserName:')
        hbox_2.Add(self.userLb, flag=flagsR, border=2)
        self.userFI = wx.TextCtrl(
            self, -1, "", size=(100, -1), style=wx.TE_PROCESS_ENTER)
        self.userFI.SetBackgroundColour(wx.Colour(200, 200, 200))
        hbox_2.Add(self.userFI, flag=flagsR, border=2)
        self.pwdLb = wx.StaticText(self, label='PassWord:')
        hbox_2.Add(self.pwdLb, flag=flagsR, border=2)
        self.pwdFI = wx.TextCtrl(
            self, -1, "", size=(100, -1), style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        self.pwdFI.SetBackgroundColour(wx.Colour(200, 200, 200))
        hbox_2.Add(self.pwdFI, flag=flagsR, border=2)
        self.lgBt = wx.Button(self, label='LogIn', size=(70, 24))
        self.lgBt.Bind(wx.EVT_BUTTON, self.loginServer)
        hbox_2.Add(self.lgBt, flag=flagsR, border=2)
        sizer.Add(hbox_2, flag=flagsR, border=2)
        sizer.AddSpacer(10)
        # row idx = 3 Set the firmware file path:
        hbox_3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox_3.Add(wx.StaticText(self, label='FirmwarePath:'),
                   flag=flagsR, border=2)
        self.fmpath = wx.TextCtrl(
            self, -1, self.firmwarePath, size=(300, -1), style=wx.TE_PROCESS_ENTER)
        self.fmpath.SetBackgroundColour(wx.Colour(200, 210, 200))
        hbox_3.Add(self.fmpath, flag=flagsR, border=2)
        self.changeBt = wx.Button(self, label='change', size=(70, 24))
        self.changeBt.Bind(wx.EVT_BUTTON, self.changeFMPath)
        hbox_3.Add(self.changeBt, flag=flagsR, border=2)
        sizer.Add(hbox_3, flag=flagsR, border=2)
        sizer.AddSpacer(5)
        self.signBt = wx.Button(self, label='Sign firmware', size=(100, 24))
        self.signBt.Bind(wx.EVT_BUTTON, self.signFirmware)
        self.signBt.Enable(False)
        sizer.Add(self.signBt, flag=flagsR, border=2)
        self.hidenWidgetList.append(self.userLb)
        self.hidenWidgetList.append(self.userFI)
        self.hidenWidgetList.append(self.pwdLb)
        self.hidenWidgetList.append(self.pwdFI)
        self.hidenWidgetList.append(self.lgBt)
        return sizer

#-----------------------------------------------------------------------------
    def changeFMPath(self, event):
        """ Change the firmware file path. """
        with wx.FileDialog(self, "Open firmware file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            # Proceed loading the file chosen by the user
            self.firmwarePath = fileDialog.GetPath()
            self.fmpath.SetValue("")  # clear the path display area.
            self.fmpath.SetValue(self.firmwarePath)

#-----------------------------------------------------------------------------
    def connectToServer(self, event):
        """ Connect to the server(ip, port) based on users selection. """
        ServerName = self.serverchoice.GetString(
            self.serverchoice.GetSelection())
        ip, port = SERVER_CHOICE[ServerName]
        try:
            self.tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcpClient.connect((ip, port))
            connectRequest = self.msgMgr.dumpMsg(action='CR')
            self.tcpClient.send(connectRequest)
            response = self.tcpClient.recv(BUFFER_SIZE)
            dataDict = self.msgMgr.loadMsg(response)
            if dataDict['act'] == 'HB' and dataDict['lAct'] == 'CR':
                if dataDict['state']:
                    self.lgLb.SetLabel('Login [  %s  ]' % str(ServerName))
                    self.hideWidgets(hide=False)
                    self.SetStatusText("Connection: connected")
                else:
                    print("Connection: connection deny")
            else:
                print("Connection: connect fail")
        except:
            print("TCP connection fault.")
            self.tcpClient = None

#-----------------------------------------------------------------------------
    def fetchCert(self):
        """ Send the certificate file fetch request. """

        datab = self.msgMgr.dumpMsg(action='CF')
        self.tcpClient.send(datab)
        fileSize = 4096
        response = self.tcpClient.recv(fileSize)
        data = self.msgMgr.loadMsg(response)
        # here we assument the file not more than 4K
        if self.saveCert:
            #f = open(CER_PATH, "wb")
            f = open(SCER_PATH, "wb")
            f.write(data)
            f.close()
        else:
            self.bIOhandler = chilkat.CkBinData()
            # Append the bytes in the IO handler.
            for b in data:
                self.bIOhandler.AppendByte(b)
        print("Fetched the certificate file from the server.")

#-----------------------------------------------------------------------------
    def getMD5Hash(self, fname):
        """ Get the file MD5 hash value for the input file. """ 
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
#-----------------------------------------------------------------------------
    def getSWATThash(self, fname):
        """ Get the file SWATT hash """
        response = self.swattHd.getSWATT(self.swattChaStr, SWATT_ITER, fname)
        return response

#-----------------------------------------------------------------------------
    def hideWidgets(self, hide=False):
        """ Hide/show the UI Widgets in the hidenWidgetList."""
        for wideget in self.hidenWidgetList:
            if hide:
                wideget.Hide()
            else:
                wideget.Show()

#-----------------------------------------------------------------------------
    def getEncryptedStr(self, dataStr):
        """ Encrypte the dataString for sending. """
        usePrivateKey = False
        encryptedStr = self.rsaEncryptor.encryptStringENC(dataStr, usePrivateKey)
        return encryptedStr

#-----------------------------------------------------------------------------
    def loadCert(self):
        """ Load the certificate file and get the public key for signing the firmware. 
        """
        if self.saveCert and not os.path.exists(CER_PATH):
            print("The certificate file is not exist")
            return None
        cert = chilkat.CkCert()
        if self.saveCert:
            success = cert.LoadFromFile(CER_PATH)
        else:
            success = cert.LoadFromBd(self.bIOhandler)
        if not success:
            print(cert.lastErrorText())
            return None
        pubKey = cert.ExportPublicKey()
        success = self.rsaEncryptor.ImportPublicKey(pubKey.getXml())

    def loadPrivateK(self):
        if self.saveCert and not os.path.exists(SCER_PATH):
            print("The private file is not exist")
        with open(SCER_PATH,'rb') as f:
            self.priv_key = crypto.load_privatekey(crypto.FILETYPE_PEM, f.read())

#-----------------------------------------------------------------------------
    def loginServer(self, event):
        """ Login ther firmware sign server. """
        if self.tcpClient is None:
            return
        user, pwd = self.userFI.GetLineText(0), self.pwdFI.GetLineText(0)
        # Send the username and randome to server.
        datab, self.ownRandom = self.msgMgr.dumpMsg(action='LI1', dataArgs=[user])
        self.tcpClient.send(datab)
        response = self.tcpClient.recv(BUFFER_SIZE)
        dataDict = self.msgMgr.loadMsg(response)
        if dataDict['act'] == 'HB':
            if dataDict['lAct'] == 'LI1' and  not dataDict['state']: 
                print("Login: the user is not exist")
                return
        elif dataDict['act'] == 'LR1':
            if dataDict['state']:
                if  bytes.fromhex(dataDict['random1']) == self.ownRandom:
                    datab = self.msgMgr.dumpMsg(action='LI2', dataArgs=(dataDict['random2'], pwd))
                    self.tcpClient.send(datab)
                    response = self.tcpClient.recv(BUFFER_SIZE)
                    dataDict = self.msgMgr.loadMsg(response)
                    if dataDict['act'] =='LR2':
                        self.swattChaStr = dataDict['challenge']
                        self.signBt.Enable(True)
                        self.statusbar.SetStatusText("Login and fetch sertificate suscessful.")
                    else:
                        self.signBt.Enable(False)
                        self.statusbar.SetStatusText("UserName or password invalid")
                else:
                    print("Login: The server dosent response correctly.")
                    
            return

#-----------------------------------------------------------------------------
    def signFirmware(self, event):
        """ Sign the firmware file and send the data to server. 
        """
        self.fetchCert()
        print("sign the firmware")
        #self.loadCert()
        self.loadPrivateK()
        sensor_id = str(SENSOR_ID)
        signer_id = str(SIGNER_ID)
        swatt_str = self.getSWATThash(self.firmwarePath)
        date_str = str(datetime.now())
        sensor_type = 'XKAK_PPL_COUNT'
        version = '1.01'
        combinStr = ''.join([sensor_id, signer_id,swatt_str, date_str, sensor_type, version])
        #signature = self.getEncryptedStr(combinStr)
        signature = crypto.sign(self.priv_key, combinStr.encode('utf-8'), 'sha256')
        datab = self.msgMgr.dumpMsg(action='SR', dataArgs=(SENSOR_ID, SIGNER_ID,swatt_str, date_str, sensor_type, version, signature))
        self.tcpClient.send(datab)
        response = self.tcpClient.recv(BUFFER_SIZE)
        dataDict = self.msgMgr.loadMsg(response)
        if dataDict['act'] == 'HB' and dataDict['lAct']:
            print("The firmware is signed succesflly")

#-----------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        frame = FirmwareSignTool(None, -1, 'XAKA firmware sign tool')
        frame.Show(True)
        return True

app = MyApp(0)
app.MainLoop()
