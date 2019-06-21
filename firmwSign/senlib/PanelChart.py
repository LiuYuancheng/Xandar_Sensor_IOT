import wx
import time
import random

PERIODIC = 500  # how many ms the periodic call back


class PanelChart(wx.Panel):

    def __init__(self, parent, recNum):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        self.recNum = 60
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.data = [(0, 0, 0)]*60
        self.times = ('-30s', '-25s', '-20s', '-15s', '-10s', '-5s', '0s')

    def updateDisplay(self):
        self.Refresh(True)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.SetDeviceOrigin(40, 240)
        dc.SetAxisOrientation(True, True)
        dc.SetPen(wx.Pen('WHITE'))
        dc.DrawRectangle(1, 1, 300, 200)
        self.DrawAxis(dc)
        self.DrawGrid(dc)
        self.DrawTitle(dc)
        self.DrawData(dc)

    def DrawAxis(self, dc):
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

    def DrawGrid(self, dc):
        dc.SetPen(wx.Pen('#d5d5d5'))

        for i in range(20, 220, 20):
            dc.DrawLine(2, i, 300, i)

        for i in range(50, 300, 50):
            dc.DrawLine(i, 2, i, 200)

    def DrawTitle(self, dc):
        font = dc.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        dc.DrawText('XAKA sensor data', 90, 235)

    def addData(self, num):
        self.data.append(num)
        self.data.pop(0)

    def DrawData(self, dc):

        color = ('#0ab1ff', 'red', 'green')
        #dc.SetPen(wx.Pen('#0ab1ff'))
        for idx in range(3):
            dc.SetPen(wx.Pen(color[idx]))
            for i in range(len(self.data)-1):
                dc.DrawLine(
                    (i+1)*5, int(self.data[i][idx]*10), (i+2)*5, int(self.data[i+1][idx]*10))


class LineChartExample(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(390, 300))

        panel = wx.Panel(self, -1)
        panel.SetBackgroundColour('WHITE')

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.linechart = PanelChart(panel, 100)
        hbox.Add(self.linechart, 1, wx.EXPAND | wx.ALL, 15)
        panel.SetSizer(hbox)
        self.Centre()
        self.Show(True)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.periodic)
        self.timer.Start(PERIODIC)  # every 500 ms

    def periodic(self, event):
        num = random.randint(0, 20)
        self.linechart.addData(
            (random.randint(0, 20), random.randint(0, 20), random.randint(0, 20))
        self.linechart.updateDisplay()


app = wx.App()
LineChartExample(None, -1, 'A line chart')
app.MainLoop()
