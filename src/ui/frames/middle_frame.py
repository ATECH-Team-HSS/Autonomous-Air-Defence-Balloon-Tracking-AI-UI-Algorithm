from PyQt5 import QtWidgets, QtGui, QtCore


class MiddleFrame(QtWidgets.QFrame):
    # Define signals
    start_pressed = QtCore.pyqtSignal()
    stop_pressed = QtCore.pyqtSignal()
    shoot_pressed = QtCore.pyqtSignal()
    mission_selected = QtCore.pyqtSignal(str)
    error_happened = QtCore.pyqtSignal(str)              
    update_happened = QtCore.pyqtSignal(str)
    update_completed = QtCore.pyqtSignal(str)                

    def __init__(self, parent=None):
        super().__init__(parent)

        # Frame setup
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.setSizePolicy(sizePolicy)
        self.setMaximumWidth(2000)


        # Main horizontal layout of the middle frame
        self.layout = QtWidgets.QHBoxLayout(self)

        # ───── Commands and Hardware Info Frame ─────
        self.Commands_hardware_info_frame = QtWidgets.QFrame()
        self.Commands_hardware_info_frame.setMinimumSize(QtCore.QSize(1200, 150))
        self.verticalLayout = QtWidgets.QVBoxLayout(self.Commands_hardware_info_frame)

        # Commands Frame
        self.commands_frame = QtWidgets.QFrame()
        self.commandsLayout = QtWidgets.QHBoxLayout(self.commands_frame)

        self.Start_pushButton = self.create_button("START", "green")
        self.Stop_pushButton = self.create_button("STOP", "red")
        self.Shoot_pushButton = self.create_button("SHOOT", "blue")

        # make shoot button checkable
        self.Shoot_pushButton.setCheckable(True)

        self.commandsLayout.addWidget(self.Start_pushButton)
        self.commandsLayout.addWidget(self.Stop_pushButton)
        self.commandsLayout.addWidget(self.Shoot_pushButton)

        


        # Connect button signals
        self.Start_pushButton.clicked.connect(self._emit_start_preesed)
        self.Stop_pushButton.clicked.connect(self._emit_stop_pressed)
        self.Shoot_pushButton.toggled.connect(self._handle_shoot_toggled)

        self.Mission_select_comboBox = QtWidgets.QComboBox()
        self.Mission_select_comboBox.setMinimumHeight(42)
        self.Mission_select_comboBox.setStyleSheet("background-color:#c3c300")
        font = QtGui.QFont("Rockwell", 14)
        self.Mission_select_comboBox.setFont(font)
        self.Mission_select_comboBox.addItems(["Select mission", "Manual mode", "Mission 1", "Mission 2", "Mission 3"])
        self.commandsLayout.addWidget(self.Mission_select_comboBox)

        # Connect combo box signal
        self.Mission_select_comboBox.currentTextChanged.connect(lambda mission_name: self._emit_mission_selected(mission_name))

        self.verticalLayout.addWidget(self.commands_frame)

        # Hardware Info GroupBox
        self.GroupBox_actuators_info = QtWidgets.QGroupBox("Actuators Info")
        self.layout_3 = QtWidgets.QHBoxLayout(self.GroupBox_actuators_info)

        # Tilt angle group
        self.Tilt_angle = self.create_label("Tilt:")
        self.Tilt_angle_value = self.create_value_label("0°")
        tilt_angle_group_widget = self.create_group(self.Tilt_angle, self.Tilt_angle_value)

        # Pan angle group
        self.Pan_angle = self.create_label("Pan:")
        self.Pan_angle_value = self.create_value_label("0°")
        pan_angle_group_widget = self.create_group(self.Pan_angle, self.Pan_angle_value)

        # Tilt speed group
        self.Tilt_speed_label = self.create_label("Tilt speed: ")
        self.Tilt_command = self.create_value_label("")
        self.Tilt_speed = self.create_value_label("0 rpm ")
        
        tilt_speed_group_widget = self.create_group(self.Tilt_speed_label, self.Tilt_command)
        #tilt_speed_group_widget = self.create_group(self.Tilt_speed_label, self.Tilt_speed, self.Tilt_command)

        # Pan speed group
        self.Pan_speed_label = self.create_label("Pan speed: ")
        self.Pan_command = self.create_value_label("")
        self.Pan_speed = self.create_value_label("0 rpm ")
        
        pan_speed_group_widget = self.create_group(self.Pan_speed_label, self.Pan_command)
        #pan_speed_group_widget = self.create_group(self.Pan_speed_label, self.Pan_speed, self.Pan_command)

        # Laser status group
        self.Laser_status_label = self.create_label("Laser: ")
        self.Laser_status = self.create_value_label("")

        laser_group_widget = self.create_group(self.Laser_status_label, self.Laser_status)

        # Add all groups to the main layout

        # for w in [
        #             tilt_angle_group_widget,
        #             pan_angle_group_widget,
        #             tilt_speed_group_widget,
        #             pan_speed_group_widget,
        #             laser_group_widget
        #         ]:
        for w in [
            tilt_speed_group_widget,
            pan_speed_group_widget,
            laser_group_widget
        ]:
            self.layout_3.addWidget(w, alignment=QtCore.Qt.AlignVCenter)

        self.verticalLayout.addWidget(self.GroupBox_actuators_info)
        self.layout.addWidget(self.Commands_hardware_info_frame)

        # ───── System Status GroupBox ─────
        self.System_status_groupbox = QtWidgets.QGroupBox("System Status")
        self.System_status_groupbox.setMinimumSize(QtCore.QSize(200, 150))
        self.System_status_groupbox.setMaximumWidth(200)
        font = QtGui.QFont("Rockwell", 10)
        self.System_status_groupbox.setFont(font)

        # Create a layout for the groupbox
        status_layout = QtWidgets.QHBoxLayout(self.System_status_groupbox)

        # Create the icon label with the groupbox as parent
        self.system_status_icon = QtWidgets.QLabel(self.System_status_groupbox)
        self.system_status_icon.setScaledContents(True)
        self.system_status_icon.setText("")
        #self.system_status_icon.setPixmap(QtGui.QPixmap("assets/red_icon.png"))

        # Optional: fix a preferred size
        self.system_status_icon.setFixedSize(100, 100)  # adjust as needed

        # Add stretch, icon, stretch for centering
        status_layout.addStretch()
        status_layout.addWidget(self.system_status_icon, alignment=QtCore.Qt.AlignCenter)
        status_layout.addStretch()

        # Finally, add the groupbox to your main layout
        self.layout.addWidget(self.System_status_groupbox)

    def create_button(self, text, color):
        button = QtWidgets.QPushButton(text)
        button.setMinimumSize(QtCore.QSize(0, 40))
        button.setFont(QtGui.QFont("Rockwell", 14))
        button.setStyleSheet(f"background-color:{color}; color:white")
        return button

    def create_label(self, text):
        label = QtWidgets.QLabel(text)
        font = QtGui.QFont("Rockwell", 14, QtGui.QFont.Bold)
        label.setFont(font)

        # Force left alignment
        label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        #label.setFixedWidth(width)
        return label

    def create_value_label(self, text):
        label = QtWidgets.QLabel(text)
        palette = label.palette()
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(144, 144, 0))
        label.setPalette(palette)
        label.setFont(QtGui.QFont("Rockwell", 14))

        # Force left alignment
        label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        label.setFixedWidth(120)
        return label
    
    def create_group(self, *widgets, min_height=40, min_width=100, spacing=10):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 50, 13)
        layout.setSpacing(spacing)
        for w in widgets:
            layout.addWidget(w)
        group_widget = QtWidgets.QWidget()
        group_widget.setLayout(layout)
        group_widget.setMinimumHeight(min_height)
        group_widget.setMinimumWidth(min_width)

        
        return group_widget
  
    def _emit_start_preesed(self):
        try:
            self.start_pressed.emit()
            msg = "[System] Start pressed"
            self.update_happened.emit(msg)
            print(msg)
              
        except Exception as e:
            erMsg = f"[System] Error in emitting start signal"
            self.error_happened.emit(erMsg)
            print(f"{erMsg} , Error(_emit_start_preesed): {e}")

    def _emit_stop_pressed(self):
        try:
            self.stop_pressed.emit()
            msg = "[System] Stop pressed"
            self.update_happened.emit(msg)
            print(msg)
              
        except Exception as e:
            erMsg = f"[System] Error in emitting stop signal"
            self.error_happened.emit(erMsg)
            print(f"{erMsg} , Error(_emit_stop_pressed): {e}")

    # def _emit_shoot_pressed(self):
    #     try:
    #         self.shoot_pressed.emit()
    #         msg = "[System] Shoot pressed"
    #         self.update_happened.emit(msg)
    #         print(msg)
              
    #     except Exception as e:
    #         erMsg = f"[System] Error in emitting shoot signal"
    #         self.error_happened.emit(erMsg)
    #         print(f"{erMsg} , Error(_emit_shoot_pressed): {e}")

    def _handle_shoot_toggled(self, checked):
        try:
            if checked:
                # When toggled ON
                self.shoot_pressed.emit()
                msg = "[System] Shoot ON"
                self.update_happened.emit(msg)
                print(msg)
                # Optional: change button color to show ON state
                self.Shoot_pushButton.setStyleSheet("background-color: darkblue; color: white;")
            else:
                # When toggled OFF
                msg = "[System] Shoot OFF"
                self.update_happened.emit(msg)
                print(msg)
                # Optional: revert button color to show OFF state
                self.Shoot_pushButton.setStyleSheet("background-color: blue; color: white;")
        except Exception as e:
            erMsg = "[System] Error in toggling shoot"
            self.error_happened.emit(erMsg)
            print(f"{erMsg}, Error(_handle_shoot_toggled): {e}")


    def _emit_mission_selected(self, mission_name):
        try:
            if mission_name == "Select mission":
                raise ValueError("Please select a valid mission.")
            self.mission_selected.emit(mission_name)
            msg = f"[System] Mission selected: {mission_name}"
            self.update_completed.emit(msg)
            print(msg)
              
        except Exception as e:
            erMsg = f"[System] Error in choosing mission"
            self.error_happened.emit(erMsg + f" : {e}")
            print(f"{erMsg} , Error(_emit_mission_selected) : {e}")
