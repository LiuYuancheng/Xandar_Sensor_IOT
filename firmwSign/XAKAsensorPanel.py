#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        XAKAsensorPanel.py
#
# Purpose:     This module is used to provide differentfunction panels for the 
#              XAKAsensorReader. 
#              
# Author:      Yuancheng Liu
#
# Created:     2019/06/24
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------
import wx
import time
import random

PERIODIC = 500  # how many ms the periodic call back

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class PanelBaseInfo(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size=(120, 300))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        
        self.valueDispList = []
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)
        for item in LABEL_LIST2:

            sizer.Add(wx.StaticText(self, -1, item))
            datalabel = wx.StaticText(self, -1, '--')
            self.valueDispList.append(datalabel)
            sizer.Add(datalabel,flag=flagsR, border=2)

        self.pauseBt = wx.Button(self, label='Pause', size=(100, 23))
        sizer.Add(self.pauseBt,flag=flagsR, border=2)
        self.detailBt = wx.Button(self, label='Detail >>', size=(100, 23))
        sizer.Add(self.detailBt,flag=flagsR, border=2)

        self.SetSizer(sizer)
        self.Show(True)
        
    def updateData(self, dataList):
        for i in range(len(dataList)):
             self.valueDispList[i].SetLabel(str(dataList[i]))
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class PanelChart(wx.Panel):
    """ This function is used to provide lineChart wxPanel to show the history 
        of the people counting sensor's data. 
    """
    def __init__(self, parent, recNum):
        """ Init the panel.
        """
        wx.Panel.__init__(self, parent, size=(350, 300))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        self.recNum = 60
        self.data = [(0,0,0)]* self.recNum #[(current num, average num, final num)]*60
        self.times = ('-30s', '-25s', '-20s', '-15s', '-10s', '-5s', '0s')
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def updateDisplay(self):
        
        self.Refresh(True)
        self.Update()

    #-----------------------------------------------------------------------------
    def OnPaint(self, event):
        """ Main panel drawing function."""
        dc = wx.PaintDC(self)
        # set the axis Orientation area and fmt to up+right direction.
        dc.SetDeviceOrigin(40, 240)
        dc.SetAxisOrientation(True, True)
        self.drawBG(dc)
        self.DrawFG(dc)
    #-----------------------------------------------------------------------------

    def drawBG(self, dc):
        """ Draw the line chart background."""
        dc.SetPen(wx.Pen('WHITE'))
        dc.DrawRectangle(1, 1, 300, 200)
        # Draw Axis:
        dc.SetPen(wx.Pen('#0AB1FF'))
        font = dc.GetFont()
        font.SetPointSize(8)
        dc.SetFont(font)
        dc.DrawLine(1, 1, 300, 1)
        dc.DrawLine(1, 1, 1, 201)
        for i in range(2, 22, 2):
            dc.DrawText(str(i), -30, i*10+5)
            dc.DrawLine(2, i*10, -5, i*10)
        for i in range(100, 300, 50):
            dc.DrawLine(i, 2, i, -5)
        for i in range(len(self.times)):
            dc.DrawText(self.times[i], i*50-10, -8)
        # Draw Grid :
        dc.SetPen(wx.Pen('#d5d5d5'))
        for i in range(20, 220, 20):
            dc.DrawLine(2, i, 300, i)
        for i in range(50, 300, 50):
            dc.DrawLine(i, 2, i, 200)
        # DrawTitle:
        font = dc.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        dc.DrawText('XAKA sensor data', 20, 235)

    #-----------------------------------------------------------------------------
    def addData(self, nums):
        for i, value in enumerate(nums, 1):
            if value> 20:
                nums[i] = 20
        self.data.append(nums)
        self.data.pop(0)

    #-----------------------------------------------------------------------------
    def DrawData(self, dc):
        color = ('#0ab1ff', 'red', 'green')
        label = ("Cur_N", "Avg_N", "Fnl_N") 
        #dc.SetPen(wx.Pen('#0ab1ff'))
        for idx in range(3):
            dc.SetPen(wx.Pen(color[idx], width=2, style=wx.PENSTYLE_SOLID))
            dc.DrawLine(idx*100, 210, idx*100+30, 210)
            dc.DrawText(label[idx], idx*100+35, 215)

            for i in range(len(self.data)-1):
                y1 = self.data[i][idx]*10 if self.data[i][idx]*10 <200 else 200
                y2 = self.data[i+1][idx]*10 if self.data[i+1][idx]*10<200 else 200
                dc.DrawLine((i+1)*5, int(y1), (i+2)*5, int(y2))

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class LineChartExample(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(390, 300))

        panel = wx.Panel(self, -1)
        panel.SetBackgroundColour('WHITE')

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.linechart = PanelChart(panel, 100)
        hbox.Add(self.linechart)
        panel.SetSizer(hbox)
        self.Centre()
        self.Show(True)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.periodic)
        self.timer.Start(PERIODIC)  # every 500 ms

    def periodic(self, event):
        num = random.randint(0, 20)
        self.linechart.addData(
            (random.randint(0, 20), random.randint(0, 20), random.randint(0, 20)))
        self.linechart.Refresh(True)


#app = wx.App()
#LineChartExample(None, -1, 'A line chart')
#app.MainLoop()
