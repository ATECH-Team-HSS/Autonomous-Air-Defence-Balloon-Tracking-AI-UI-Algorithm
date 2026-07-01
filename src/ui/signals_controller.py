import os
import math
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer
from hardware_manager.mcu_communication import McuCommunication
from hardware_manager.pid_tracker import TargetPID

base_path = os.path.dirname(os.path.abspath(__file__))  # This is src/ui/frames
project_root = os.path.abspath(os.path.join(base_path, "..", ".."))  # Go up to project root
assets_path = os.path.join(project_root, "assets")

class SignalsMainController:
    def __init__(self, upper_frame, middle_frame, lower_frame):
        self.upper_frame = upper_frame
        self.middle_frame = middle_frame
        self.lower_frame = lower_frame

        # Set up hardware communication
        self.mcu_communication = McuCommunication()
        self.command_freq = 50 # ms
        self.command_timer = QTimer()
        self.command_timer.setInterval(self.command_freq)
        self.camera_port = None
        self.mcu_port = None
        self.mcu_connection_status = False

        # Set up status of control station hardware components
        # buttons & selectors
        self.start_slc = False
        self.last_start_slc_state = False
        self.laser_blue_btn = False
        self.laser_green_btn = False
        self.mission_1_slc = False
        self.mission_2_slc = False
        self.mission_3_slc = False
        self.manual_mode_slc = False
        self.last_mission_slc_state = None
        self.confirm_target_btn = False
        # joystick
        self.pot_pan = 0.0
        self.pot_tilt = 0.0
        self.pot_focus = 0.0
        self.pot_press = False

        # Set up PID targeting system
        self.system_enabled = False
        self.cx=None
        self.cy=None
        self.frame_center_x = 640 # Default center for 1280x720 resolution
        self.frame_center_y = 380
        self.enable_pid = False
        self.enable_aim = False
        self.enable_shoot = False
        self.kp_pan = 0.02
        self.ki_pan = 0.0
        self.kd_pan = 0.03
        self.kp_tilt = 0.02
        self.ki_tilt = 0.0
        self.kd_tilt = 0.03
        self.min_rpm = 0.1
        self.max_rpm = 5.0
        self.shoot_region_radius = 50.0
        self.pan_cmd = 0.0
        self.tilt_cmd = 0.0
        self.shoot = False
        self.previous_shoot = False
        self.shoot_laser1 = False
        self.shoot_laser2 = False
        self.shoot_laser3 = False
        self.shoot_buzzer = False

        # Set up detection timeout
        # This timer will be used to disable PID if no balloon is detected for a certain time
        self.detection_timeout_ms = 300 
        self.detection_timer = QTimer()
        self.detection_timer.setInterval(self.detection_timeout_ms)
        self.detection_timer.setSingleShot(True)  # Only fire once unless restarted
        self.detection_timer.timeout.connect(self._handle_detection_timeout)
        

        self.slider_jogging_enabled = False
        # Setup working mode
        self.mission_name = None

        self.frendlies_number = 0
        self.enemies_number = 0

        self.shoot_gui = False


        self._connectSignals()        

    def _connectSignals(self):

        # ─────────── Connect logging signals ───────────
        # upper frame
        self.upper_frame.error_happened.connect(self.lower_frame.log_error)
        self.upper_frame.update_happened.connect(self.lower_frame.log_update)
        self.upper_frame.update_completed.connect(self.lower_frame.log_completed)
        

        # middle frame
        self.middle_frame.error_happened.connect(self.lower_frame.log_error)
        self.middle_frame.update_happened.connect(self.lower_frame.log_update)
        self.middle_frame.update_completed.connect(self.lower_frame.log_completed)

        # AI
        self.upper_frame.ai_widget.status_message.connect(self.lower_frame.log_ai_system)

        # MCU
        self.mcu_communication.error_happened.connect(self.lower_frame.log_error)
        self.mcu_communication.update_happened.connect(self.lower_frame.log_update)
        self.mcu_communication.update_completed.connect(self.lower_frame.log_completed)

        # ─────────── Connect logic signals ───────────
        # mission operrations and commands
        self.middle_frame.mission_selected.connect(self._handle_mission_selected)
        self.middle_frame.Start_pushButton.clicked.connect(self._handle_starting_mission)
        self.middle_frame.Stop_pushButton.clicked.connect(self._handle_stopping_mission)
        self.middle_frame.Shoot_pushButton.toggled.connect(self._handle_shoot_toggled)

        # AI system
        self.upper_frame.ai_widget.AI_detection_running.connect(self._handle_ai_detection_running)
        self.upper_frame.ai_widget.balloon_position.connect(self._handle_new_balloon_position)
        self.upper_frame.ai_widget.balloon_counts.connect(self._handle_new_balloon_counts)
        self.upper_frame.ai_widget.camera_size.connect(self._handle_frame_size)

        # mcu communication
        self.mcu_communication.data_received.connect(self._handle_mcu_data)
        self.mcu_communication.connection_status.connect(self._handle_mcu_connection_status)
        
        # configure ports
        self.upper_frame.ports_configured.connect(self._handle_port_configration)

        # jogging sliders
        self.upper_frame.checkbox_enable_slider_jogging.stateChanged.connect(self._handle_slider_jogging_enable_changed)
        self.upper_frame.jog_slider_changed.connect(self._handle_jogging_command)

        # command sender
        self.command_timer.timeout.connect(self._send_command)
        self.upper_frame.pid_value_changed.connect(self._handle_pid_value_changed)
        self.upper_frame.aim_param_changed.connect(self._handle_aim_param_changed)

        # auto aim and shoot mode
        self.upper_frame.checkbox_auto_aim.stateChanged.connect(self._handle_auto_aim_changed)
        self.upper_frame.checkbox_auto_shoot.stateChanged.connect(self._handle_auto_shoot_changed)
        


    def _handle_port_configration(self, name, action, value):
        try:
            if action == "set":
                # Set the port for the specified hardware component
                if name == "Camera":
                    self.camera_port = value
                    self.lower_frame.log_completed(f"[Camera] port set to {value}")
                elif name == "MCU":
                    self.mcu_port = value
                    self.lower_frame.log_completed(f"[MCU] port set to {value}")

            elif action == "connect":
                # Connect to the specified hardware component
                if name == "Camera":
                        self.upper_frame.Recognition_layout.setCurrentWidget(self.upper_frame.camera_widget)
                        self.upper_frame.camera_widget.connect_camera(value)
                elif name == "MCU":
                    if self.upper_frame.mcu_selector.currentText() == "turret":
                        self.mcu_communication.connect_mcu_turret(value)
                        # Start the timer responsible for sending commands if not already activated
                        if not self.command_timer.isActive():
                            self.lower_frame.log_completed(f"[Command processor] started its timer with {self.command_freq}ms sending rate")
                            self.command_timer.start()
                    elif self.upper_frame.mcu_selector.currentText() == "station":
                        self.mcu_communication.connect_mcu_station(value)


            elif action == "disconnect":
                # Disconnect the specified hardware component
                if name == "Camera":
                    self.upper_frame.camera_widget.disconnect_camera()
                elif name == "MCU":
                    if self.upper_frame.mcu_selector.currentText() == "turret":
                        self.mcu_communication.disconnect_mcu_turret()
                        # Stop the timer responsible for sending commands if activated
                        if self.command_timer.isActive():
                            self.command_timer.stop()
                            self.lower_frame.log_completed(f"[Command processor] stopped its timer")
                    elif self.upper_frame.mcu_selector.currentText() == "station":
                        self.mcu_communication.disconnect_mcu_station()

        except Exception as e:
            self.lower_frame.log_error(f"Error in port logic: {e}")

    def _handle_mcu_data(self, data: dict):
        if data.get("type") == "status":
            try:
                # motors info feedback (currently not used)
                tilt_angle = data["motion"]["tilt_angle_deg"]
                #self.middle_frame.Tilt_angle_value.setText(f"{tilt_angle:.1f}°")
                pan_angle = data["motion"]["pan_angle_deg"]
                #self.middle_frame.Pan_angle_value.setText(f"{pan_angle:.1f}°")
                tilt_speed = data["motion"]["tilt_speed_rpm"]
                #self.middle_frame.Tilt_speed.setText(f"{tilt_speed:.1f} rpm")
                pan_speed = data["motion"]["pan_speed_rpm"]
                #self.middle_frame.Pan_speed.setText(f"{pan_speed:.1f} rpm")

                # btns and selectors feedback
                self.start_slc = data["buttons"]["arm"]
                self.laser_blue_btn = data["buttons"]["laser_blue"]
                self.laser_green_btn = data["buttons"]["laser_green"]
                self.mission_1_slc = data["buttons"]["stage1"]
                self.mission_2_slc = data["buttons"]["stage2"]
                self.mission_3_slc = data["buttons"]["stage3"]
                self.manual_mode_slc = data["buttons"]["manual_mode"]
                self.confirm_target_btn = data["buttons"]["confirm_target"]

                # Pot values
                self.pot_pan = data["joystick"]["pot_pan"]
                self.pot_tilt = data["joystick"]["pot_tilt"]
                self.pot_focus = data["joystick"]["pot_focus"]
                self.pot_press = data["joystick"]["press"]

                # mission slectors
                # modify the mission from the selector on the control station when comboBox is on "Select mission"
                if self.middle_frame.Mission_select_comboBox.currentText() == "Select mission":
                    if self.mission_1_slc:self.mission_name= "Mission 1"
                    if self.mission_2_slc:self.mission_name= "Mission 2"
                    if self.mission_3_slc:self.mission_name= "Mission 3"
                    if self.manual_mode_slc:self.mission_name= "Manual mode"

                    # Update the mission info label and logic of the mission only if it has changed
                    if self.mission_name is not None and (self.mission_name != self.last_mission_slc_state):
                        self.upper_frame.mission_info_labels["Current Mission     "].setText(f"{self.mission_name}")
                        self.lower_frame.log_update(f"[Control station] {self.mission_name} selected")
                        if self.mission_name == "Manual mode":
                            self.enable_aim, self.enable_shoot = False, False
                        elif self.mission_name == "Mission 1":
                            self.enable_aim, self.enable_shoot = True, False
                        elif self.mission_name == "Mission 2":
                            self.enable_aim, self.enable_shoot = True, True
                        elif self.mission_name == "Mission 3":
                            pass # Mission 3 is not implemented yet
                            #self.enable_aim, self.enable_shoot = True, True
                        self._handle_auto_aim_changed(self.enable_aim)
                        self._handle_auto_shoot_changed(self.enable_shoot)

                    self.last_mission_slc_state = self.mission_name

                
                # start stop selector
                if self.start_slc != self.last_start_slc_state:
                    # Selector position changed
                    if self.start_slc:  # switched to START
                        self.lower_frame.log_update("[Control station] Start pressed")
                        self._handle_starting_mission()
                    else:  # switched to STOP
                        self.lower_frame.log_update("[Control station] Stop pressed")
                        self._handle_stopping_mission()

                self.last_start_slc_state = self.start_slc

            except Exception as e:
                self.lower_frame.log_error(f"[MCU] Error while unpacking data: {e}")
        else:
            self.lower_frame.log_error("[MCU] Recieved Control Command instead of status msg")

    def _handle_mcu_connection_status(self , status):
        self.mcu_connection_status= status

    def _handle_mission_selected(self ,mission):
        self.mission_name = mission
        self.upper_frame.mission_info_labels["Current Mission     "].setText(f"{mission}")

    def _handle_ai_detection_running(self, running):
            if running:
                self.lower_frame.log_completed("[System] AI system started")
            else:
                self.lower_frame.log_completed("[System] AI system stopped")
                self.set_system_status_icon("yellow")

    def _handle_frame_size(self, width, height):
        msg = f"[INFO] Camera frame size: width={width}, height={height}"
        self.lower_frame.log_ai_system(msg)

        self.frame_center_x = width // 2
        self.frame_center_y = (height // 2)+20
        self.pid_tracker = TargetPID(center_x=self.frame_center_x, center_y=self.frame_center_y)
        self.lower_frame.log_completed(f"[PID] PID targeting initialized")

    def _handle_slider_jogging_enable_changed(self, state):
        self.slider_jogging_enabled = state

    def _handle_jogging_command(self ,axis: str , value: int):
        if self.slider_jogging_enabled :
            match axis:
                case "Pan":
                    slider_pan_value_mapped= (value / 100) * self.max_rpm * -1 # multiplied with -1 to make the slider movement aligned with real movement
                    if abs(slider_pan_value_mapped) < abs(self.min_rpm):
                        self.pan_cmd = 0.0
                    else:
                        self.pan_cmd = slider_pan_value_mapped
                case "Tilt":
                    slider_tilt_value_mapped= (value / 100) * self.max_rpm * -1 # multiplied with -1 to make the slider movement aligned with real movement
                    if abs(slider_tilt_value_mapped) < abs(self.min_rpm):
                        self.tilt_cmd = 0.0
                    else:
                        self.tilt_cmd = slider_tilt_value_mapped

    def _handle_auto_aim_changed(self, state):
        self.enable_aim = bool(state)
        self.lower_frame.log_completed(f"[Aiming] Auto Aim enabled")
        if state:
            self.upper_frame.mission_info_labels["Auto Aim            "].setText('<span style="color:green;">Activated</span>')
        else:
            self.upper_frame.mission_info_labels["Auto Aim            "].setText('<span style="color:red;">Not-activated</span>')

    def _handle_auto_shoot_changed(self, state):
        self.enable_shoot = bool(state)
        self.lower_frame.log_completed(f"[Aiming] Auto Shoot enabled")
        if state:
            self.upper_frame.mission_info_labels["Auto Shoot          "].setText('<span style="color:green;">Activated</span>')
        else:
            self.upper_frame.mission_info_labels["Auto Shoot          "].setText('<span style="color:red;">Not-activated</span>')
    
    def _handle_pid_value_changed(self, axis: str, pid_name: str, value: float):
        """
        Handle PID value changes coming from upper_frame.
        axis: 'pan' or 'tilt'
        pid_name: 'P', 'I', or 'D'
        value: float
        """
        try:
            if axis == "Pan":
                if pid_name == "P":
                    self.kp_pan = value
                elif pid_name == "I":
                    self.ki_pan = value
                elif pid_name == "D":
                    self.kd_pan = value
            elif axis == "Tilt":
                if pid_name == "P":
                    self.kp_tilt = value
                elif pid_name == "I":
                    self.ki_tilt = value
                elif pid_name == "D":
                    self.kd_tilt = value
            else:
                self.lower_frame.log_error(f"[PID] Unknown axis: {axis}")
                return

            self.lower_frame.log_completed(f"[PID] {axis} {pid_name} updated to {value}")

        except Exception as e:
            self.lower_frame.log_error(f"[PID] Error updating PID: {e}")

    def _handle_aim_param_changed(self, param: str, new_val: float):
        """
        Handle changes to aiming parameters.
        param: 'min_rpm', 'max_rpm', 'shoot_region_radius'
        new_val: float
        """
        try:
            if param == "Min RPM":
                self.min_rpm = new_val
            elif param == "Max RPM":
                self.max_rpm = new_val
            elif param == "Aim Radius":
                self.shoot_region_radius = new_val
            else:
                self.lower_frame.log_error(f"[Aiming] Unknown parameter: {param}")
                return

            msg = f"[Aiming] {param} updated to {new_val}"
            self.lower_frame.log_completed(msg)
            

        except Exception as e:
            self.lower_frame.log_error(f"[Aiming] Error updating parameter {param}: {e}")

    def _handle_new_balloon_position(self, cx: int, cy: int):
        self.cx = cx
        self.cy = cy
        self.enable_pid = True

        # Restart the detection timeout timer
        self.detection_timer.start()

    def _handle_detection_timeout(self):
        # Detection lost for too long
        self.enable_pid = False
        self.lower_frame.log_ai_system("[System] Balloon tracking lost - PID disabled")

    def _handle_new_balloon_counts(self, red: int, blue: int):
        if self.system_enabled and (self.mission_name is not None and self.mission_name != "Select mission"):
            self.frendlies_number = blue
            self.enemies_number = red
            self.upper_frame.mission_info_labels["Detected Friendlies "].setText(f'<span style="color:green;">{self.frendlies_number}</span>')
            self.upper_frame.mission_info_labels["Detected Enemies    "].setText(f'<span style="color:green;">{self.enemies_number}</span>')

    def _send_command(self):
        """
        This method is called periodically by the command timer.
        """
        if self.mcu_connection_status :
            self.set_system_status_icon("green")

            if self.mission_name == "Manual mode":
                    # Jogging commands
                    if not self.slider_jogging_enabled:

                        pot_pan_value_mapped= (self.pot_pan / 100) * self.max_rpm * -1  # Invert direction for pan
                        if abs(pot_pan_value_mapped) < abs((self.min_rpm+ 1.5)):
                            self.pan_cmd = 0.0
                        else:
                            self.pan_cmd = pot_pan_value_mapped

                        pot_tilt_value_mapped= (self.pot_tilt / 100) * self.max_rpm * -1  # Invert direction for tilt
                        if abs(pot_tilt_value_mapped) < abs((self.min_rpm+ 1.5)):
                            self.tilt_cmd = 0.0
                        else:
                            self.tilt_cmd = pot_tilt_value_mapped

                    # Shoot command 
                    if self.shoot_gui == False:
                        self.shoot_laser1 = self.laser_blue_btn
                        self.shoot_laser2 = self.laser_green_btn
                        self.shoot_laser3 = self.laser_green_btn # CHECK
                        self.shoot_buzzer = self.shoot_laser1 or self.shoot_laser2 or self.shoot_laser3
                        self.shoot = self.shoot_laser1 or self.shoot_laser2 or self.shoot_laser3
                        if self.shoot != self.previous_shoot:
                            self.lower_frame.log_update(f"[Control station] shoot laser is being pressed")
                        self.last_shoot = self.shoot

            elif self.mission_name in ["Mission 1", "Mission 2", "Mission 3"] and self.system_enabled:
                # Chech if pid_tracker is initialized
                # This is to ensure that the pid_tracker is initialized with the frame center
                if not hasattr(self, "pid_tracker"):
                    self.lower_frame.log_error("[PID] PID targeting not initialized with frame center yet, start the mission first.")
                    return
                
                # movement commands
                self.pan_cmd, self.tilt_cmd, self.shoot, erMsg = self.pid_tracker.update(
                    cx=self.cx,
                    cy=self.cy,
                    enable_pid= self.enable_pid,
                    enable_aim=self.enable_aim,
                    enable_shoot=self.enable_shoot,
                    kp_pan=self.kp_pan, ki_pan=self.ki_pan, kd_pan=self.kd_pan,
                    kp_tilt=self.kp_tilt, ki_tilt=self.ki_tilt, kd_tilt=self.kd_tilt,
                    min_rpm=self.min_rpm,
                    max_rpm=self.max_rpm,
                    shoot_region_radius=self.shoot_region_radius
                )
                if erMsg:
                    self.lower_frame.log_error(erMsg)
                    return
                
                # shooting commands
                match self.mission_name:
                    case "Mission 1":
                        # All shoot cmds will take boolean value of laser green or blue button
                        self.shoot = self.shoot_laser1 = self.shoot_laser2 = self.shoot_laser3 = self.shoot_buzzer = (self.laser_blue_btn or self.laser_green_btn)
                        if self.shoot != self.previous_shoot:
                            self.lower_frame.log_update(f"[Control station] shoot laser is being pressed")
                        self.last_shoot = self.shoot

                    case "Mission 2":
                        # All shoot cmds will take boolean value of PID system shoot command
                        self.shoot_laser1 = self.shoot_laser2 = self.shoot_laser3 = self.shoot_buzzer = self.shoot

                    case "Mission 3":
                        # Mission 3 is not implemented yet
                        pass

            # filter comands before sending
            if self.mission_name != "Manual mode":
                if not self.enable_aim:
                    self.pan_cmd , self.tilt_cmd = 0.0, 0.0
                if not self.enable_shoot:
                    self.shoot_laser1, self.shoot_laser2, self.shoot_laser3, self.shoot_buzzer = False, False, False, False
                    self.shoot = False

            # Send commands to MCU
            self.mcu_communication.send_command(
                system_enabled= (self.system_enabled or self.mission_name == "Manual mode"),
                pan_speed_rpm= self.pan_cmd,
                pan_min_angle=0.0,
                pan_max_angle=0.0,
                tilt_speed_rpm= self.tilt_cmd,
                tilt_min_angle=0.0,
                tilt_max_angle=0.0,
                laser_focus_angle=0.0,
                laser1_on= self.shoot_laser1,
                laser2_on= self.shoot_laser2,
                laser3_on= True,
                pan_motor_on= True,
                tilt_motor_on= True,
                buzzer_on= self.shoot_buzzer
            )
            # Update the middle frame with the current commands
            self.middle_frame.Tilt_command.setText(f'<span style="color:blue;">{self.tilt_cmd:.2f} rpm</span>')
            self.middle_frame.Pan_command.setText(f'<span style="color:blue;">{self.pan_cmd:.2f} rpm</span>')
            if self.shoot_gui == False:
                if self.shoot :
                    self.middle_frame.Laser_status.setText('<span style="color:green;">ON</span>')
                else:
                    self.middle_frame.Laser_status.setText('<span style="color:red;">OFF</span>')
            
                
        else:
            self.set_system_status_icon("yellow")
            self.lower_frame.log_update("[Command processor] Check connection of MCU")
            if self.command_timer.isActive():
                self.lower_frame.log_completed("[Command processor] stopped its timer")
            self.command_timer.stop()
            self.middle_frame.Tilt_command.setText('')
            self.middle_frame.Pan_command.setText('')

    # def _send_command(self):
    #     # Chech if pid_tracker is initialized
    #     if not hasattr(self, "pid_tracker"):
    #         self.lower_frame.log_error("[PID] PID targeting not initialized with frame center yet.")
    #         return
        
    #     try:
    #         if self.mcu_connection_status :
    #             self.set_system_status_icon("green")

    #             if self.mission_name in ["Mission 1", "Mission 2", "Mission 3"]:
    #                 self.pan_cmd, self.tilt_cmd, self.shoot, erMsg = self.pid_tracker.update(
    #                     cx=self.cx,
    #                     cy=self.cy,
    #                     enable_pid= self.enable_pid,
    #                     enable_aim=self.enable_aim,
    #                     enable_shoot=self.enable_shoot,
    #                     kp_pan=self.kp_pan, ki_pan=self.ki_pan, kd_pan=self.kd_pan,
    #                     kp_tilt=self.kp_tilt, ki_tilt=self.ki_tilt, kd_tilt=self.kd_tilt,
    #                     min_rpm=self.min_rpm,
    #                     max_rpm=self.max_rpm,
    #                     shoot_region_radius=self.shoot_region_radius
    #                 )
    #                 if erMsg:
    #                     self.lower_frame.log_error(erMsg)
    #                     return
                
    #             match self.mission_name:
    #                 case "Manual mode":
    #                     # Jogging commands
    #                     if not self.slider_jogging_enabled:

    #                         pot_pan_value_mapped= (self.pot_pan / 100) * self.max_rpm * -1  # Invert direction for pan
    #                         if abs(pot_pan_value_mapped) < abs((self.min_rpm+ 1.5)):
    #                             self.pan_cmd = 0.0
    #                         else:
    #                             self.pan_cmd = pot_pan_value_mapped

    #                         pot_tilt_value_mapped= (self.pot_tilt / 100) * self.max_rpm * -1  # Invert direction for tilt
    #                         if abs(pot_tilt_value_mapped) < abs((self.min_rpm+ 1.5)):
    #                             self.tilt_cmd = 0.0
    #                         else:
    #                             self.tilt_cmd = pot_tilt_value_mapped

    #                     # Shoot command 
    #                     if self.shoot_gui == False:
    #                         self.shoot_laser1 = self.laser_blue_btn
    #                         self.shoot_laser2 = self.laser_green_btn
    #                         self.shoot_laser3 = self.laser_green_btn # CHECK
    #                         self.shoot_buzzer = self.shoot_laser1 or self.shoot_laser2 or self.shoot_laser3
    #                         self.shoot = self.shoot_laser1 or self.shoot_laser2 or self.shoot_laser3
    #                         if self.shoot != self.previous_shoot:
    #                             self.lower_frame.log_update(f"[Control station] shoot laser is being pressed")
    #                         self.last_shoot = self.shoot
                                

    #                 case "Mission 1":
    #                     # All shoot cmds will take boolean value of laser green or blue button
    #                     self.shoot = self.shoot_laser1 = self.shoot_laser2 = self.shoot_laser3 = self.shoot_buzzer = (self.laser_blue_btn or self.laser_green_btn)
    #                     if self.shoot != self.previous_shoot:
    #                         self.lower_frame.log_update(f"[Control station] shoot laser is being pressed")
    #                     self.last_shoot = self.shoot


    #                 case "Mission 2":
    #                     # All shoot cmds will take boolean value of self.shoot
    #                     self.shoot_laser1 = self.shoot_laser2 = self.shoot_laser3 = self.shoot_buzzer = self.shoot




    #             # Send commands to MCU
    #             self.mcu_communication.send_command(
    #                 system_enabled= self.system_enabled,
    #                 pan_speed_rpm= self.pan_cmd,
    #                 pan_min_angle=0.0,
    #                 pan_max_angle=0.0,
    #                 tilt_speed_rpm= self.tilt_cmd,
    #                 tilt_min_angle=0.0,
    #                 tilt_max_angle=0.0,
    #                 laser_focus_angle=0.0,
    #                 laser1_on= self.shoot_laser1,
    #                 laser2_on= self.shoot_laser2,
    #                 laser3_on= True,
    #                 pan_motor_on= True,
    #                 tilt_motor_on= True,
    #                 buzzer_on= self.shoot_buzzer
    #             )

    #             self.middle_frame.Tilt_command.setText(f'<span style="color:blue;">{self.tilt_cmd:.2f} rpm</span>')
    #             self.middle_frame.Pan_command.setText(f'<span style="color:blue;">{self.pan_cmd:.2f} rpm</span>')
                    
    #             if self.shoot_gui == False:
    #                 if self.shoot :
    #                     self.middle_frame.Laser_status.setText('<span style="color:green;">ON</span>')
    #                 else:
    #                     self.middle_frame.Laser_status.setText('<span style="color:red;">OFF</span>')


    #             # Disable PID until new update comes from AI
    #             #self.enable_pid = False

    #         else:
    #            self.lower_frame.log_update("[Command processor] Check connection of MCU")
    #            self.set_system_status_icon("yellow")
    #            if self.command_timer.isActive():
    #             self.lower_frame.log_completed("[Command processor] stopped its timer")
    #             self.command_timer.stop()
    #             self.middle_frame.Tilt_command.setText('')
    #             self.middle_frame.Pan_command.setText('')


    #     except Exception as e:
    #         self.lower_frame.log_error(f"[PID] Error in periodic command sender: {e}")

    def _handle_starting_mission(self ,mission_name=None , cam_index= 0):
        if not self.system_enabled:
            try:
                # Put the ai widget in the recognition layout and disconnect the camera if it was used before by the normal camera widget
                if self.upper_frame.Recognition_layout.currentWidget() == self.upper_frame.camera_widget:
                    self.upper_frame.camera_widget.disconnect_camera()
                self.upper_frame.Recognition_layout.setCurrentWidget(self.upper_frame.ai_widget)
                
                # Set the the camera port used by the AI system
                if self.camera_port is not None:
                    cam_index = int(self.camera_port)
                    msg= f"[INFO] Camera index used: {cam_index}"
                    self.lower_frame.log_ai_system(msg)   
                else:
                    msg = "[Warning] No camera port set, using default camera index 0"
                    self.lower_frame.log_ai_system(msg)
                    
                # Select the mission to be started
                mission_name = self.mission_name
                if mission_name == "Select mission" or mission_name is None:
                    msg = "[Warning] No mission selected, please select a mission"
                    self.lower_frame.log_ai_system(msg)
                    return
                
                elif mission_name == "Manual mode":
                    self.system_enabled ,self.enable_aim ,self.enable_shoot  = True , False, False
                    self.set_system_status_icon("green")
                    msg = "[INFO] Starting manual mode"
                    self.lower_frame.log_ai_system(msg)
                    self.upper_frame.start_ai(cam_index=cam_index)

                elif mission_name == "Mission 1":
                    self.system_enabled ,self.enable_aim ,self.enable_shoot  = True , True, False
                    self.set_system_status_icon("green")
                    msg = "[INFO] Starting Mission 1"
                    self.lower_frame.log_ai_system(msg)
                    self.upper_frame.start_ai(cam_index=cam_index)

                elif mission_name == "Mission 2":
                    self.system_enabled ,self.enable_aim ,self.enable_shoot  = True , True, True
                    self.set_system_status_icon("green")
                    msg = "[INFO] Starting Mission 2"
                    self.lower_frame.log_ai_system(msg)
                    self.upper_frame.start_ai(cam_index=cam_index)

                # Update auto aim and shoot status
                self._handle_auto_shoot_changed(self.enable_shoot)
                self._handle_auto_aim_changed(self.enable_aim)

                # Start the timer responsible for sending commands if not already activated
                if not self.command_timer.isActive():
                    self.lower_frame.log_completed(f"[Command processor] started its timer with {self.command_freq}ms sending rate")
                    self.command_timer.start()
                
            except Exception as e:
                self.lower_frame.log_error(f"[Error] while starting mission: {e}")
        else:
            msg = "[INFO] System already started"
            self.lower_frame.log_ai_system(msg)
            
    def _handle_stopping_mission(self):
        if self.system_enabled:
            try:
                self.system_enabled , self.enable_aim , self.enable_shoot = False, False, False
                self.lower_frame.log_completed("[System] Stopping mission")
                self.upper_frame.stop_ai()
                #self.mcu_communication.disconnect_mcu()
                self.set_system_status_icon("red")
                # Update auto aim and shoot status
                self._handle_auto_shoot_changed(self.enable_shoot)
                self._handle_auto_aim_changed(self.enable_aim)

                # Stop the timer responsible for sending commands if activated
                if self.command_timer.isActive():
                    self.command_timer.stop()
                    self.lower_frame.log_completed(f"[Command processor] stopped its timer")
                
            except Exception as e:
                self.lower_frame.log_error(f"[Error] while stopping mission: {e}")
        else:
            msg = "[INFO] System already stopped"
            self.lower_frame.log_ai_system(msg)
            
    def _handle_shoot_toggled(self, checked: bool):
        if self.system_enabled and (self.mission_name == "Manual mode" or self.mission_name == "Mission 1"):
            if checked:
                # ON
                self.shoot = self.shoot_laser1 = self.shoot_laser2 = self.shoot_laser3 = self.shoot_buzzer = self.shoot_gui = True
                self.middle_frame.Laser_status.setText('<span style="color:green;">ON</span>')

            else:
                # OFF
                self.shoot = self.shoot_laser1 = self.shoot_laser2 = self.shoot_laser3 = self.shoot_buzzer = self.shoot_gui = False
                self.middle_frame.Laser_status.setText('<span style="color:red;">OFF</span>')

    def set_system_status_icon(self, color_name):
        icon_map = {
            "green": "green_icon.png",
            "yellow": "yellow_icon.png",
            "red": "red_icon.png"
        }
        icon_file = icon_map.get(color_name.lower())
        img_path = os.path.join(assets_path, icon_file)
        self.middle_frame.system_status_icon.setPixmap(QtGui.QPixmap(img_path))