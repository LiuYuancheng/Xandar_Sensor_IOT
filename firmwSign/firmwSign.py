#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        firmwareSign.py
#
# Purpose:     This module is used to connect to the firmware sign server and:
#               - Login to authorize the user.
#               - Download the sign sertificate and the swatt challenge string.
#               - Calculate firmware SWATT value and sign the related informaiton, 
#                 then feed back encrypted string to server.
# Author:      Yuancheng Liu
#
# Created:     2019/04/29
# Copyright:   NUS – Singtel Cyber Security Research & Development Laboratory
# License:     YC @ NUS
#-----------------------------------------------------------------------------

import os
import wx # use wx to build the UI.
import sys
import time
import json
import socket
import hashlib
import platform
import chilkat # need to download this lib.

import IOT_Att as SWATT
import firmwMsgMgr
import firmwTLSclient as SSLC
import firmwGlobal as gv

from functools import partial
from datetime import datetime
from OpenSSL import crypto
from Constants import BUFFER_SIZE, SWATT_ITER

SENSOR_ID   = 203   # default sernsor ID for test.
SIGNER_ID   = 154946511204681   # default signer user ID.

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class FirmwareSignTool(wx.Frame):
    """ Main firmware sign program.
    """
    def __init__(self, parent, id, title):
        """ Init the parameters and UI. """
        wx.Frame.__init__(self, parent, id, title, size=(450, 200))
        self.SetIcon(wx.Icon(gv.ICON_PATH))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        # Init parameters here:
        self.sslClient = SSLC.TLS_sslClient(self)   # changed to ssl client.
        self.msgMgr= firmwMsgMgr.msgMgr(self) # create the message manager.
        self.saveCert = True    # flag to specify whether we save certificate in local.
        self.bIOhandler = None  # ByteIO used to save the certificate in memory.
        self.ownRandom = None   # login random1
        self.serRandom = None   # random2 given by server.
        self.priv_key = None    # sign private key.
        self.firmwarePath = gv.DEFUALT_FW
        # Init the SWATT calculator. 
        self.swattHd = SWATT.swattCal()
        self.swattChaStr = 'Default Challenge String' 
        # Create the RSA encrypter(currently not use as we switch to new design)
        self.rsaEncryptor = chilkat.CkRsa()
        if not self.rsaEncryptor.UnlockComponent(gv.RSA_UNLOCK):
            print("RsaEncryptor: RSA component unlock failed.")
            #sys.exit()
        self.rsaEncryptor.put_EncodingMode(gv.RSA_ENCODE_MODE)
        # Init the UI here.
        self.hidenWidgetList = [] # widget will show if login in successful.
        self.SetSizer(self.buildUISizer())
        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText(
            'Please select the server you want to connect.')
        # Hide the not active widgets.
        self.hideWidgets(hide=True)
        self.Show()

#--FirmwareSignTool------------------------------------------------------------
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
            self, -1, choices=list(gv.SI_SERVER_CHOICE.keys()), name='Server')
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
        self.lgiBt = wx.Button(self, label='Login', size=(50, 24))
        self.lgiBt.Bind(wx.EVT_BUTTON, self.loginServer)
        hbox_2.Add(self.lgiBt, flag=flagsR, border=2)
        self.lgoBt = wx.Button(self, label='Logout', size=(50, 24))
        self.lgoBt.Bind(wx.EVT_BUTTON, self.logoutServer)
        hbox_2.Add(self.lgoBt, flag=flagsR, border=2)
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
        self.changeBt = wx.Button(self, label='Change', size=(70, 24))
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
        self.hidenWidgetList.append(self.lgiBt)
        self.hidenWidgetList.append(self.lgoBt)
        return sizer

#--FirmwareSignTool------------------------------------------------------------
    def changeFMPath(self, event):
        """ Pop-up a fileDialog to change the firmware file path. """
        with wx.FileDialog(self, "Open firmware file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL: return
            # Proceed loading the file chosen by the user
            self.firmwarePath = fileDialog.GetPath()
            self.fmpath.SetValue("")  # clear the path display area.
            self.fmpath.SetValue(self.firmwarePath)

#--FirmwareSignTool------------------------------------------------------------
    def connectToServer(self, event):
        """ Connect to the server(ip, port) based on user's selection. """
        ServerName = self.serverchoice.GetString(
            self.serverchoice.GetSelection())
        ip, port = gv.SI_SERVER_CHOICE[ServerName]
        try:
            self.sslClient.connect((ip, port))
            # Connect to server.
            connectRequest = self.msgMgr.dumpMsg(action='CR')
            self.sslClient.send(connectRequest)
            response = self.sslClient.recv(BUFFER_SIZE)                
            dataDict = self.msgMgr.loadMsg(response)
            if dataDict['act'] == 'HB' and dataDict['lAct'] == 'CR':
                if dataDict['state']:
                    self.lgLb.SetLabel('Login [ %s ]' %ServerName)
                    self.hideWidgets(hide=False)
                    self.SetStatusText("Connection: connected.")
                else:
                    print("Connection: connection denied.")
            else:
                print("Connection: connect fail.")
        except:
            print("Connection: TCP connection fault.")
            self.sslClient = None

#--FirmwareSignTool------------------------------------------------------------
    def fetchKeyFromServer(self):
        """ Send the private key file fetch request. """
        self.sslClient.send(self.msgMgr.dumpMsg(action='CF'))
        # Assume the sign certificate file is not more than 4K bytes.
        response = self.sslClient.recv(BUFFER_SIZE*4) 
        data = self.msgMgr.loadMsg(response)
        if self.saveCert:
            with open(gv.RECV_PRIK_PATH, "wb") as fh:
                fh.write(data)
        else:
            self.bIOhandler = chilkat.CkBinData()
            # Append the bytes in the IO handler.
            for b in data:
                self.bIOhandler.AppendByte(b)
        print("Fetched the certificate file from the server.")

#--FirmwareSignTool------------------------------------------------------------
    def getEncryptedStr(self, dataStr):
        """ Encrypte the dataString by rsa 2048 for sending. """
        usePrivateKey = False
        encryptedStr = self.rsaEncryptor.encryptStringENC(dataStr, usePrivateKey)
        return encryptedStr

#--FirmwareSignTool------------------------------------------------------------
    def getMD5Hash(self, fname):
        """ Get the input file's MD5 hash value.""" 
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

#--FirmwareSignTool------------------------------------------------------------
    def getSWATThash(self, fname):
        """ Get the input file SWATT hash value."""
        return self.swattHd.getSWATT(self.swattChaStr, SWATT_ITER, fname)

#--FirmwareSignTool------------------------------------------------------------
    def hideWidgets(self, hide=False):
        """ Hide/show the UI Widgets in the hidenWidgetList."""
        _ = [wideget.Hide() for wideget in self.hidenWidgetList] if hide else [
            wideget.Show() for wideget in self.hidenWidgetList]

#--FirmwareSignTool------------------------------------------------------------
    def loadCert(self):
        """ Load the certificate file and get the public key to sign the firmware."""
        if self.saveCert and not os.path.exists(gv.RECV_CERT_PATH):
            print("The certificate file is not exist.")
            return None
        cert = chilkat.CkCert()
        success = cert.LoadFromFile(
            gv.RECV_CERT_PATH) if self.saveCert else cert.LoadFromBd(self.bIOhandler)
        if not success:
            print(cert.lastErrorText())
            return None
        pubKey = cert.ExportPublicKey()
        success = self.rsaEncryptor.ImportPublicKey(pubKey.getXml())
        return success

#--FirmwareSignTool------------------------------------------------------------
    def loadPrivateKey(self, keyPath):
        """ Load private key from the sertificate file."""
        if self.saveCert and not os.path.exists(keyPath):
            print("The private key file is not exist.")
            return
        with open(keyPath, 'rb') as f:
            self.priv_key = crypto.load_privatekey(
                crypto.FILETYPE_PEM, f.read())

#--FirmwareSignTool------------------------------------------------------------
    def loginServer(self, event):
        """ Login the firmware sign server. """
        if self.sslClient is None: return
        user, pwd = self.userFI.GetLineText(0), self.pwdFI.GetLineText(0)
        # Send the username and randome to server.
        datab, self.ownRandom = self.msgMgr.dumpMsg(
            action='LI1', dataArgs=user)
        self.sslClient.send(datab)
        response = self.sslClient.recv(BUFFER_SIZE)
        dataDict = self.msgMgr.loadMsg(response)
        if dataDict['act'] == 'HB':
            if dataDict['lAct'] == 'LI1' and not dataDict['state']:
                print("Login: the user is not exist.")
                return
        elif dataDict['act'] == 'LR1':
            if dataDict['state']:
                if bytes.fromhex(dataDict['random1']) == self.ownRandom:
                    datab = self.msgMgr.dumpMsg(
                        action='LI2', dataArgs=(dataDict['random2'], pwd))
                    self.sslClient.send(datab)
                    response = self.sslClient.recv(BUFFER_SIZE)
                    dataDict = self.msgMgr.loadMsg(response)
                    if dataDict['act'] == 'LR2':
                        self.swattChaStr = dataDict['challenge']
                        self.signBt.Enable(True)
                        self.statusbar.SetStatusText(
                            "Login and fetch sertificate suscessful.")
                    else:
                        self.signBt.Enable(False)
                        self.statusbar.SetStatusText(
                            "UserName or password invalid")
                else:
                    print("Login: The server dosent response correctly.")

#--FirmwareSignTool------------------------------------------------------------
    def logoutServer(self, event):
        """ Log out from the firmware sign server."""
        # Send the logout requst.
        datab = self.msgMgr.dumpMsg(action='LO')
        self.sslClient.send(datab)
        # disconnect from the server.
        self.sslClient.close()
        self.signBt.Enable(False)
        self.hideWidgets(hide=True)
        
#--FirmwareSignTool------------------------------------------------------------
    def signFirmware(self, event):
        """ Sign the firmware file and send the data to server.(use SSL commmunication 
            private key to sign the data string.)
        """
        print("FirmwSign: starting sign the firmware")
        #self.loadCert()
        self.loadPrivateKey(gv.CSSL_PRIK_PATH)
        sensor_id, signer_id = str(SENSOR_ID), str(SIGNER_ID)
        self.swattHd.setPuff(SIGNER_ID)
        swatt_str = self.getSWATThash(self.firmwarePath)
        date_str = str(time.time()) #str(datetime.now())
        sensor_type, version = 'XKAK_PPL_COUNT', '30015.0'
        combinStr = ''.join([sensor_id, signer_id, swatt_str, date_str, sensor_type, version])
        #signature = self.getEncryptedStr(combinStr)
        signature = crypto.sign(self.priv_key, combinStr.encode('utf-8'), 'sha256')
        datab = self.msgMgr.dumpMsg(action='SR', dataArgs=(SENSOR_ID, SIGNER_ID, swatt_str, date_str, sensor_type, version, signature))
        self.sslClient.send(datab)
        response = self.sslClient.recv(BUFFER_SIZE)
        dataDict = self.msgMgr.loadMsg(response)
        if dataDict['act'] == 'HB' and dataDict['lAct'] and dataDict['state']:
            print("FirmwSign: The firmware is signed successfully.")
        else:
            print("FirmwSign: The firmware siganture is out of date.")

#--FirmwareSignTool------------------------------------------------------------
    def signFirmware_notinused(self, event):
        """ Sign the firmware file and send the data to server.(fetch the private 
            key from the server to sign the data string.) """
        self.fetchKeyFromServer()
        print("FirmwSign: starting sign the firmware")
        #self.loadCert()
        self.loadPrivateKey(gv.RECV_PRIK_PATH)
        sensor_id = str(SENSOR_ID)
        signer_id = str(SIGNER_ID)
        swatt_str = self.getSWATThash(self.firmwarePath)
        date_str = str(time.time())#str(datetime.now())
        sensor_type = 'XKAK_PPL_COUNT'
        version = '30015.0'
        combinStr = ''.join([sensor_id, signer_id,swatt_str, date_str, sensor_type, version])
        #signature = self.getEncryptedStr(combinStr)
        signature = crypto.sign(self.priv_key, combinStr.encode('utf-8'), 'sha256')
        datab = self.msgMgr.dumpMsg(action='SR', dataArgs=(SENSOR_ID, SIGNER_ID,swatt_str, date_str, sensor_type, version, signature))
        self.sslClient.send(datab)
        response = self.sslClient.recv(BUFFER_SIZE)
        dataDict = self.msgMgr.loadMsg(response)
        if dataDict['act'] == 'HB' and dataDict['lAct']:
            print("FirmwSign: The firmware is signed successfully.")

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        frame = FirmwareSignTool(None, -1, gv.APP_NAME)
        frame.Show(True)
        return True

app = MyApp(0)
app.MainLoop()
