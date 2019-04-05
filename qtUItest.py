import sys
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt 
from PyQt5.QtWidgets import(
        QApplication,QMainWindow, QWidget, QDesktopWidget,
        QToolTip, QPushButton, QMessageBox, QMenu, QAction, 
        QHBoxLayout, QVBoxLayout, QGridLayout,
        QLCDNumber, QSlider,
        qApp)

from PyQt5.QtGui import (QIcon, QFont)

nowStr = QDate.currentDate()
dateTimeStr = QDateTime.currentDateTime()
timeStr = QTime.currentTime()

#app = QApplication([])
#button = QPushButton("click test")

def onButtonClick():
    alert = QMessageBox()
    alert.setText("You clicked the button")
    alert.exec_

#button.clicked.connect(onButtonClick)
#button.show()
#app.exec_()
class Example(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setTitle()
        self.setGeometry(300, 300, 400, 300)
        self.buildTileArea()
        self.showButtons = False
        # set the tool tips:
        QToolTip.setFont(QFont('SansSerif', 10))
        self.setToolTip("This is a <b> QWidget </b> widget")
        # Set the box layout:
        bgWidgets = QWidget(self)
        vbox = QVBoxLayout()

        # Row 1: use GridLayout set the buttons.
        if self.showButtons:
            grid = QGridLayout()
            btLabels = [ 'clr', 'bck',  ' ',    'close', 
                        '7',   '8',    '9',    '/',
                        '4',   '5',    '6',    '*',
                        '1',   '2',    '3',    '-',
                        '0',   '.',    '=',    '+']

            positions = [(i,j) for i in range(5) for j in range(4)]
            for pos, name in zip(positions, btLabels):
                x, y = pos
                button = QPushButton(name)
                grid.addWidget(button, x, y)
            vbox.addLayout(grid)
        else:
            lcd = QLCDNumber(bgWidgets)
            vbox.addWidget(lcd)
            sld = QSlider(Qt.Horizontal, bgWidgets)
            vbox.addWidget(sld)
            sld.valueChanged.connect(lcd.display)

        # Add the buttons
        hbox = QHBoxLayout()
        hbox.addStretch(1)

        self.okBtn = QPushButton("OK", bgWidgets)
        hbox.addWidget(self.okBtn)
        self.cancelBtn = QPushButton("Cancel", bgWidgets)
        hbox.addWidget(self.cancelBtn)

        self.btn = QPushButton("Close window", bgWidgets)
        self.btn.resize(self.btn.sizeHint())
        self.btn.setToolTip("This is a <b> QwidgePushButton</b> widget")
        self.btn.clicked.connect(QApplication.instance().quit)
        hbox.addWidget(self.btn)
        vbox.addLayout(hbox)
        
        bgWidgets.setLayout(vbox)
        bgWidgets.show()

        self.setCentralWidget(bgWidgets)


        self.stateB = self.statusBar()
        self.stateB.showMessage("ready")
        self.setTitle()
        self.setCenter()
        # Show the applicatoin. 
        self.show()

    def buildTileArea(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        # Add the file bar.  
        exitAct = QAction(QIcon('exit.png'), '&exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip("Exit application")
        exitAct.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAct) 
        impMenu = QMenu('Import', self)
        impAct = QAction('Import emsil', self)
        impMenu.addAction(impAct)
        fileMenu.addMenu(impMenu)
        # Add the view bar 
        viewAction = QAction('View statusbar', self, checkable=True)
        viewAction.setStatusTip('View statusbar')
        viewAction.setChecked(True)
        viewAction.triggered.connect(self.toggleMenu)
        viewMenu = menubar.addMenu('view')
        mvMenu = QMenu('Move button', self)
        mvAction = QAction('move button', self)
        mvAction.setStatusTip('Move the button to the window center postion')
        mvAction.triggered.connect(self.moveButton)
        mvMenu.addAction(mvAction)
        viewMenu.addMenu(mvMenu)
        viewMenu.addAction(viewAction)
        # Add the tool bar. 
        self.toolbar = self.addToolBar('exit')
        self.toolbar.addAction(exitAct)

    def contextMenuEvent(self, event):
        """ Add the right click pop-up context menu. 
        """
        cmenu = QMenu(self)
        newAct = cmenu.addAction("New")
        openAct = cmenu.addAction("Open")
        quitAct = cmenu.addAction("Close")
        action = cmenu.exec_(self.mapToGlobal(event.pos()))
        # Check the user selection.
        print("user selected the action:" + str(action))
        if action == quitAct:
            qApp.quit()

    def keyPressEvent(self, e):
        """ listen the key press event. 
        """
        print("The key you pressed is :"+str(e.key()))
        if e.key() == Qt.Key_Escape:
            self.close()

    def setCenter(self):
        """ set the window to the center of the screen
        """
        size = self.frameGeometry()
        centerPt = QDesktopWidget().availableGeometry().center()
        size.moveCenter(centerPt)
        self.move(size.topLeft())

    def setTitle(self):
        """ Set the title bar of the window.
        """
        self.setWindowTitle("Icon test")
        self.setWindowIcon(QIcon('icon.jpg'))
        self.menubar = self.menuBar()

    def toggleMenu(self, state):
        
        if state:
            self.stateB.show()
        else:
            self.stateB.hide() 

    def moveButton(self, evet):
        """ Test move the button to the center poition. 
        """
        print("Enter the move button method")
        size = self.frameGeometry()
        #print("this is the qusize"+str(size))
        self.btn.move(100, 100)

    def closeEvent(self, event):
        """ pop-up confirm window for user to confirm quit action.
        """
        alert = QMessageBox.question(self, "Quit confirm", "Are u sure you want to quit?", 
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if alert == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Example()
    sys.exit(app.exec_())