import sys
from PyQt5.QtWidgets import (QWidget, QSlider, QApplication, QHBoxLayout,
                             QHBoxLayout, QVBoxLayout, QMainWindow)

from PyQt5.QtCore import (QObject, Qt, pyqtSignal)

from PyQt5.QtGui import (QPainter, QFont, QColor, QPen, QBrush)

OVER_CAPACITY = 750


class Communiate(QObject):
    updateBW = pyqtSignal(int)


class ProgressWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.value = 75
        self.num = [75, 150, 225, 300, 375, 450, 525, 600, 675]
        self.initUI()

    def initUI(self):
        self.setMinimumSize(1, 30)

    def setValue(self, val):
        self.value = val

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.drawWidget(event, qp)
        qp.end()

    def drawWidget(self, event, qp):
        maxCapacity = 700
        font = QFont('Serif', 7, QFont.Light)
        qp.setFont(font)
        size = self.size()
        w, h = size.width(), size.height()
        
        till = int(w/OVER_CAPACITY*self.value)
        full = int(w/OVER_CAPACITY*maxCapacity)
        # Draw the pregress bar: 
        qp.setPen(QPen(QColor(255, 255, 255)))
        qp.setBrush(QBrush(QColor(255, 255, 184)))
        qp.drawRect(0, 0, till, h)

        if self.value > maxCapacity:
            qp.setPen(QColor(255, 175, 175))
            qp.setBrush(QColor(255, 175, 175))
            qp.drawRect(full, 0, till-full, h)

        # Draw the scal marker: 
        pen = QPen(QColor(20, 20, 20), 1,  Qt.SolidLine)
        qp.setPen(pen)
        qp.setBrush(Qt.NoBrush)
        qp.drawRect(0, 0, w-1, h-1)
        step = int(round(w/10))
        for idx, i in enumerate (range(step, 10*step, step)):
            qp.drawLine(i , 0 , i , 5)
            metrics = qp.fontMetrics()
            fw = metrics.width(str(self.num[idx]))
            qp.drawText(i-fw/2, h/2, str(self.num[idx]))

class CWidegt(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.sld = QSlider(Qt.Horizontal, self)
        self.sld.setFocusPolicy(Qt.NoFocus)
        self.sld.setRange(1, OVER_CAPACITY)
        self.sld.setValue(100)
        self.sld.setGeometry(30, 40, 150, 30)

        self.c = Communiate()
        self.wid = ProgressWidget()
        self.c.updateBW[int].connect(self.wid.setValue)
        self.sld.valueChanged[int].connect(self.changeValue)
        

        vbox = QVBoxLayout()
        vbox.addStretch(1)

        hbox = QHBoxLayout()
        hbox.addWidget(self.wid)
        
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.setGeometry(300, 300, 390, 210)
        self.setWindowTitle('Burning widget')
        self.show()

    def changeValue(self, value):
        self.c.updateBW.emit(value)
        self.wid.repaint() # Call repaint to re-draw the widget. 


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CWidegt()
    sys.exit(app.exec_())