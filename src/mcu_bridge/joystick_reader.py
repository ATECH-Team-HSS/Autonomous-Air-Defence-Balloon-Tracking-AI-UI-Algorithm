import serial
import threading
from PyQt5.QtCore import QObject, pyqtSignal

class JoystickReader(QObject):
    anglesUpdated = pyqtSignal(int, int)  # pan, tilt
    connectionLost = pyqtSignal()

    def __init__(self, port='COM3', baudrate=9600):
        super().__init__()
        self._running = False
        self.ser = None
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            self._running = True
            self.thread = threading.Thread(target=self.read_loop, daemon=True) # Daemon thread will exit when the main program exits
            self.thread.start()
        except serial.SerialException as e:
            print("⚠️ Could not open serial port:", e)


    def read_loop(self):
        while self._running:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if "Pan:" in line and "Tilt:" in line:
                    parts = line.split(',')
                    Pan_raw = int(parts[0].split(':')[1])
                    Tilt_raw = int(parts[1].split(':')[1])
                    # Map 0–1023 to 0–180 degrees
                    Pan_mapped = int((Pan_raw / 1023) * 180)
                    Tilt_mapped = int((Tilt_raw / 1023) * 180)
                    self.anglesUpdated.emit(Pan_mapped, Tilt_mapped)

            except (serial.SerialException, OSError) as e:
                print("🔌 Arduino disconnected or serial error:", e)
                self._running = False  # Stop the loop
                try:
                    self.ser.close()
                except Exception as e:
                    print("Error while closing serial:", e)
                self.connectionLost.emit()
                break  # Exit the thread cleanly

            except Exception as e:
                print("Other error in connection with microcontroller:", e)

    def stop(self):
        self._running = False
        try:
            self.ser.close()  # Close the serial port
        except Exception as e:
            print("Serial port closing error happened:", e)
 