from PyQt5 import QtCore, QtGui, QtWidgets
from recognition_system.start_camera import Start_Camera
from ui.frames.lower_frame import LowerFrame
from ui.frames.middle_frame import MiddleFrame
from ui.frames.upper_frame import UpperFrame
from ui.signals_controller import SignalsMainController

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        # Set up the main window title , icon and size
        MainWindow.setWindowTitle("Air Defense ATech")
        MainWindow.setWindowIcon(QtGui.QIcon("assets/ATech_logo.png"))
        MainWindow.resize(1248, 864)
        
        # Set up the central widget that will hold all frames
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        # Main layout of the application
        self.layout = QtWidgets.QVBoxLayout(self.centralwidget)
        
        # Add the upper frame which contains the camera feed and mission info
        self.upper_frame = UpperFrame()
        self.layout.addWidget(self.upper_frame)

        # Add the middle frame which contains hardware info , control buttons and system status
        self.middle_frame = MiddleFrame()
        self.layout.addWidget(self.middle_frame)

        # Add the lower frame which contains the system log
        self.low_frame = LowerFrame()
        self.layout.addWidget(self.low_frame)

        # Connect signals using the SignalsMainController
        self.signals_controller = SignalsMainController(self.upper_frame, self.middle_frame, self.low_frame)

        #QtCore.QMetaObject.connectSlotsByName(MainWindow)



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
