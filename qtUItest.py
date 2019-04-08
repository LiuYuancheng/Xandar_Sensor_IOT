import sys
from PyQt5.QtCore import QDate, QTime, QDateTime, QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import(
        QApplication,QMainWindow, QWidget, QDesktopWidget,
        QToolTip, QPushButton, QMessageBox, QMenu, QAction, 
        QHBoxLayout, QVBoxLayout, QGridLayout, QFrame, QLabel,
        QLCDNumber, QSlider, QLineEdit, QInputDialog, QColorDialog, QFontDialog, QFileDialog,
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

class Communicate(QObject):
    closeApp = pyqtSignal()

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
        self.bgWidgets = QWidget(self)


        vbox = QVBoxLayout()
        # Add the line edit used for the title area
        self.le = QLineEdit(self.bgWidgets)
        vbox.addWidget(self.le)
        self.lbl = QLabel('Text string use to test different format string', self.bgWidgets)
        vbox.addWidget(self.lbl)
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
            lcd = QLCDNumber(self.bgWidgets)
            vbox.addWidget(lcd)
            sld = QSlider(Qt.Horizontal, self.bgWidgets)
            vbox.addWidget(sld)
            sld.valueChanged.connect(lcd.display)

        # Add the buttons
        hbox = QHBoxLayout()
        hbox.addStretch(1)

        self.okBtn = QPushButton("OK", self.bgWidgets)
        self.okBtn.clicked.connect(self.buttonClicked)
        hbox.addWidget(self.okBtn)
        self.cancelBtn = QPushButton("Cancel", self.bgWidgets)
        self.cancelBtn.clicked.connect(self.buttonClicked)
        hbox.addWidget(self.cancelBtn)

        self.btn = QPushButton("Close window", self.bgWidgets)
        self.btn.resize(self.btn.sizeHint())
        self.btn.setToolTip("This is a <b> QwidgePushButton</b> widget")
        self.btn.clicked.connect(QApplication.instance().quit)
        hbox.addWidget(self.btn)
        vbox.addLayout(hbox)
        
        self.bgWidgets.setLayout(vbox)
        self.bgWidgets.show()

        self.setCentralWidget(self.bgWidgets)
        # emit event from mouse click event:
        self.comm = Communicate()
        self.comm.closeApp.connect(self.close)

        self.stateB = self.statusBar()
        self.stateB.showMessage("ready")
        self.setTitle()
        self.setCenter()
        # Show the applicatoin. 
        # Set evet
        self.setMouseTracking(True)
        self.show()

    def buildTileArea(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')

        fileAct = QAction(QIcon('open.png'), 'Open', self)
        fileAct.setShortcut('Ctrl+O')
        fileAct.setStatusTip('Pop up file selection dialog.')
        fileAct.triggered.connect(self.popUPfillin)
        fileMenu.addAction(fileAct)
        # Add the file bar.  
        exitAct = QAction(QIcon('exit.png'), '&exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip("Exit application")
        exitAct.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAct) 
        impMenu = QMenu('Import', self)
        # Add the import email action. 
        impEmAct = QAction('Import email', self)
        impEmAct.triggered.connect(self.popUPfillin)
        impMenu.addAction(impEmAct)

        # Add the import color selection action. 
        impCoAct = QAction('Import bgColor', self)
        impCoAct.triggered.connect(self.popUPfillin)
        impMenu.addAction(impCoAct)
        
        # Add the text format change selection action. 
        impFtAct = QAction('Import font', self)
        impFtAct.triggered.connect(self.popUPfillin)
        impMenu.addAction(impFtAct)

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

    def buttonClicked(self):
        sender = self.sender()
        print("Button clicked:"+sender.text())

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

    def mouseMoveEvent(self, e):
        x, y = e.x(), e.y()
        self.stateB.showMessage("x :{0}, y:{1}".format(x, y))

    def mousePressEvetn(self, e):
        self.comm.closeApp.emit()

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

    def popUPfillin(self, event):
        sender = self.sender()
        print("This is the sender: "+str(sender.text()))
        senderStr = sender.text()
        if senderStr == 'Import email':
            text, ok = QInputDialog.getText(self.bgWidgets, 'Email', 
                'Enter your email:')
            if ok: self.le.setText(str(text))
        elif senderStr == 'Import bgColor':
            col = QColorDialog.getColor()
            if col.isValid():
                self.setStyleSheet("QWidget { background-color: %s }" % col.name())
        elif senderStr == 'Import font':
            font, ok = QFontDialog.getFont()
            if ok: self.lbl.setFont(font)
        else:
            fname = QFileDialog.getOpenFileName(self, 'Open file', 'C:')
            if fname[0]:
                with open(fname[0], 'r') as f:
                    data = f.read()
                    self.le.setText(str(data))

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
