# PyQt5 Control Station

<p align="center">
  <img alt="PyQt5" src="https://img.shields.io/badge/PyQt5-control%20station-purple">
  <img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-camera%20feed-green">
  <img alt="Serial" src="https://img.shields.io/badge/Serial-JSON%20UART-blue">
  <img alt="PID" src="https://img.shields.io/badge/PID-pan%2Ftilt-orange">
</p>

This document explains the user-interface and control-station side of the project. The UI is a PyQt5 desktop application for camera/AI feedback, mission state, PID tuning, manual jogging, serial communication, command display, and system logging.

> The UI is intended for safe educational robotics prototyping. Do not connect high-power outputs until the AI widget, MCU communication, JSON schema, safety state, and emergency-stop behavior are verified.

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

---

## Main UI modules

| Path | Purpose |
| --- | --- |
| `src/main_window.py` | Main PyQt5 application entry point and frame composition. |
| `src/ui/main_window.ui` | Qt Designer UI file. |
| `src/ui/frames/upper_frame.py` | Camera/AI view, mission tabs, jogging sliders, PID fields, aim parameters, port controls. |
| `src/ui/frames/middle_frame.py` | Start/stop/shoot controls, mission selector, command displays, actuator status icons. |
| `src/ui/frames/lower_frame.py` | System log panel for errors, updates, completed operations, and AI messages. |
| `src/ui/signals_controller.py` | Main GUI logic controller connecting frames, AI signals, PID tracking, and MCU commands. |
| `src/hardware_manager/camera_communication.py` | Camera connection, disconnection, and frame display using OpenCV and Qt. |
| `src/hardware_manager/mcu_communication.py` | Serial communication with turret and station MCUs. |
| `src/hardware_manager/pid_tracker.py` | PID tracking logic for converting target error into pan/tilt speed commands. |
| `src/mcu_bridge/JsonMessenger.cpp` / `.h` | Embedded-side JSON helper for Arduino-compatible firmware. |

---

## Upper frame

`UpperFrame` is the operator's main interaction area. It includes:

- Camera preview widget.
- AI detection widget placeholder/integration point.
- Mission information tab.
- Manual jogging sliders for tilt, pan, and laser/focus-related motion.
- PID tuning controls for pan and tilt.
- Aiming parameter controls such as minimum RPM, maximum RPM, and aim radius.
- Camera and MCU port configuration controls.

Expected AI widget signals used by `SignalsMainController`:

| Signal | Meaning |
| --- | --- |
| `status_message` | Text log from AI subsystem. |
| `AI_detection_running` | Indicates whether AI inference is active. |
| `balloon_position` | Emits target center coordinates. |
| `balloon_counts` | Emits detected friendly/enemy counts. |
| `camera_size` | Emits current frame width/height for PID center calculation. |

> Integration note: the current UI imports `balloon_shooter.ai_detection_widget.AIDetectionWidget`. If this file is missing in your branch, create an adapter around the existing `balloon_shooter` AI runtime and emit the signals above.

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

For robotics demos, this log area is important. It tells the operator what the system is doing instead of hiding state inside the terminal.

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

Before public release, define this as the canonical schema and make sure the Python and embedded C++ sides both parse the same fields.

---

## Run the UI

Install base requirements first:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

Install UI dependencies if they are not already included in your environment:

```bash
python -m pip install PyQt5 pyserial simple-pid
```

Run:

```bash
python src/main_window.py
```

Recommended from repository root, because the current code uses relative asset paths such as `assets/ATech_logo.png`.

---

## Operator checklist

Before connecting real hardware:

1. Run the UI without MCU hardware.
2. Confirm that camera preview works.
3. Confirm that the AI detection widget loads and emits signals.
4. Test PID command values with dummy target coordinates.
5. Send serial commands to a safe dummy receiver first.
6. Verify JSON schema compatibility with firmware.
7. Test emergency stop and manual stop behavior.
8. Use LEDs or safe indicators before any physical output.
9. Enable physical actuation only under direct supervision.

---

## Known integration risks

| Severity | Risk | Fix |
| --- | --- | --- |
| Critical | Missing `balloon_shooter.ai_detection_widget` breaks full UI startup if not restored. | Add the adapter or update imports to use the existing AI runtime. |
| High | Python and C++ JSON schemas may drift. | Create one schema document and round-trip tests. |
| High | Serial port handling is Windows-style `COM` focused. | Add cross-platform port discovery. |
| Medium | UI dependencies are not separated clearly from AI dependencies. | Add `requirements-ui.txt` or package extras. |
| Medium | UI has no smoke test in CI. | Add minimal import/startup test with Qt offscreen mode. |

---

## UI improvement roadmap

- Add a polished dark engineering theme.
- Add forbidden-zone editor directly in the video panel.
- Add QR-zone editor directly in the video panel.
- Add live FPS, latency, inference device, and model confidence display.
- Add command telemetry table with last TX/RX timestamps.
- Add log export to CSV or JSONL.
- Add replay mode for recorded videos.
- Add operator-safe simulation mode.
- Add UI screenshots to every major release.

---

## Keywords

PyQt5 robotics UI, control station, OpenCV camera interface, Air Defence GUI, Python robotics dashboard, PID tuning, pan tilt turret, serial communication, UART, JSON MCU protocol, robotics operator interface, mechatronics GUI, AI detection widget, YOLO11 UI integration.
