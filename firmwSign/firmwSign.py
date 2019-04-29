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

SERVER_CHOICE = {
    "Local_test [127.0.0.1]"    : '127.0.0.1',
    "Server_1 [192.168.0.100]"  : '192.168.0.100'
}


class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        """ Init the UI. 
        """
        wx.Frame.__init__(self, parent, id, title, size=(450, 200))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        sizer = wx.BoxSizer(wx.VERTICAL)

        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        sizer.AddSpacer(5)
        hbox_1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox_1.Add(wx.StaticText(self, label='Server Selection: '),
                   flag=flagsR, border=2)
        self.serverchoice = wx.Choice(
            self, -1, choices=list(SERVER_CHOICE.keys()), name='Server')
        hbox_1.Add(self.serverchoice, flag=flagsR, border=2)
        self.connectBt = wx.Button(self, label='Connect', size=(70, 24))
        hbox_1.Add(self.connectBt, flag=flagsR, border=2)
        sizer.Add(hbox_1, flag=flagsR, border=2)
        sizer.AddSpacer(5)
        sizer.Add(wx.StaticText(self, label='Login [unconnected]: '),
                   flag=flagsR, border=2)
        sizer.AddSpacer(5)
        hbox_2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox_2.Add(wx.StaticText(self, label='User:'), flag=flagsR, border=2)
        self.userFI = wx.TextCtrl(self, -1, "", size=(100, -1), style=wx.TE_PROCESS_ENTER)
        self.userFI.SetEditable(False)
        self.userFI.SetBackgroundColour(wx.Colour(200, 200, 200))
        hbox_2.Add(self.userFI, flag=flagsR, border=2)
        hbox_2.Add(wx.StaticText(self, label='PassWord:'), flag=flagsR, border=2)
        self.pwdFI = wx.TextCtrl(self, -1, "", size=(100, -1), style=wx.TE_PROCESS_ENTER)
        self.pwdFI.SetEditable(False)
        self.pwdFI.SetBackgroundColour(wx.Colour(200, 200, 200))
        hbox_2.Add(self.pwdFI, flag=flagsR, border=2)
        sizer.Add(hbox_2, flag=flagsR, border=2)
        sizer.AddSpacer(5)
        # Set the firmware file path: 
        hbox_3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox_3.Add(wx.StaticText(self, label='FirmwarePath:'), flag=flagsR, border=2)
        self.fmpath = wx.TextCtrl(self, -1, "C:\Project\\testProgram\IOT\IOT", size=(300, -1), style=wx.TE_PROCESS_ENTER)
        self.fmpath.SetBackgroundColour(wx.Colour(200, 210, 200))
        hbox_3.Add(self.fmpath, flag=flagsR, border=2)
        self.changeBt = wx.Button(self, label='change', size=(70, 24))
        hbox_3.Add(self.changeBt, flag=flagsR, border=2)
        sizer.Add(hbox_3, flag=flagsR, border=2)
        sizer.AddSpacer(5)
        self.signBt = wx.Button(self, label='Sign firmware', size=(100, 24))
        sizer.Add(self.signBt, flag=flagsR, border=2)
        self.SetSizer(sizer)
        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText('Please select the server you want to connect')
        self.Show()

#-----------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, -1, 'XAKA firm ware sign')
        frame.Show(True)
        return True

app = MyApp(0)
app.MainLoop()
