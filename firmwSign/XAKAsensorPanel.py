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
import firmwGlobal as gv 

PERIODIC = 500  # how many ms the periodic call back

LABEL_LIST2 = [
    'Seonsor ID:',  # int
    'Connection:',  # str
    'Sequence_N:',  # float
    'People_NUM:',  # float
    'Average_PP:',  # float
    'Final_PNUM:'   # float
]

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class PanelBaseInfo(wx.Panel):
    """ Panel to display the basic sensor information."""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size=(100, 300))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        self.valueDispList = []
        flagsR = wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)
        # Information rows
        for item in LABEL_LIST2:
            sizer.Add(wx.StaticText(self, -1, item))
            datalabel = wx.StaticText(self, -1, '--')
            self.valueDispList.append(datalabel)
            sizer.Add(datalabel, flag=flagsR, border=2)
        # Control button rows.
        self.pauseBt = wx.Button(self, label='Pause ||'.rjust(10), size=(80, 23))
        self.pauseBt.Bind(wx.EVT_BUTTON, self.pauseUpdate)
        sizer.Add(self.pauseBt, flag=flagsR, border=2)
        self.detailBt = wx.Button(self, label='Detail >>'.rjust(10), size=(80, 23))
        self.detailBt.Bind(wx.EVT_BUTTON, self.showDetail)
        sizer.Add(self.detailBt, flag=flagsR, border=2)
        self.SetSizer(sizer)
        self.Show(True)

    #-----------------------------------------------------------------------------
    def pauseUpdate(self, event):
        """ Start/Pause the update of the chart."""
        buttonLb = event.GetEventObject().GetLabel()
        if 'Pause' in buttonLb:
            self.pauseBt.SetLabel('Start >'.rjust(10))
            if gv.iChartPanel:
                gv.iChartPanel.updateDisplay(updateFlag=False)
        elif 'Start' in buttonLb:
            self.pauseBt.SetLabel('Pause ||'.rjust(10))
            if gv.iChartPanel:
                gv.iChartPanel.updateDisplay(updateFlag=True)

    #-----------------------------------------------------------------------------
    def showDetail(self, event):
        """ pop up the detail window to show the information.
        """
        pass

    #-----------------------------------------------------------------------------
    def updateData(self, dataList):
        """ Update the data display on the panel. Input parameter sequence and 
            type follow <LABEL_LIST2>. 
        """
        if len(dataList) != len(LABEL_LIST2):
            return
        for i, value in enumerate(dataList):
            dataStr = "{0:.2f}".format(value) if isinstance(
                value, float) else str(value)
            self.valueDispList[i].SetLabel(dataStr)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class PanelChart(wx.Panel):
    """ This function is used to provide lineChart wxPanel to show the history 
        of the people counting sensor's data.
        example:
        http://manwhocodes.blogspot.com/2013/04/graphics-device-interface-in-wxpython.html
    """
    def __init__(self, parent, recNum):
        """ Init the panel.
        """
        wx.Panel.__init__(self, parent, size=(350, 300))
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        self.recNum = 60
        self.updateFlag = True # flag whether we update the diaplay area
        self.data = [(0,0,0)]* self.recNum #[(current num, average num, final num)]*60
        self.times = ('-30s', '-25s', '-20s', '-15s', '-10s', '-5s', '0s')
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    #-----------------------------------------------------------------------------
    def AppendData(self, numsList):
        """ Append the data into the data hist list.
            numsList Fmt: [(current num, average num, final num)]
        """
        for i, value in enumerate(numsList):
            if value> 20: numsList[i] = 20
        self.data.append(numsList)
        self.data.pop(0) # remove the first oldest recode in the list.

    #-----------------------------------------------------------------------------
    def updateDisplay(self, updateFlag=None):
        """ Set/Update the display: if called as updateDisplay() the function will 
            update the panel, if called as updateDisplay(updateFlag=?) the function will 
            set the self update flag.
        """
        if updateFlag is None and self.updateFlag: 
            self.Refresh(True)
            self.Update()
        else:
            self.updateFlag = updateFlag

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
        # Draw Axis and Grids:
        dc.SetPen(wx.Pen('#D5D5D5')) #dc.SetPen(wx.Pen('#0AB1FF'))
        font = dc.GetFont()
        font.SetPointSize(8)
        dc.SetFont(font)
        dc.DrawLine(1, 1, 300, 1)
        dc.DrawLine(1, 1, 1, 201)
        for i in range(2, 22, 2): 
            dc.DrawLine(2, i*10, 300, i*10) # Y-Grid
            dc.DrawLine(2, i*10, -5, i*10)  # Y-Axis
            dc.DrawText(str(i).zfill(2), -25, i*10+5) # format to ## int  
        for i in range(len(self.times)): 
            dc.DrawLine(i*50, 2, i*50, 200) # X-Grid
            dc.DrawLine(i*50, 2, i*50, -5)  # X-Axis
            dc.DrawText(self.times[i], i*50-10, -5)
        # DrawTitle:
        font = dc.GetFont()
        #font.SetWeight(wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        dc.DrawText('XAKA sensor data', 2, 235)

    #-----------------------------------------------------------------------------
    def DrawFG(self, dc):
        """ Draw the front ground data chart line."""
        color = ('#0AB1FF', '#CE8349', '#A5CDAA')
        label = ("Cur_N", "Avg_N", "Fnl_N")
        for idx in range(3):
            # Draw the line sample.
            dc.SetPen(wx.Pen(color[idx], width=2, style=wx.PENSTYLE_SOLID))
            dc.DrawLine(100+idx*60, 212, 100+idx*60+8, 212)
            dc.DrawText(label[idx], idx*60+115, 220)
            # Create the point list and draw.
            dc.DrawSpline([(i*5, self.data[i][idx]*10)for i in range(len(self.data))])

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
