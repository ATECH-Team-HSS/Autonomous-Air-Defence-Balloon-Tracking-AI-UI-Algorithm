# AI System

<p align="center">
  <img alt="YOLO11" src="https://img.shields.io/badge/YOLO-11-orange">
  <img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-real--time-green">
  <img alt="Tracking" src="https://img.shields.io/badge/Tracking-SORT%20style-blue">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue">
</p>

This document explains the AI subsystem: the YOLO11 balloon detector, dataset, training artifacts, inference pipeline, tracking logic, target selection, alignment checks, safety-zone evaluation, and integration contract for the PyQt5 UI and hardware-control layers.

---

## AI scope

The AI package under `src/balloon_shooter/` provides:

- YOLO11 red/blue balloon detection.
- Real-time OpenCV camera inference.
- Detection output normalization.
- SORT-style target tracking using Kalman prediction and IoU matching.
- Target selection by color strategy.
- Confirmation delay to avoid unstable target switching.
- Crosshair alignment evaluation.
- Forbidden-zone safety evaluation.
- OpenCV overlay rendering.
- QR-code ROI decoding.
- HSV color/shape detection helper.
- Unit-tested pure-Python modules.

The AI demo intentionally keeps physical output disabled. Hardware action should be handled only after safety validation, operator supervision, and a verified MCU command contract.

---

## Model objective

The final model detects two classes:

| Class ID | Class name |
| --- | --- |
| `0` | `Blue Balloon` |
| `1` | `Red Balloon` |

The model file used for inference is:

```text
models/best.pt
```

The model path is configured in `config.yaml`:

```yaml
video:
  model_path: "models/best.pt"
  class_names:
    - "Blue Balloon"
    - "Red Balloon"
```

---

## Dataset summary

The previous training documentation describes the dataset as:

| Split | Images |
| --- | ---: |
| Training | 1,666 |
| Validation | 308 |
| Test | 138 |
| Total | 2,112 |

About one quarter of the dataset came from controlled black-background scenes, while the rest was collected in more varied environments to improve generalization.

<p align="center">
  <img src="docs/assets/ai/original-dataset-image.jpeg" alt="Original red and blue balloon dataset image" width="70%">
</p>

---

## Training artifacts

The AI asset folder contains the main training outputs:

```text
docs/assets/ai/
├── results.png
├── results.csv
├── results.xlsx
├── PR_curve.png
├── P_curve.png
├── R_curve.png
├── F1_curve.png
├── confusion_matrix.png
├── confusion_matrix_normalized.png
├── labels.jpg
└── labels_correlogram.jpg
```

### Training result overview

<p align="center">
  <img src="docs/assets/ai/results.png" alt="YOLO training results" width="90%">
</p>

Final epoch metrics from `results.csv`:

| Epoch | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
| ---: | ---: | ---: | ---: | ---: |
| 100 | 0.96039 | 0.90348 | 0.96342 | 0.78729 |

Best observed values in the training log:

| Metric focus | Epoch | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Best mAP@0.5 | 66 | 0.97451 | 0.96721 | 0.98272 | 0.78228 |
| Best mAP@0.5:0.95 | 84 | 0.96480 | 0.92518 | 0.97483 | 0.79810 |

These metrics are strong for a specialized balloon detector, especially in controlled and semi-controlled environments. Do not overclaim real-world robustness without more diverse validation videos and hardware-in-the-loop tests.

---

## Curves and confusion matrices

### Precision–Recall curve

<p align="center">
  <img src="docs/assets/ai/PR_curve.png" alt="YOLO precision recall curve" width="75%">
</p>

The PR curve helps evaluate whether the detector maintains high precision while still detecting most real balloons.

### Precision, recall, and F1 confidence curves

<p align="center">
  <img src="docs/assets/ai/P_curve.png" alt="Precision confidence curve" width="32%">
  <img src="docs/assets/ai/R_curve.png" alt="Recall confidence curve" width="32%">
  <img src="docs/assets/ai/F1_curve.png" alt="F1 confidence curve" width="32%">
</p>

Use these plots when choosing `confidence_threshold` in `config.yaml`. Higher thresholds reduce false detections but can miss small or weak targets.

### Confusion matrices

<p align="center">
  <img src="docs/assets/ai/confusion_matrix.png" alt="Confusion matrix" width="45%">
  <img src="docs/assets/ai/confusion_matrix_normalized.png" alt="Normalized confusion matrix" width="45%">
</p>

Color classification matters because mission logic may depend on red/blue target priority.

### Label analysis

<p align="center">
  <img src="docs/assets/ai/labels.jpg" alt="YOLO label distribution" width="45%">
  <img src="docs/assets/ai/labels_correlogram.jpg" alt="YOLO label correlogram" width="45%">
</p>

These images help analyze class distribution, target locations, and bounding-box geometry.

---

## Runtime inference pipeline

```text
Load config.yaml
      │
      ▼
Load YOLO model from models/best.pt
      │
      ▼
Open camera/video source with OpenCV
      │
      ▼
Resize frame to configured resolution
      │
      ▼
Run YOLO inference
      │
      ▼
Return detections:
[x1, y1, x2, y2, confidence, class_id]
      │
      ▼
Update tracker
      │
      ▼
Return tracks:
[x1, y1, x2, y2, track_id, class_id]
      │
      ▼
Select and confirm target
      │
      ▼
Evaluate forbidden-zone safety
      │
      ▼
Check crosshair alignment
      │
      ▼
Draw overlays / emit state to UI
```

<p align="center">
  <img src="docs/assets/diagrams/ai-workflow.png" alt="AI workflow" width="85%">
</p>

---

## Detection output contract

`detector.py` returns detections as:

```python
[x1, y1, x2, y2, confidence, class_id]
```

| Field | Meaning |
| --- | --- |
| `x1`, `y1` | Top-left corner of the bounding box. |
| `x2`, `y2` | Bottom-right corner of the bounding box. |
| `confidence` | YOLO confidence score. |
| `class_id` | `0` for blue balloon, `1` for red balloon. |

---

## Tracking logic

`tracker.py` implements a SORT-style tracker:

```text
Kalman prediction + IoU association + persistent track IDs
```

Each track is returned as:

```python
[x1, y1, x2, y2, track_id, class_id]
```

Tracking reduces frame-to-frame flicker and provides stable IDs for UI display and future servo control.

---

## Target-selection logic

`targeting.py` filters tracks by:

- Minimum bounding-box width.
- Minimum bounding-box height.
- Color strategy.
- Confirmation duration.

Configuration:

```yaml
targeting:
  min_bbox_width: 20
  min_bbox_height: 20
  color_strategy: "red_only"
  confirmation_duration: 0.3
```

Supported strategies:

| Strategy | Behavior |
| --- | --- |
| `red_only` | Select red balloons only. |
| `blue_only` | Select blue balloons only. |
| `red_then_blue` | Prefer red; fall back to blue. |
| `all` | Accept both classes. |

---

## Crosshair alignment

`target_distance.py` computes target center and compares it with the configured crosshair:

```yaml
crosshair:
  x: 640
  y: 360

targeting:
  x_tolerance: 50
  y_tolerance: 50
```

A target is aligned when its center falls inside the configured tolerance window. This signal is useful for future PID, servo, and MCU control.

---

## Safety-zone logic

`safety.py` evaluates whether the selected target center is inside the forbidden-fire zone.

```yaml
safety:
  enabled: true
  forbidden_fire_zone:
    enabled: true
    rect: [100, 100, 300, 200]
```

Rectangle format:

```text
[x, y, width, height]
```

Known safety states include:

- `safe`
- `no target`
- `target in forbidden zone`
- `safety disabled`

This is a software helper, not a complete safety system. Physical actuation must use additional hardware interlocks, manual supervision, and emergency-stop handling.

---

## OpenCV overlays

`overlays.py` draws:

- YOLO detections.
- Selected target box.
- Target ID and class name.
- Target center point.
- Crosshair.
- Forbidden-zone rectangle.
- FPS.
- Safety and alignment status.

These overlays make the pipeline easy to debug before connecting UI or hardware layers.

---

## Auxiliary vision

### QR-code ROI

`auxiliary_vision/qr_decoder.py` decodes QR codes inside a configured ROI.

```yaml
auxiliary_vision:
  qr_roi: [100, 50, 180, 180]
```

Default accepted command values are `A` and `B`.

### Shape detection ROI

`auxiliary_vision/shape_detector.py` uses HSV segmentation and contour approximation to detect simple colored objects.

Supported colors include red, green, and blue. Supported shape categories include triangle, square, and circle.

---

## Run commands

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python -m balloon_shooter.main --config config.yaml
```

Installed command:

```bash
balloon-shooter-ai --config config.yaml
```

Auxiliary demo:

```bash
python examples/task_command_demo.py --config config.yaml
```

---

## Tests

```bash
pytest
ruff check .
```

Current tests cover configuration loading, ROI parsing, QR decoding behavior, HSV shape detection, target-distance logic, forbidden-zone safety, and tracker ID persistence.

---

## Limitations

- Strongest performance is expected in environments represented by the dataset.
- Complex backgrounds can create false detections.
- Unusual lighting can reduce red/blue classification reliability.
- Motion blur, occlusion, or small distant balloons can reduce recall.
- Forbidden-zone logic checks target center; box-overlap safety would be stricter.
- The OpenCV AI demo does not implement full physical firing control.
- UI integration requires a stable AI widget adapter.

---

## Recommended AI improvements

1. Add more varied lighting, background, distance, and camera-angle data.
2. Add real-world validation videos and per-scene metrics.
3. Export ONNX for deployment options.
4. Benchmark CPU, CUDA, and TensorRT inference speeds.
5. Add logging for detections, tracks, FPS, target state, and safety state.
6. Improve forbidden-zone logic using bounding-box overlap.
7. Add a PyQt-compatible AI widget adapter with tested signals.

---

## Keywords

YOLO11, Ultralytics, OpenCV, computer vision, balloon detection, red balloon detection, blue balloon detection, object detection, target tracking, Kalman filter, SORT tracker, IoU matching, Air Defence AI, robotics, mechatronics, PyQt5, PID control, servo turret, QR detection, HSV shape detection, engineering thesis, Teknofest robotics.
