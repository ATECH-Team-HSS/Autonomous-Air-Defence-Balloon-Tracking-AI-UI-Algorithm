# import json
# import serial
# #import serial.tools.list_ports
# from PyQt5.QtCore import QObject, pyqtSignal, QTimer

# class McuCommunication(QObject):
#     # ───── Signals ─────
#     connection_status = pyqtSignal(bool)       # True if connected, False if disconnected
#     error_happened = pyqtSignal(str)           # emits error text
#     update_happened = pyqtSignal(str)          # emits log/update text
#     update_completed = pyqtSignal(str)       # emits completion text
#     data_received = pyqtSignal(dict)           # emits parsed JSON from MCU
    

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.ser = None
#         self.timer = QTimer(self)
#         self.timer.timeout.connect(self._read_from_mcu)
#         self.x = 0

#     # ───── Connect to port ─────
#     def connect_mcu(self, port: int, baudrate:  int = 115200):
#         try:
#             self.ser = serial.Serial("COM" + str(port), baudrate=baudrate, timeout=1)
#             if self.ser.is_open:
#                 self.connection_status.emit(True)
#                 self.update_completed.emit(f"[MCU] Successfully connected on COM{port} @ {baudrate} baud")
#                 print(f"[MCU] Successfully connected on COM{port} @ {baudrate} baud")
#                 self.timer.start(300)  # poll every 300 ms
#         except Exception as e:
#             erMsg = f"[MCU] Error opening COM{port}"
#             print(erMsg + f" , Error(connect_mcu): {e}")
#             self.ser = None
#             self.connection_status.emit(False)
#             self.error_happened.emit(erMsg)

#     # ───── Disconnect from port ─────
#     def disconnect_mcu(self):
#         try:
#             self.timer.stop()
#             if self.ser and self.ser.is_open:
#                 self.ser.close()
#                 self.update_completed.emit("[MCU] Successfully disconnected")
#                 print("[MCU] Successfully disconnected")
#             self.ser = None
#             self.connection_status.emit(False)
#         except Exception as e:
#             erMsg = "[MCU] Error disconnecting"
#             print(erMsg + f" , Error(disconnect_mcu): {e}")
#             self.error_happened.emit(erMsg)

#     # ───── Send a JSON command ─────
#     def send_command(self,
#                      system_enabled: bool,
#                      pan_speed_rpm: float, pan_min_angle: float, pan_max_angle: float,
#                      tilt_speed_rpm: float, tilt_min_angle: float, tilt_max_angle: float,
#                      laser_focus_angle: float,
#                      laser1_on: bool, laser2_on: bool, laser3_on: bool,
#                      pan_motor_on: bool, tilt_motor_on: bool, buzzer_on: bool):
#         if not self.ser or not self.ser.is_open:
#             erMsg = "[MCU] Not connected. Cannot send command."
#             print(erMsg)
#             self.error_happened.emit(erMsg)
#             return

#         try:
#             payload = {
#                 "type": "command",
#                 "system_enabled": system_enabled,
#                 "motion": {
#                     "pan_speed_rpm": pan_speed_rpm,
#                     "pan_min_angle": pan_min_angle,
#                     "pan_max_angle": pan_max_angle,
#                     "tilt_speed_rpm": tilt_speed_rpm,
#                     "tilt_min_angle": tilt_min_angle,
#                     "tilt_max_angle": tilt_max_angle,
#                     "laser_focus_angle": laser_focus_angle
#                 },
#                 "actuator": {
#                     "laser1_on": laser1_on,
#                     "laser2_on": laser2_on,
#                     "laser3_on": laser3_on,
#                     "pan_motor_on": pan_motor_on,
#                     "tilt_motor_on": tilt_motor_on,
#                     "buzzer_on": buzzer_on
#                 }
#             }
#             json_str = json.dumps(payload)
#             self.ser.write((json_str + "\n").encode("utf-8"))
#             #self.update_happened.emit("[MCU] Command sent")

#             print(f"[TX] {json_str}")
#         except Exception as e:
#             erMsg = f"[MCU] Error sending command: {e}"
#             print(erMsg)
#             self.error_happened.emit(erMsg)
#             self.disconnect_mcu()


#     # ───── Read incoming data ─────
#     def _read_from_mcu(self):
#         if not self.ser or not self.ser.is_open:
#             return
#         try:
#             line = self.ser.readline().decode("utf-8").strip()
#             if line:
#                 try:
#                     data = json.loads(line)
#                     self.data_received.emit(data)
#                     print(f"[RX] {data}")
#                     self.x += 1
#                     self.update_happened.emit(f"[MCU] RX recieved: {self.x} msg")

#                 except json.JSONDecodeError:
#                     # self.error_happened.emit(f"[MCU] ⚠️ Invalid JSON: {line}")
#                     # self.update_happened.emit(f"[MCU] If Invalid JSON keeps happening , check Code on MCU , ignore this error if it stops")
#                     print(f"[MCU] ⚠️ Invalid JSON: {line}")
#         except Exception as e:
#             self.error_happened.emit(f"[MCU] Error reading: {e}")
#             self.update_happened.emit("[MCU] Disconnecting due to error")
#             self.disconnect_mcu()


# import json
# import serial
# from PyQt5.QtCore import QObject, pyqtSignal, QTimer

# class McuCommunication(QObject):
#     # ───── Signals ─────
#     connection_status = pyqtSignal(bool)       # True if connected, False if disconnected
#     error_happened = pyqtSignal(str)
#     update_happened = pyqtSignal(str)
#     update_completed = pyqtSignal(str)
#     data_received = pyqtSignal(dict)

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         # Two separate serial connections
#         self.ser_turret = None   # for sending
#         self.ser_station = None   # for receiving

#         # Two separate timers
#         self.timer_turret = QTimer(self)
#         self.timer_station = QTimer(self)

#         self.timer_turret.timeout.connect(self._read_from_mcu_turret) # just for debugging
#         self.timer_station.timeout.connect(self._read_from_mcu_station)

#     # ──────────────────────────────────────
#     # MCU1 (turret) Connect / Disconnect
#     # ──────────────────────────────────────
#     def connect_mcu_turret(self, port: int, baudrate: int = 115200):
#         try:
#             self.ser_turret = serial.Serial("COM" + str(port), baudrate=baudrate, timeout=1)
#             if self.ser_turret.is_open:
#                 self.connection_status.emit(True)
#                 self.update_completed.emit(f"[MCU-turret] Connected on COM{port} @ {baudrate}")
#                 print(f"[MCU-turret] Connected on COM{port} @ {baudrate}")
#                 self.timer_turret.start(300)
#         except Exception as e:
#             erMsg = f"[MCU-turret] Error opening COM{port}: {e}"
#             print(erMsg)
#             self.ser_turret = None
#             self.connection_status.emit(False)
#             self.error_happened.emit(erMsg)

#     def disconnect_mcu_turret(self):
#         try:
#             self.timer_turret.stop()
#             if self.ser_turret and self.ser_turret.is_open:
#                 self.ser_turret.close()
#                 self.update_completed.emit("[MCU-turret] Disconnected")
#                 print("[MCU-turret] Disconnected")
#             self.ser_turret = None
#             self.connection_status.emit(False)
#         except Exception as e:
#             erMsg = f"[MCU-turret] Error disconnecting: {e}"
#             print(erMsg)
#             self.error_happened.emit(erMsg)

#     # ──────────────────────────────────────
#     # MCU2 (station) Connect / Disconnect
#     # ──────────────────────────────────────
#     def connect_mcu_station(self, port: int, baudrate: int = 115200):
#         try:
#             self.ser_station = serial.Serial("COM" + str(port), baudrate=baudrate, timeout=1)
#             if self.ser_station.is_open:
#                 self.connection_status.emit(True)
#                 self.update_completed.emit(f"[MCU-station] Connected on COM{port} @ {baudrate}")
#                 print(f"[MCU-station] Connected on COM{port} @ {baudrate}")
#                 self.timer_station.start(300)
#         except Exception as e:
#             erMsg = f"[MCU-station] Error opening COM{port}: {e}"
#             print(erMsg)
#             self.ser_station = None
#             self.connection_status.emit(False)
#             self.error_happened.emit(erMsg)

#     def disconnect_mcu_station(self):
#         try:
#             self.timer_station.stop()
#             if self.ser_station and self.ser_station.is_open:
#                 self.ser_station.close()
#                 self.update_completed.emit("[MCU-station] Disconnected")
#                 print("[MCU-station] Disconnected")
#             self.ser_station = None
#             self.connection_status.emit(False)
#         except Exception as e:
#             erMsg = f"[MCU-station] Error disconnecting: {e}"
#             print(erMsg)
#             self.error_happened.emit(erMsg)

#     # ──────────────────────────────────────
#     # Send command (turret)
#     # ──────────────────────────────────────
#     def send_command(self,
#                      system_enabled: bool,
#                      pan_speed_rpm: float, pan_min_angle: float, pan_max_angle: float,
#                      tilt_speed_rpm: float, tilt_min_angle: float, tilt_max_angle: float,
#                      laser_focus_angle: float,
#                      laser1_on: bool, laser2_on: bool, laser3_on: bool,
#                      pan_motor_on: bool, tilt_motor_on: bool, buzzer_on: bool):
#         if not self.ser_turret or not self.ser_turret.is_open:
#             erMsg = "[MCU-turret] Not connected. Cannot send command."
#             print(erMsg)
#             self.error_happened.emit(erMsg)
#             return
#         try:
#             payload = {
#                 "type": "command",
#                 "system_enabled": system_enabled,
#                 "motion": {
#                     "pan_speed_rpm": pan_speed_rpm,
#                     "pan_min_angle": pan_min_angle,
#                     "pan_max_angle": pan_max_angle,
#                     "tilt_speed_rpm": tilt_speed_rpm,
#                     "tilt_min_angle": tilt_min_angle,
#                     "tilt_max_angle": tilt_max_angle,
#                     "laser_focus_angle": laser_focus_angle
#                 },
#                 "actuator": {
#                     "laser1_on": laser1_on,
#                     "laser2_on": laser2_on,
#                     "laser3_on": laser3_on,
#                     "pan_motor_on": pan_motor_on,
#                     "tilt_motor_on": tilt_motor_on,
#                     "buzzer_on": buzzer_on
#                 }
#             }
#             json_str = json.dumps(payload)
#             self.ser_turret.write((json_str + "\n").encode("utf-8"))
#             print(f"[turret] {json_str}")
#         except Exception as e:
#             erMsg = f"[MCU-turret] Error sending command: {e}"
#             print(erMsg)
#             self.error_happened.emit(erMsg)
#             # self.disconnect_mcu_turret()

#     # ──────────────────────────────────────
#     # Read incoming data from station MCU
#     # ──────────────────────────────────────
#     def _read_from_mcu_station(self):
#         if not self.ser_station or not self.ser_station.is_open:
#             return
#         try:
#             line = self.ser_station.readline().decode("utf-8").strip()
#             if line:
#                 try:
#                     data = json.loads(line)
#                     self.data_received.emit(data)
#                     print(f"[station] {data}")
#                 except json.JSONDecodeError:
#                     print(f"[MCU-station] ⚠️ Invalid JSON: {line}")
#         except Exception as e:
#             self.error_happened.emit(f"[MCU-station] Error reading: {e}")
#             # self.update_happened.emit("[MCU-station] Disconnecting due to error")
#             # self.disconnect_mcu_station()

#     # Dummy read for turret (not used for status)
#     def _read_from_mcu_turret(self):
#         # If you want to monitor echo or debug responses from turret device, implement here
#         pass

import json
import serial
import threading
from PyQt5.QtCore import QObject, pyqtSignal


class McuCommunication(QObject):
    # ───── Signals ─────
    connection_status = pyqtSignal(bool)       # True if connected, False if disconnected
    error_happened = pyqtSignal(str)
    update_happened = pyqtSignal(str)
    update_completed = pyqtSignal(str)
    data_received = pyqtSignal(dict)

    def _init_(self, parent=None):
        super()._init_(parent)
        # Serial interfaces
        self.ser_turret = None
        self.ser_station = None

        # Thread controls
        self.station_thread = None
        self.station_running = False

        self.turret_thread = None
        self.turret_running = False

    # ──────────────────────────────────────
    # MCU1 (turret) Connect / Disconnect
    # ──────────────────────────────────────
    def connect_mcu_turret(self, port: int, baudrate: int = 115200):
        try:
            self.ser_turret = serial.Serial(f"COM{port}", baudrate=baudrate, timeout=1)
            if self.ser_turret.is_open:
                self.connection_status.emit(True)
                self.update_completed.emit(f"[MCU-turret] Connected on COM{port} @ {baudrate}")
                print(f"[MCU-turret] Connected on COM{port} @ {baudrate}")
                self.turret_running = True
                self.turret_thread = threading.Thread(target=self._read_turret_loop, daemon=True)
                self.turret_thread.start()
        except Exception as e:
            erMsg = f"[MCU-turret] Error opening COM{port}: {e}"
            print(erMsg)
            self.ser_turret = None
            self.connection_status.emit(False)
            self.error_happened.emit(erMsg)

    def disconnect_mcu_turret(self):
        try:
            self.turret_running = False
            if self.turret_thread:
                self.turret_thread.join(timeout=1)
                self.turret_thread = None
            if self.ser_turret and self.ser_turret.is_open:
                self.ser_turret.close()
                self.update_completed.emit("[MCU-turret] Disconnected")
                print("[MCU-turret] Disconnected")
            self.ser_turret = None
            self.connection_status.emit(False)
        except Exception as e:
            erMsg = f"[MCU-turret] Error disconnecting: {e}"
            print(erMsg)
            self.error_happened.emit(erMsg)

    # ──────────────────────────────────────
    # MCU2 (station) Connect / Disconnect
    # ──────────────────────────────────────
    def connect_mcu_station(self, port: int, baudrate: int = 115200):
        try:
            self.ser_station = serial.Serial(f"COM{port}", baudrate=baudrate, timeout=1)
            if self.ser_station.is_open:
                self.connection_status.emit(True)
                self.update_completed.emit(f"[MCU-station] Connected on COM{port} @ {baudrate}")
                print(f"[MCU-station] Connected on COM{port} @ {baudrate}")
                self.station_running = True
                self.station_thread = threading.Thread(target=self._read_station_loop, daemon=True)
                self.station_thread.start()
        except Exception as e:
            erMsg = f"[MCU-station] Error opening COM{port}: {e}"
            print(erMsg)
            self.ser_station = None
            self.connection_status.emit(False)
            self.error_happened.emit(erMsg)

    def disconnect_mcu_station(self):
        try:
            self.station_running = False
            if self.station_thread:
                self.station_thread.join(timeout=1)
                self.station_thread = None
            if self.ser_station and self.ser_station.is_open:
                self.ser_station.close()
                self.update_completed.emit("[MCU-station] Disconnected")
                print("[MCU-station] Disconnected")
            self.ser_station = None
            self.connection_status.emit(False)
        except Exception as e:
            erMsg = f"[MCU-station] Error disconnecting: {e}"
            print(erMsg)
            self.error_happened.emit(erMsg)

    # ──────────────────────────────────────
    # Send command (turret)
    # ──────────────────────────────────────
    def send_command(self,
                     system_enabled: bool,
                     pan_speed_rpm: float, pan_min_angle: float, pan_max_angle: float,
                     tilt_speed_rpm: float, tilt_min_angle: float, tilt_max_angle: float,
                     laser_focus_angle: float,
                     laser1_on: bool, laser2_on: bool, laser3_on: bool,
                     pan_motor_on: bool, tilt_motor_on: bool, buzzer_on: bool):
        if not self.ser_turret or not self.ser_turret.is_open:
            erMsg = "[MCU-turret] Not connected. Cannot send command."
            print(erMsg)
            self.error_happened.emit(erMsg)
            return
        try:
            payload = {
                "type": "command",
                "system_enabled": system_enabled,
                "motion": {
                    "pan_speed_rpm": pan_speed_rpm,
                    "pan_min_angle": pan_min_angle,
                    "pan_max_angle": pan_max_angle,
                    "tilt_speed_rpm": tilt_speed_rpm,
                    "tilt_min_angle": tilt_min_angle,
                    "tilt_max_angle": tilt_max_angle,
                    "laser_focus_angle": laser_focus_angle
                },
                "actuator": {
                    "laser1_on": laser1_on,
                    "laser2_on": laser2_on,
                    "laser3_on": laser3_on,
                    "pan_motor_on": pan_motor_on,
                    "tilt_motor_on": tilt_motor_on,
                    "buzzer_on": buzzer_on
                }
            }
            json_str = json.dumps(payload)
            self.ser_turret.write((json_str + "\n").encode("utf-8"))
            print(f"[turret] {json_str}")
        except Exception as e:
            erMsg = f"[MCU-turret] Error sending command: {e}"
            print(erMsg)
            self.error_happened.emit(erMsg)

    # ──────────────────────────────────────
    # Station thread loop
    # ──────────────────────────────────────
    def _read_station_loop(self):
        while self.station_running and self.ser_station and self.ser_station.is_open:
            try:
                line = self.ser_station.readline().decode("utf-8").strip()
                if line:
                    try:
                        data = json.loads(line)
                        self.data_received.emit(data)
                        #print(f"[station] {data}")
                    except json.JSONDecodeError:
                        print(f"[MCU-station] ⚠ Invalid JSON: {line}")
            except Exception as e:
                self.error_happened.emit(f"[MCU-station] Error reading: {e}")
                break

    # ──────────────────────────────────────
    # Turret thread loop (debugging only)
    # ──────────────────────────────────────
    def _read_turret_loop(self):
        pass
        # while self.turret_running and self.ser_turret and self.ser_turret.is_open:
        #     try:
        #         line = self.ser_turret.readline().decode("utf-8").strip()
        #         if line:
        #             print(f"[turret-debug] {line}")
        #     except Exception as e:
        #         print(f"[MCU-turret] Error reading (ignored): {e}")
        #         break