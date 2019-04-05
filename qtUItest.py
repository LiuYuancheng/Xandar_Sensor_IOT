import sys
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt 
from PyQt5.QtWidgets import (QApplication,QMainWindow, QWidget, QDesktopWidget, QToolTip, 
        QPushButton, QMessageBox, QMenu, QAction, qApp)
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
        # Set exit action:
        exitAct = QAction(QIcon('exit.png'), '&exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip("Exit application")
        exitAct.triggered.connect(qApp.quit)
        # Add the menu bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        fileMenu.addAction(exitAct) 
        impMenu = QMenu('Import', self)
        impAct = QAction('Import emsil', self)
        impMenu.addAction(impAct)
        fileMenu.addMenu(impMenu)


        viewAction = QAction('View statusbar', self, checkable=True)
        viewAction.setStatusTip('View statusbar')
        viewAction.setChecked(True)
        viewAction.triggered.connect(self.toggleMenu)
        viewMenu = menubar.addMenu('view')
        viewMenu.addAction(viewAction)
        # Add the tool bar. 
        self.toolbar = self.addToolBar('exit')
        self.toolbar.addAction(exitAct)



        QToolTip.setFont(QFont('SansSerif', 10))
        self.setToolTip("This is a <b> QWidget </b> widget")
        #self.btn = QPushButton("Close window", self)
        #self.btn.resize(self.btn.sizeHint())
        #self.btn.setToolTip("This is a <b> QwidgePushButton</b> widget")
        #self.btn.clicked.connect(QApplication.instance().quit)
        self.setGeometry(300, 300, 330, 200)

        self.stateB = self.statusBar()
        self.stateB.showMessage("ready")
        self.setTitle()
        self.setCenter()
        # Show the applicatoin. 
        self.show()

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