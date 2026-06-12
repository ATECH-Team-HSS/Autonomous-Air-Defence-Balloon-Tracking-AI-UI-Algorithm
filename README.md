# Air Defence ATech

<p align="center">
  <img src="assets/logo.png" alt="ATech logo" width="180">
</p>

<p align="center">
  <strong>YOLO11 balloon detection, real-time tracking, PyQt5 control-station UI, and servo-turret integration for a safe educational Air Defence robotics prototype.</strong>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue">
  <img alt="YOLO11" src="https://img.shields.io/badge/YOLO-11-orange">
  <img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-real--time-green">
  <img alt="PyQt5" src="https://img.shields.io/badge/PyQt5-control%20station-purple">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-lightgrey">
</p>

> **Safety scope**  
> This repository is for education, research, competitions, and supervised balloon-target demonstrations. It is not a deployable defence product. Test physical outputs with dummy indicators first, keep manual supervision, use emergency-stop logic, and comply with local safety rules.

---

## Overview

**Air Defence ATech** is a PC-based computer-vision and mechatronics project for detecting red and blue balloons, tracking targets in real time, visualizing mission state in a PyQt5 control station, and preparing command data for a microcontroller-driven pan/tilt turret.

The repository combines:

- **YOLO11** object detection for `Blue Balloon` and `Red Balloon` classes.
- **OpenCV** camera capture, overlays, crosshair visualization, and safety-zone drawing.
- **SORT-style tracking** using Kalman filtering and IoU association.
- **Target-selection logic** with red-only, blue-only, red-then-blue, and all-target modes.
- **PyQt5 UI** for camera/AI view, mission controls, PID tuning, status indicators, and system logs.
- **Serial/UART integration** for JSON-based communication with turret and station MCUs.
- **Auxiliary vision** for QR-code ROI decoding and HSV-based colored shape recognition.
- **Tests and CI** using `pytest`, `ruff`, and GitHub Actions.

<p align="center">
  <img src="docs/assets/general/real-system-photo.jpeg" alt="Real Air Defence prototype" width="46%">
  <img src="docs/assets/general/cad-design-main.jpg.jpeg" alt="CAD design of the Air Defence turret" width="46%">
</p>

---

## Documentation map

| Document | Purpose |
| --- | --- |
| [`README.md`](README.md) | Main repository overview, installation, usage, modules, and release notes. |
| [`README_AI.md`](README_AI.md) | AI model, dataset, metrics, inference pipeline, tracking, targeting, safety logic, and limitations. |
| [`README_UI.md`](README_UI.md) | PyQt5 control-station UI, frame layout, mission workflow, PID controls, serial communication, and operator flow. |
| [`AGENTS.md`](AGENTS.md) | AI-assisted development guide for ChatGPT, Claude, Gemini, Cursor, Copilot, Windsurf, and similar agents. |

---

## System architecture

```text
Camera / video source
        │
        ▼
OpenCV frame capture
        │
        ▼
YOLO11 balloon detection
        │
        ▼
Tracker: Kalman filter + IoU association
        │
        ▼
Target selector: color strategy + confirmation delay
        │
        ├──► Safety check: forbidden-fire zone
        │
        ├──► Crosshair alignment check
        │
        └──► PyQt5 UI / telemetry / logs
                         │
                         ▼
              PID pan/tilt command generation
                         │
                         ▼
              JSON serial command to MCU
```

<p align="center">
  <img src="docs/assets/diagrams/ai-workflow.png" alt="AI workflow diagram" width="85%">
</p>

---

## Repository structure

```text
Air Defence/
├── README.md
├── README_AI.md / AI_README.md
├── README_UI.md / UI_README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── config.yaml
├── models/
│   └── best.pt
├── assets/
│   ├── ATech_logo.png
│   ├── ATech_icon.png
│   ├── green_icon.png
│   ├── yellow_icon.png
│   └── red_icon.png
├── docs/assets/
│   ├── general/
│   ├── ai/
│   ├── ui/
│   └── diagrams/
├── src/
│   ├── balloon_shooter/
│   ├── ui/
│   ├── hardware_manager/
│   ├── mcu_bridge/
│   ├── recognition_system/
│   └── main_window.py
├── examples/
│   └── task_command_demo.py
├── tests/
└── .github/workflows/ci.yml
```

---

## Main features

### AI and vision

- YOLO11 inference using `models/best.pt`.
- Red/blue balloon classification.
- Configurable confidence and IoU thresholds.
- SORT-style tracking with persistent track IDs.
- Target confirmation delay to reduce unstable target switching.
- Configurable crosshair and alignment tolerance.
- Software-level forbidden-zone validation.
- Live overlays for detections, selected target, FPS, safety state, and crosshair.

### UI and operator workflow

- PyQt5 desktop control station.
- Upper frame for camera/AI feed and mission tabs.
- Middle frame for command buttons, mission selection, command values, and status indicators.
- Lower frame for logs, errors, AI messages, and system events.
- PID tuner for pan and tilt axes.
- Manual jogging controls.
- Auto-aim and auto-shoot state handling.

### Hardware integration

- Serial communication through `pyserial`.
- JSON command payloads for turret/station MCU communication.
- Embedded-side helper files: `JsonMessenger.cpp` and `JsonMessenger.h`.
- PID-based command generation through `hardware_manager/pid_tracker.py`.
- MCU connection/disconnection and telemetry callbacks through `hardware_manager/mcu_communication.py`.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

> On Linux, `pyzbar` may require the system `zbar` library. Example: `sudo apt install libzbar0`.

---

## Configuration

The main runtime settings live in [`config.yaml`](config.yaml).

Important sections:

```yaml
video:
  source: 0
  frame_width: 1280
  frame_height: 720
  model_path: "models/best.pt"
  class_names:
    - "Blue Balloon"
    - "Red Balloon"
  confidence_threshold: 0.5
  iou_threshold: 0.45
  device: "auto"

targeting:
  color_strategy: "red_only"
  confirmation_duration: 0.3
  x_tolerance: 50
  y_tolerance: 50

safety:
  enabled: true
  forbidden_fire_zone:
    enabled: true
    rect: [0, 0, 0, 0]
```

Supported target strategies:

| Strategy | Behavior |
| --- | --- |
| `red_only` | Select only red balloons. |
| `blue_only` | Select only blue balloons. |
| `red_then_blue` | Prefer red; fall back to blue if no red target exists. |
| `all` | Accept both target classes. |

---

## Run the AI demo

```bash
python -m balloon_shooter.main --config config.yaml
```

Or after editable install:

```bash
balloon-shooter-ai --config config.yaml
```

Press `q` to close the OpenCV window.

---

## Run the auxiliary QR/shape demo

```bash
python examples/task_command_demo.py --config config.yaml
```

Custom source:

```bash
python examples/task_command_demo.py --config config.yaml --source path/to/image_or_video
```

Custom ROIs:

```bash
python examples/task_command_demo.py \
  --config config.yaml \
  --qr-roi 100,50,180,180 \
  --shape-roi 320,50,180,180
```

---

## Run the PyQt5 control station

From the repository root:

```bash
python src/main_window.py
```

The UI is designed for the integrated control-station workflow: camera display, AI detection widget, mission selection, PID tuning, manual jogging, system logs, and MCU serial communication.

> Current integration note: the UI imports `balloon_shooter.ai_detection_widget`. If your branch does not include this widget, add the adapter file or connect the existing AI runtime to the UI signal contract before presenting the GUI as fully runnable.

---

## Quality checks

```bash
ruff check .
pytest
```

The repository includes GitHub Actions CI under `.github/workflows/ci.yml`.

---

## Important modules

| Path | Role |
| --- | --- |
| `src/balloon_shooter/config.py` | Loads YAML configuration into structured dataclasses. |
| `src/balloon_shooter/detector.py` | YOLO model wrapper for balloon detection. |
| `src/balloon_shooter/tracker.py` | SORT-style tracker with Kalman filter and IoU matching. |
| `src/balloon_shooter/targeting.py` | Target selection and confirmation logic. |
| `src/balloon_shooter/safety.py` | Forbidden-zone safety evaluation. |
| `src/balloon_shooter/target_distance.py` | Crosshair offset and alignment checks. |
| `src/balloon_shooter/overlays.py` | OpenCV visualization utilities. |
| `src/balloon_shooter/auxiliary_vision/qr_decoder.py` | QR-code ROI decoder. |
| `src/balloon_shooter/auxiliary_vision/shape_detector.py` | HSV shape/color detector. |
| `src/ui/frames/upper_frame.py` | Camera/AI view, mission tabs, PID and port controls. |
| `src/ui/frames/middle_frame.py` | Mission buttons, command display, and status indicators. |
| `src/ui/frames/lower_frame.py` | Logging panel. |
| `src/ui/signals_controller.py` | Main GUI logic, mission state, PID, and command routing. |
| `src/hardware_manager/mcu_communication.py` | Serial communication with MCU hardware. |
| `src/hardware_manager/pid_tracker.py` | PID-based target tracking command calculation. |
| `src/mcu_bridge/JsonMessenger.cpp` | Embedded-side JSON messaging helper. |

---

## Media

### Real system and CAD

<p align="center">
  <img src="docs/assets/general/real-system-photo.jpeg" alt="Real Air Defence system" width="48%">
  <img src="docs/assets/general/cad-design-main.jpg.jpeg" alt="Air Defence CAD design" width="48%">
</p>

### UI

<p align="center">
  <img src="docs/assets/ui/gui-screen.png" alt="Air Defence PyQt5 GUI" width="48%">
  <img src="docs/assets/ui/ui-control-station.jpg" alt="Air Defence control station" width="48%">
</p>

### Demonstration videos

- [`autonomous-balloon-tracking.mp4`](docs/assets/general/autonomous-balloon-tracking.mp4)
- [`autonomous-balloon-engagement.mp4`](docs/assets/general/autonomous-balloon-engagement.mp4)

---

## Development roadmap

Recommended next improvements before public release:

1. Add or restore `src/balloon_shooter/ai_detection_widget.py` so the UI runs cleanly.
2. Define one canonical Python↔MCU JSON schema and test it from both sides.
3. Add `requirements-ui.txt` or package extras such as `pip install .[ui]`.
4. Add UI smoke tests to CI.
5. Remove committed `__pycache__` folders from the repository.
6. Standardize documentation filenames: `README_AI.md` and `README_UI.md`.
7. Normalize asset folder names to lowercase: `docs/assets/ai` and `docs/assets/ui`.

---

## License

This project is released under the MIT License. See [`LICENSE`](LICENSE).

---

## Keywords

YOLO11, Ultralytics, OpenCV, PyQt5, Python, computer vision, object detection, balloon detection, red balloon, blue balloon, Air Defence prototype, target tracking, Kalman filter, SORT tracker, robotics, mechatronics, servo turret, PID control, UART, serial communication, QR detection, HSV shape detection, Teknofest, AI robotics project, engineering thesis, graduation project.
