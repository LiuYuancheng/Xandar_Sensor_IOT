#!/usr/bin/python
# -----------------------------------------------------------------------------
# Name:        qtPain.py
#
# Purpose:     This module is used to test paint function on a Qtwidget.
#
# Author:      Yuancheng Liu
#
# Created:     2019/04/15
# Copyright:   YC
# License:     YC
# -----------------------------------------------------------------------------
import sys
import random
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QApplication)
from PyQt5.QtGui import (QPainter, QColor, QFont, QPen, QBrush, QPainterPath)

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class PaintTest(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 400, 600)
        self.text = 'color text test'
        self.setWindowTitle("PyQt paint test")
        self.show()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        # Draw the text line:
        self.drawText(event, qp)
        # Draw the point matrix
        self.drawPoints(event, qp)
        # Draw shap and compare color
        self.drawRectangles(event, qp)
        # Draw lines
        self.drawLines(event, qp)
        # Draw Brushes
        self.drawBrushes(event, qp)
        # Draw Curve
        self.drawCurve(event, qp)
        qp.end()

# -----------------------------------------------------------------------------
    def drawCurve(self, event, qp):
        """ Draw a Bézier curve
        """
        path = QPainterPath()
        # reset the pen and brush to default.
        qp.setPen(QPen())
        qp.setBrush(QBrush())
        path.moveTo(30, 30)
        path.cubicTo(30, 30, 200, 350, 350, 30)
        qp.drawPath(path)

    def drawText(self, event, qp):
        """ Draw color text. 
        """
        qp.setPen(QColor(168, 34, 3))
        qp.setFont(QFont('Decorative', 10))
        qp.drawText(event.rect(), Qt.AlignCenter, self.text)

    def drawPoints(self, event, qp):
        """ Draw random points.
        """
        qp.setPen(QColor('green'))
        size = self.size()
        for _ in range(1000):
            qp.drawPoint(random.randint(1, size.width()-1),
                         random.randint(1, size.height()-1))

    def drawRectangles(self, event, qp):
        """ Draw different color rectangles
        """
        col = QColor(0, 0, 0)
        qp.setPen(col)
        qp.setBrush(QColor(200, 0, 0))
        qp.drawRect(10, 15, 90, 60)
        qp.setBrush(QColor(255, 80, 0, 160))
        qp.drawRect(130, 15, 90, 60)
        qp.setBrush(QColor(25, 0, 90, 200))
        qp.drawRect(250, 15, 90, 60)

    def drawLines(self, event, qp):
        """ Draw different style of lines.
        """
        pen = QPen(Qt.blue, 2, Qt.SolidLine)
        qp.setPen(pen)
        y, offset = 80, 10
        # Draw solidline
        qp.setPen(pen)
        qp.drawLine(20, y, 250, y)
        y += offset
        # Draw othe line
        styleList = (Qt.DashLine, Qt.DashDotLine,
                     Qt.DotLine, Qt.DashDotDotLine)
        for sytleI in styleList:
            pen.setStyle(sytleI)
            qp.setPen(pen)
            qp.drawLine(20, y, 250, y)
            y += offset
        # Draw customer line:
        pen.setStyle(Qt.CustomDashLine)
        pen.setDashPattern([1, 4, 5, 4])
        qp.setPen(pen)
        qp.drawLine(20, y, 250, y)

    def drawBrushes(self, event, qp):
        """ Draw different style rectangles.
        """
        brushesList = (Qt.SolidPattern, Qt.Dense1Pattern, Qt.Dense2Pattern, Qt.DiagCrossPattern,
                       Qt.Dense5Pattern, Qt.Dense6Pattern, Qt.HorPattern, Qt.VerPattern, Qt.BDiagPattern)
        for idx, item in enumerate(brushesList):
            x = 10 + (idx % 3)*100
            y = 400 + (idx//3)*70
            brush = QBrush(item)
            qp.setBrush(brush)
            qp.drawRect(x, y, 90, 60)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    testUI = PaintTest()
    sys.exit(app.exec_())
