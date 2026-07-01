# PyQt5 Control Station

<p align="center">
  <img alt="PyQt5" src="https://img.shields.io/badge/PyQt5-control%20station-purple">
  <img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-camera%20feed-green">
  <img alt="Serial" src="https://img.shields.io/badge/Serial-JSON%20UART-blue">
  <img alt="PID" src="https://img.shields.io/badge/PID-pan%2Ftilt-orange">
</p>

This document explains the user-interface and control-station side of the project. The UI is a PyQt5 desktop application for camera/AI feedback, mission state, PID tuning, manual jogging, serial communication, command display, and system logging.

> The UI is intended for safe educational robotics prototyping.

---
## Key Features

- PyQt5-based desktop control-station interface.
- Modular GUI layout with upper, middle, and lower frames.
- Camera preview using OpenCV and Qt widgets.
- Integrated AI-detection widget.
- Target-position handling using emitted object center coordinates.
- PID-based pan and tilt command generation.
- Configurable PID values for pan and tilt axes.
- Configurable aiming parameters, including minimum RPM, maximum RPM, and aim radius.
- Manual jogging through GUI sliders.
- Serial communication with MCU devices using JSON messages.
- Separate serial connection handling for a turret MCU and a station MCU.
- Mission selection workflow with Manual Mode, Mission 1, Mission 2, and a placeholder Mission 3.\
- Embedded-side JSON messenger code for exchanging commands and status messages.
---
### Main Modules

| Module | Purpose |
|---|---|
| `src/main_window.py` | Entry point for the PyQt5 application. Builds the main window and connects the main GUI frames. |
| `src/ui/frames/upper_frame.py` | Contains the recognition/camera area, mission information tabs, jogging sliders, PID inputs, aiming controls, and port configuration controls. |
| `src/ui/frames/middle_frame.py` | Contains the main command buttons, mission selector, displayed pan/tilt command values, visual indicator status, and actuator status display. |
| `src/ui/frames/lower_frame.py` | Provides a logging area for system updates, errors, completed actions, and AI-system messages. |
| `src/ui/signals_controller.py` | Central logic controller. Connects GUI signals, handles mission state, receives AI detection events, runs PID control, and sends MCU commands. |
| `src/hardware_manager/camera_communication.py` | Handles OpenCV camera connection, disconnection, and live frame display inside the GUI. |
| `src/hardware_manager/mcu_communication.py` | Handles serial communication with turret and station MCUs using JSON messages. |
| `src/hardware_manager/pid_tracker.py` | Implements the PID tracking logic that converts target image error into pan/tilt speed commands. |
| `src/recognition_system/start_camera.py` | Standalone/simple camera preview widget. |
| `src/mcu_bridge/JsonMessenger.cpp` and `.h` | Embedded-side JSON communication helper for Arduino-compatible firmware. |
| `assets/` | Contains GUI icons and project branding images. |

---

## Technologies Used

- **Python** for the desktop control-station application.
- **PyQt5** for the graphical user interface.
- **OpenCV** for camera capture and frame display.
- **PySerial** for serial communication with microcontrollers.
- **JSON** for structured command and status messages.

---
## UI overview

The main UI entry point is:

```text
src/main_window.py
```

It builds a `QMainWindow` titled **Air Defense ATech** and combines three major frames:

```text
MainWindow
└── Central widget
    └── Vertical layout
        ├── UpperFrame   → camera/AI view, mission tabs, PID controls, ports
        ├── MiddleFrame  → mission buttons, command values, status indicators
        └── LowerFrame   → logs and system messages
```

<p align="center">
  <img src="docs/assets/ui/gui-screen.png" alt="Air Defence PyQt5 GUI screen" width="85%">
</p>

---

## Control-station workflow

```text
Start PyQt5 GUI
      │
      ▼
Configure camera and MCU ports
      │
      ▼
Choose camera-only or AI detection view
      │
      ▼
Select mission mode
      │
      ▼
Receive target center from AI widget
      │
      ▼
Run PID pan/tilt command calculation
      │
      ▼
Send JSON command to turret MCU
      │
      ▼
Display command values, status indicators, and logs
```

<p align="center">
  <img src="docs/assets/ui/ui-control-station.jpg" alt="Air Defence UI control station" width="85%">
</p>

## Upper frame

`UpperFrame` is the operator's main interaction area. It includes:

- Camera preview widget.
- AI detection widget placeholder/integration point.
- Mission information tab.
- Manual jogging sliders for tilt, pan, and laser/focus-related motion.
- PID tuning controls for pan and tilt.
- Aiming parameter controls such as minimum RPM, maximum RPM, and aim radius.
- Camera and MCU port configuration controls.

---

## Middle frame

`MiddleFrame` groups mission and command controls:

- Start button.
- Stop button.
- Shoot toggle/button.
- Mission selector.
- Manual mode / mission mode state.
- Pan command display.
- Tilt command display.
- Actuator/system status indicators.
- Red/yellow/green icon-based status display.

The middle frame is connected to `SignalsMainController`, which interprets user actions and updates mission state.

---

## Lower frame

`LowerFrame` provides operator feedback:

- Error logs.
- Update logs.
- Completion logs.
- AI-system messages.
- MCU communication messages.


---

## PID control workflow

Target feedback from the AI widget is converted into pan/tilt commands using `TargetPID`.

```text
AI target center: (cx, cy)
        │
        ▼
Frame center: (frame_center_x, frame_center_y)
        │
        ▼
Error calculation
        │
        ▼
PID controller
        │
        ▼
Clamp command to min/max RPM
        │
        ▼
Send pan_speed_rpm and tilt_speed_rpm to MCU
```

Configurable values in the UI/control code include:

- `kp_pan`, `ki_pan`, `kd_pan`
- `kp_tilt`, `ki_tilt`, `kd_tilt`
- `min_rpm`
- `max_rpm`
- `shoot_region_radius`
- `enable_aim`
- `enable_shoot`

---

## Serial communication

The UI uses `McuCommunication` to send structured JSON commands over serial.

Command concept:

```json
{
  "type": "command",
  "system_enabled": true,
  "motion": {
    "pan_speed_rpm": 0.0,
    "pan_min_angle": 0.0,
    "pan_max_angle": 0.0,
    "tilt_speed_rpm": 0.0,
    "tilt_min_angle": 0.0,
    "tilt_max_angle": 0.0,
    "laser_focus_angle": 0.0
  },
  "actuator": {
    "laser1_on": false,
    "laser2_on": false,
    "laser3_on": false,
    "pan_motor_on": true,
    "tilt_motor_on": true,
    "buzzer_on": false
  }
}
```

---

## Safety and Ethical Notice

This project is intended strictly for educational, simulation, research, and safe robotics prototyping purposes. It is not intended for real-world weaponization, autonomous targeting, harmful use, or deployment against people, animals, vehicles, or property.
