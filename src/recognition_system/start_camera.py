# -*- coding: utf-8 -*-
"""
Created on Thu May  8 11:00:10 2025

@author: Mahmoud Tafran
@email: mahmoudtafran40@gmail.com
"""
import sys
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

class Start_Camera(QWidget):
    def __init__(self,cam_index=0):
        super().__init__()
        self.setWindowTitle(f"{cam_index}.Camera Feed")
        self.image_label = QLabel()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.image_label)
        self.setLayout(self.layout)
        self.image_label.setScaledContents(True)

        # Start camera of the specified index (0.index = default camera , 1.index = external camera number 1)
        self.cam_index = cam_index
        self.cap = cv2.VideoCapture(self.cam_index)

        # Timer to grab frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 fps

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Flip the frame vertically and horizontally 
            # [1:flip about the y-axis , 0:flip about the x-axis , -1:flip both axes]
            frame = cv2.flip(frame, 1)

            height, width = frame.shape[:2]
            center = (width // 2, height // 2)

            # Draw red circle at center
            cv2.circle(frame, center, 10, (0, 0, 255), thickness=2)

            # Draw cross lines
            cross_len = 20
            cv2.line(frame, (center[0] - cross_len, center[1]),
                        (center[0] + cross_len, center[1]), (0, 0, 255), 2)
            cv2.line(frame, (center[0], center[1] - cross_len),
                        (center[0], center[1] + cross_len), (0, 0, 255), 2)

            # Convert to RGB and show
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QImage(frame, frame.shape[1], frame.shape[0],
                       frame.strides[0], QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(image))

    def closeEvent(self, event):
        self.cap.release()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Start_Camera()
    win.show()
    sys.exit(app.exec_())
