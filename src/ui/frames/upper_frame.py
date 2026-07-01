import os
from PyQt5 import QtWidgets, QtGui, QtCore
from recognition_system.start_camera import Start_Camera
from hardware_manager.camera_communication import CameraCommunication
from balloon_shooter.ai_detection_widget import AIDetectionWidget

base_path = os.path.dirname(os.path.abspath(__file__))  # This is src/ui/frames
project_root = os.path.abspath(os.path.join(base_path, "..", "..", ".."))  # Go up to project root
assets_path = os.path.join(project_root, "assets")

class UpperFrame(QtWidgets.QFrame):
    # ────────────────Define signals ────────────────
    # Logging signals
    error_happened = QtCore.pyqtSignal(str)               # Error message
    update_happened = QtCore.pyqtSignal(str)              # Status message
    update_completed = QtCore.pyqtSignal(str)             # Completed message

    # Logic signals
    jog_slider_changed = QtCore.pyqtSignal(str, int)      # which slider, value
    pid_value_changed = QtCore.pyqtSignal(str, str, float)  # axis, pid_name, value
    aim_param_changed = QtCore.pyqtSignal(str, float)     # param name, value
    ports_configured = QtCore.pyqtSignal(str, str, int)        # name(camera or mcu), action(set ,connect ,disconnect), value


    def __init__(self, parent=None):
        super().__init__(parent)

        #──────────────── Frame setup ────────────────
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.setSizePolicy(sizePolicy)
        self.setMaximumWidth(2000)
        self.layout = QtWidgets.QHBoxLayout(self)



        # ─────────────── Recognition Frame ───────────────
        self.Recognition_frame = QtWidgets.QFrame()
        self.Recognition_frame.setMaximumHeight(630)
        self.Recognition_layout = QtWidgets.QStackedLayout(self.Recognition_frame)
        self.Recognition_layout.setContentsMargins(0, 0, 0, 0)

        # Camera Communication widget with no AI detection
        self.camera_widget = CameraCommunication()
        self.Recognition_layout.addWidget(self.camera_widget)
        self.layout.addWidget(self.Recognition_frame)
        # connecting signals
        self.camera_widget.update_completed.connect(self.update_completed.emit)
        self.camera_widget.error_happened.connect(self.error_happened.emit)

        # Camera Communication widget with  AI detection (balloon shooter package)
        self.ai_widget = AIDetectionWidget()
        self.Recognition_layout.addWidget(self.ai_widget)
        self.layout.addWidget(self.Recognition_frame)
        # ai system signals is proccesed inside the logic controller



        # ────────────── Mission Frame ────────────────
        self.Mission_frame = QtWidgets.QFrame()
        self.Mission_frame.setMinimumSize(QtCore.QSize(0, 600))
        self.Mission_frame.setMaximumSize(QtCore.QSize(400, 700))
        self.Mission_layout = QtWidgets.QVBoxLayout(self.Mission_frame)

        # Logo Frame
        self.ATech_logo_frame = QtWidgets.QFrame()
        self.ATech_logo_frame.setMinimumSize(QtCore.QSize(250, 250))
        self.logo_layout = QtWidgets.QHBoxLayout(self.ATech_logo_frame)

        self.logo_layout.addStretch()
        self.ATech_logo = QtWidgets.QLabel()
        self.ATech_logo.setScaledContents(True)
        image_path = os.path.join(assets_path, "ATech_logo.png")
        self.ATech_logo.setPixmap(QtGui.QPixmap(image_path))
        self.logo_layout.addWidget(self.ATech_logo)
        self.logo_layout.addStretch()

        self.Mission_layout.addWidget(self.ATech_logo_frame)



        # ──────────────── TabWidget ────────────────
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setFocusPolicy(QtCore.Qt.TabFocus)



        # ─────────── Tab 1: Mission Info ───────────
        tab1 = QtWidgets.QWidget()
        vlayout1 = QtWidgets.QVBoxLayout(tab1)

        # Dictionary to store reference for each label for later updates
        self.mission_info_labels = {} 

        for label_text, color in [
            ("Current Mission     ", "blue"),
            ("Detected Enemies    ", "rgb(144, 144, 0)"),
            ("Detected Friendlies ", "rgb(144, 144, 0)"),
            ("Auto Shoot          ", "green"),
            ("Auto Aim            ", "green"),
        ]:
            frame = QtWidgets.QFrame()
            layout = QtWidgets.QHBoxLayout(frame)
            label = QtWidgets.QLabel(label_text)
            label.setFont(QtGui.QFont("Rockwell", 14, QtGui.QFont.Bold))
            value = QtWidgets.QLabel("- -")
            value.setFont(QtGui.QFont("Rockwell", 14))
            value.setStyleSheet(f"color: {color};")

            layout.addWidget(label)
            layout.addStretch()
            layout.addWidget(value)
            vlayout1.addWidget(frame)

            self.mission_info_labels[label_text] = value

        self.tabWidget.addTab(tab1, "Mission")




        # ─────────── Tab 2: Jogging ───────────
        tab2 = QtWidgets.QWidget()
        vlayout2 = QtWidgets.QVBoxLayout(tab2)

        # Dictionary to store reference for each slider for later updates
        self.jog_sliders = {} 

        #hello mostafa
        for label_text in ["Tilt", "Pan", "Lasers"]:
            frame = QtWidgets.QFrame()
            layout = QtWidgets.QHBoxLayout(frame)
            label = QtWidgets.QLabel(f"Jog {label_text}")
            label.setFont(QtGui.QFont("Rockwell", 14, QtGui.QFont.Bold))
            label.setFixedWidth(180)
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setMinimum(-100)
            slider.setMaximum(100)
            slider.setValue(0)
            slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
            slider.setTickInterval(10)
            slider.setSingleStep(1)
            slider.setFixedWidth(150)
            layout.addWidget(label)
            layout.addSpacing(10)
            layout.addWidget(slider)
            layout.addStretch() 
            vlayout2.addWidget(frame)
            self.jog_sliders[label_text] = slider

        self.checkbox_enable_slider_jogging = QtWidgets.QCheckBox("Enable sliders")
        self.checkbox_enable_slider_jogging.setFont(QtGui.QFont("Rockwell", 12))
        self.checkbox_enable_slider_jogging.setMinimumHeight(20)
        vlayout2.addWidget(self.checkbox_enable_slider_jogging)

        self.tabWidget.addTab(tab2, "Jogging")

        # Connect jog sliders to signal
        for label, slider in self.jog_sliders.items():
            slider.valueChanged.connect(lambda value, lbl=label: self._emit_jog_value(lbl, value))
            slider.sliderReleased.connect(self._reset_jog_slider)

        self.checkbox_enable_slider_jogging.stateChanged.connect(
            lambda state: self.update_happened.emit(
                f"[Jogging] Slider jogging {'enabled' if state == QtCore.Qt.Checked else 'disabled'}"
            )
        )




        # ─────────── Tab 3: PID ───────────
        tab3 = QtWidgets.QWidget()
        vlayout3 = QtWidgets.QVBoxLayout(tab3)

        # Nested dictionaries: pid_current_value["Pan"]["P"] gives the QLabel
        self.pid_current_value = {"Pan": {}, "Tilt": {}}
        self.pid_new_value = {"Pan": {}, "Tilt": {}}
        self.pid_buttons = {"Pan": {}, "Tilt": {}}

        for axis in ["Pan", "Tilt"]:
            axis_label = QtWidgets.QLabel(f"{axis} Axis")
            axis_label.setFont(QtGui.QFont("Rockwell", 14, QtGui.QFont.Bold))
            vlayout3.addWidget(axis_label)

            for pid in ["P", "I", "D"]:
                frame = QtWidgets.QFrame() 
                layout = QtWidgets.QHBoxLayout(frame)
                layout.setContentsMargins(0, 0, 0, 0)  # add padding around items
                layout.setSpacing(5)

                label = QtWidgets.QLabel(f"{pid} value:    ")
                label.setFont(QtGui.QFont("Rockwell", 12))

                value = QtWidgets.QLabel("0")
                value.setFont(QtGui.QFont("Rockwell", 12))
                value.setStyleSheet("color: blue;")

                new_value = QtWidgets.QLineEdit()
                new_value.setMaximumWidth(55)

                set_button = QtWidgets.QPushButton(f"Set {pid}")

                layout.addWidget(label)
                layout.addWidget(value)
                layout.addWidget(new_value)
                layout.addWidget(set_button)
                vlayout3.addWidget(frame)

                # store references
                self.pid_current_value[axis][pid] = value
                self.pid_new_value[axis][pid] = new_value
                self.pid_buttons[axis][pid] = set_button

        # Add tab to widget
        self.tabWidget.addTab(tab3, "PID")

        # Connect PID adjustments to signal
        for axis, btns in self.pid_buttons.items():
            for pid, button in btns.items():
                # capture both axis and pid in the lambda
                button.clicked.connect(
                    lambda _, a=axis, k=pid: self._emit_pid_value(a, k)
                )




        # ─────────── Tab 4: Aiming ───────────
        tab4 = QtWidgets.QWidget()
        vlayout5 = QtWidgets.QVBoxLayout(tab4)

        # Dictionaries to store references
        self.aim_current_values = {}
        self.aim_new_values = {}
        self.aim_set_buttons = {}

        # Parameters we want to control
        for param in ["Min RPM", "Max RPM", "Aim Radius"]:
            frame = QtWidgets.QFrame()
            layout = QtWidgets.QHBoxLayout(frame)
            layout.setContentsMargins(3, 3, 3, 3)
            layout.setSpacing(5)

            # Label
            label = QtWidgets.QLabel(f"{param}:")
            label.setFont(QtGui.QFont("Rockwell", 12, QtGui.QFont.Bold))

            # Current value
            value = QtWidgets.QLabel("0")
            value.setFont(QtGui.QFont("Rockwell", 12))
            value.setStyleSheet("color: blue;")

            # New value input
            new_value = QtWidgets.QLineEdit()
            new_value.setMaximumWidth(55)

            # Set button
            set_button = QtWidgets.QPushButton(f"Set")

            layout.addWidget(label)
            layout.addStretch()
            layout.addWidget(value)
            layout.addSpacing(30)
            layout.addWidget(new_value)
            layout.addWidget(set_button)
            vlayout5.addWidget(frame)

            # Store references
            self.aim_current_values[param] = value
            self.aim_new_values[param] = new_value
            self.aim_set_buttons[param] = set_button

        # Checkboxes
        checkbox_frame = QtWidgets.QFrame()
        checkbox_layout = QtWidgets.QHBoxLayout(checkbox_frame)
        checkbox_layout.setContentsMargins(3, 3, 3, 3)
        checkbox_layout.setSpacing(5)

        self.checkbox_auto_aim = QtWidgets.QCheckBox("Auto Aim")
        self.checkbox_auto_aim.setFont(QtGui.QFont("Rockwell", 12))
        self.checkbox_auto_aim.setMinimumHeight(20)

        self.checkbox_auto_shoot = QtWidgets.QCheckBox("Auto Shoot")
        self.checkbox_auto_shoot.setFont(QtGui.QFont("Rockwell", 12))
        self.checkbox_auto_shoot.setMinimumHeight(20)

        checkbox_layout.addWidget(self.checkbox_auto_aim)
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.checkbox_auto_shoot)
        vlayout5.addWidget(checkbox_frame)

        # Add tab to the tabWidget
        self.tabWidget.addTab(tab4, "Aiming")

        # Connect aiming adjustments to signals
        for param, button in self.aim_set_buttons.items():
            button.clicked.connect(lambda _, p=param: self._emit_aim_param(p))
        
        # Connect checkboxes to signals
        self.checkbox_auto_aim.stateChanged.connect(
            lambda state: self.update_happened.emit(
                f"[Aiming] Trying to {'enable' if state == QtCore.Qt.Checked else 'disable'} Auto Aim"
            )
        )
        self.checkbox_auto_shoot.stateChanged.connect(
            lambda state: self.update_happened.emit(
                f"[Aiming] Trying to {'enable' if state == QtCore.Qt.Checked else 'disable'} Auto Shoot"
            )
        )





        # ─────────── Tab 5: Ports ───────────
        tab5 = QtWidgets.QWidget()
        vlayout5 = QtWidgets.QVBoxLayout(tab5)
 
        self.port_current_value = {}
        self.port_new_value = {}
        self.port_set_buttons = {}
        self.port_connect_buttons = {}
        self.port_disconnect_buttons = {} # dictionaries to store references
        for name in ["Camera", "MCU"]:
            frame = QtWidgets.QFrame()
            layout = QtWidgets.QHBoxLayout(frame)
            label = QtWidgets.QLabel(f"{name} Port")
            label.setFont(QtGui.QFont("Rockwell", 14, QtGui.QFont.Bold))
            current = QtWidgets.QLabel("")
            current.setFont(QtGui.QFont("Rockwell", 14))
            new = QtWidgets.QLineEdit()
            new.setMaximumWidth(40)
            set_button = QtWidgets.QPushButton(f"Set")
            set_button.setMaximumWidth(75)
            layout.addWidget(label)
            layout.addWidget(current)
            layout.addWidget(new)
            if name == "MCU":
                self.mcu_selector = QtWidgets.QComboBox()
                self.mcu_selector.addItems(["turret", "station"])
                self.mcu_selector.setMinimumHeight(23)
                layout.addWidget(self.mcu_selector)
            layout.addWidget(set_button)
            vlayout5.addWidget(frame)
            self.port_current_value[name] = current
            self.port_new_value[name] = new
            self.port_set_buttons[name] = set_button

            btn_frame = QtWidgets.QFrame()
            btn_layout = QtWidgets.QHBoxLayout(btn_frame)
            connect_btn = QtWidgets.QPushButton(f"Connect {name}")
            disconnect_btn = QtWidgets.QPushButton(f"Disconnect {name}")
            btn_layout.addWidget(connect_btn)
            btn_layout.addWidget(disconnect_btn)
            vlayout5.addWidget(btn_frame)
            self.port_connect_buttons[name] = connect_btn
            self.port_disconnect_buttons[name] = disconnect_btn

        # Connect port adjastments to signals
        for name, btn in self.port_set_buttons.items():
            btn.clicked.connect(lambda _, n=name: self._emit_ports_configured(n, "set", self.port_new_value[n].text()))

        for name, btn in self.port_connect_buttons.items():
            btn.clicked.connect(lambda _, n=name: self._emit_ports_configured(n, "connect" , self.port_new_value[n].text()))

        for name, btn in self.port_disconnect_buttons.items():
            btn.clicked.connect(lambda _, n=name: self._emit_ports_configured(n, "disconnect" ,self.port_new_value[n].text()))


        self.tabWidget.addTab(tab5, "Ports")
        self.Mission_layout.addWidget(self.tabWidget)

        self.tabWidget.setCurrentIndex(4)
        self.layout.addWidget(self.Mission_frame)




    def _emit_jog_value(self, lbl , value):
        # msg= f"[Jogging] Updating {lbl} angle value to {value} ..."
        # print(msg)
        # self.update_happened.emit(msg)

        try:
            self.jog_slider_changed.emit(lbl, value)

        except Exception as e:
            erMsg = f"Error in jog slider value emission for {lbl}"
            self.error_happened.emit(erMsg)
            print(f"{erMsg} , Error(_emit_jog_value): {e}")

    def _reset_jog_slider(self):
        # Reset all jog sliders to 0 when released
        for label, slider in self.jog_sliders.items():
            slider.setValue(0)

    def _emit_pid_value(self, axis, pid_name):
        try:
            # read the value first
            value = float(self.pid_new_value[axis][pid_name].text())
            
            # emit signal
            self.pid_value_changed.emit(axis, pid_name, value)

            # log message
            msg = f"[PID] Updating {axis} {pid_name} value to {value}"
            print(msg)
            self.update_happened.emit(msg)
            self.pid_current_value[axis][pid_name].setText(str(value))

        except ValueError as e:
            erMsg = (f"[PID] Invalid input for {axis} {pid_name} with value "
                    f"{self.pid_new_value[axis][pid_name].text()}")
            self.error_happened.emit(erMsg)
            print(f"{erMsg} , Error(_emit_pid_value): {e}")

    def _emit_aim_param(self, param):
        try:
            new_val = float(self.aim_new_values[param].text())

            msg= f"[Aiming] {param} updated to {new_val}"
            print(msg)
            self.update_happened.emit(msg)

            self.aim_current_values[param].setText(str(new_val))

            self.aim_param_changed.emit(param, new_val)
        except ValueError:
            erMsg = f"[Aiming] Invalid input for {param}"
            self.error_happened.emit(erMsg)
            print(erMsg)

    def _emit_ports_configured(self, name, action, value):
        msg= f"[{name}] {action}ing port number {value} ..."
        print(msg)
        self.update_happened.emit(msg)

        try:
            value = int(value)
            self.ports_configured.emit(name, action, value)

        except Exception as e:
            erMsg = f"[{name}] Invalid input for {action}ing port {value}"
            self.error_happened.emit(erMsg)
            print(f"{erMsg} , Error(_emit_ports_configured): {e}")

    def start_ai(self , cam_index=0):
        self.ai_widget.start(cam_index)

    def stop_ai(self):
        self.ai_widget.stop()    



            

    
