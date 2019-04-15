import sys
import random
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QApplication)
from PyQt5.QtGui import (QPainter, QColor, QFont)


class PaintTest(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 400, 300)
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

        qp.end()

    def drawText(self, event, qp):
        qp.setPen(QColor(168, 34, 3))
        qp.setFont(QFont('Decorative', 10))
        qp.drawText(event.rect(), Qt.AlignCenter, self.text)

    def drawPoints(self, event, qp):
        qp.setPen(QColor('green'))
        size = self.size()
        for i in range(1000):
            x = random.randint(1, size.width()-1)
            y = random.randint(1, size.height()-1)
            qp.drawPoint(x, y)

    def drawRectangles(self, event, qp):
        col = QColor(0, 0, 0)
        qp.setPen(col)

        qp.setBrush(QColor(200, 0, 0))
        qp.drawRect(10, 15, 90, 60)

        qp.setBrush(QColor(255, 80, 0, 160))
        qp.drawRect(130, 15, 90, 60)

        qp.setBrush(QColor(25, 0, 90, 200))
        qp.drawRect(250, 15, 90, 60)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    testUI = PaintTest()
    sys.exit(app.exec_())
