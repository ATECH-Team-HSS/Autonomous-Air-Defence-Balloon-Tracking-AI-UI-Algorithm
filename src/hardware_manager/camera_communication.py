import cv2
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, pyqtSignal , Qt

class CameraCommunication(QWidget):
    connection_status = pyqtSignal(bool)
    error_happened = pyqtSignal(str)
    update_completed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cap = None
        self.cam_index = None

        # UI
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        # Timer, but we won't start until connect() is called
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def connect_camera(self, cam_index: int):
        self.cam_index = cam_index

        self.image_label.setText("Starting camera video feed...")

        try:
            self.cap = cv2.VideoCapture(self.cam_index)
            if not self.cap.isOpened():
                raise Exception("Camera could not be opened")
            self.connection_status.emit(True)
            self.update_completed.emit(f"[Camera] port {self.cam_index} connected successfully")
        except Exception as e:
            erMsg = f"[Camera] Error opening port {self.cam_index}"
            print(erMsg+ f" , Error(connect_camera): {e}")
            self.error_happened.emit(erMsg)
            self.cap = None
            self.connection_status.emit(False)
            return

        if self.cap.isOpened():
            self.connection_status.emit(True)
            self.timer.start(30)  # start updating frames
        else:
            self.connection_status.emit(False)

    def disconnect_camera(self):
        try:
            if self.cap and self.cap.isOpened():
                self.timer.stop()
                self.cap.release()
                self.cap = None
                self.connection_status.emit(False)
                self.update_completed.emit("[Camera] disconnected successfully")
                self.image_label.clear()
                self.image_label.setText("Video feed stopped.")
            else:
                self.error_happened.emit("[Camera] not connected")
        except Exception as e: 
            erMsg = f"[Camera] Error disconnecting camera {self.cam_index}"
            print(erMsg + f" , Error(disconnect_camera): {e}")
            self.error_happened.emit(erMsg)


    def update_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            center = (w // 2, h // 2)

            cv2.circle(frame, center, 10, (0,0,255), 2)
            cross_len = 20
            cv2.line(frame, (center[0]-cross_len, center[1]),
                             (center[0]+cross_len, center[1]), (0,0,255), 2)
            cv2.line(frame, (center[0], center[1]-cross_len),
                             (center[0], center[1]+cross_len), (0,0,255), 2)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(img))

    def closeEvent(self, event):
        self.disconnect_camera()
        event.accept()

