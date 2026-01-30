# Face Authentication Attendance System

A working face authentication system for attendance: register a user's face, identify the face from a real camera, and mark **punch-in** and **punch-out**.

## Features

- **Register** a user's face (one clear photo per user)
- **Identify** the face from live camera input
- **Punch-in** and **Punch-out** with a single capture (face + optional liveness)
- **Real camera** input via browser `getUserMedia` or server-side OpenCV
- **Varying lighting**: brightness checks reject too-dark or overexposed frames
- **Basic spoof prevention**: lighting validation; optional blink-based liveness (multi-frame)

## Quick Start

### Prerequisites

- Python 3.8+
- Camera (for attendance) and a browser with HTTPS or `localhost` for camera access

### Install

```bash
cd d:\medoc_assidn
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

**Windows (no CMake needed):** If `face-recognition` fails because it tries to build `dlib` from source, install the pre-built dlib and then face-recognition without deps:

```bash
pip install dlib-bin
pip install flask flask-cors opencv-python numpy Pillow face-recognition-models
pip install face-recognition --no-deps
```

### Run

```bash
python app.py
```

Open **http://127.0.0.1:5000** in a browser. Allow camera access when prompted.

1. **Register**: Go to *Register Face* → enter User ID and Name → *Capture Photo* → *Register*.
2. **Punch In/Out**: Go to *Punch In/Out* → look at the camera → click *Punch In* or *Punch Out*.
3. **Attendance**: View *Attendance* for today’s summary and full records.

---

## Model and Approach

### Face recognition

- **Library:** [face_recognition](https://github.com/ageitgey/face_recognition) (built on **dlib**).
- **Detection:** HOG-based face detector (configurable to CNN for higher accuracy with GPU).
- **Encoding:** dlib’s **ResNet-based** face recognition model (128-D embedding per face).
- **Matching:** Compare embedding of the current face to stored embeddings using **Euclidean distance**; accept if distance is below a threshold (default `0.5`; lower = stricter).

No custom training is done: we use pre-trained detection + recognition. “Training” here is **registration**: one (or more) photos per user are encoded and stored; attendance runs **identification** by encoding the live frame and comparing to those stored embeddings.

### Pipeline

1. **Registration:** User submits one image → face detected → 128-D embedding computed → stored on disk (`.npy` + metadata).
2. **Identification:** Camera frame → face detected → embedding computed → compared to all stored embeddings → closest match below threshold → user ID and name returned.
3. **Attendance:** Same as identification; on success, a punch-in or punch-out record is written to SQLite.

### Spoof prevention (basic)

- **Lighting:** Reject frames that are too dark (mean brightness &lt; 30) or overexposed (&gt; 220). Reduces use of very poor or manipulated lighting.
- **Blink (optional):** Eye Aspect Ratio (EAR) from `face_recognition.face_landmarks()`; a blink is detected when EAR drops then recovers. Requires **multiple frames** (e.g. short video or sequential captures). Single snapshot only uses lighting.

---

## “Training” Process

- **No neural network training** in this project. We use off-the-shelf models.
- **Registration = enrollment:** For each user we:
  1. Detect one face in the provided image.
  2. Compute a 128-D embedding with `face_recognition.face_encodings(..., model="small")`.
  3. Save the vector and metadata (user_id, name) under `data/embeddings/`.
- **Recognition:** At punch time we compute the embedding of the face in the current frame and match it to the stored set. No incremental learning or model updates.

---

## Accuracy Expectations

- **LFW benchmark:** The underlying dlib ResNet model is reported at ~99.38% on Labeled Faces in the Wild; our pipeline adds detection and real-world conditions.
- **In practice:** Expect high accuracy for:
  - Front-facing faces, moderate pose.
  - Reasonable lighting (after our brightness checks).
  - Users who registered with a clear, representative photo.
- **Typical drops:** Large pose/angle changes, heavy occlusion, very low light (rejected by our check), major appearance change (e.g. glasses on/off, beard), or low-quality registration image.
- **Threshold:** `FACE_MATCH_THRESHOLD = 0.5` is stricter than the library default (0.6); increase in `config.py` if you get too many false rejections.

---

## Known Failure Cases

1. **No face detected**  
   - Too dark or overexposed (rejected by lighting check).  
   - Face too small, turned away, or heavily occluded.  
   - **Mitigation:** Improve lighting, face the camera, ensure face is clearly visible.

2. **Multiple faces in frame**  
   - Only one face is allowed for identification.  
   - **Mitigation:** Ensure only the attending user is in frame.

3. **No match / wrong person**  
   - Distance to all stored embeddings above threshold.  
   - **Mitigation:** Re-register with a clearer photo; relax threshold slightly if needed; ensure consistent appearance (e.g. glasses).

4. **False match (different person accepted)**  
   - Rare with a strict threshold and good photos; more likely with very similar faces or poor registration.  
   - **Mitigation:** Keep threshold at 0.5 or lower; use better quality registration images.

5. **Blink liveness not used**  
   - Single snapshot cannot detect blink; only lighting is used.  
   - **Mitigation:** For stronger liveness, implement a multi-frame flow (e.g. send a short clip or several frames) and enable `REQUIRE_BLINK` in `config.py`.

6. **Camera / permission errors**  
   - Browser may block camera on non-HTTPS (except localhost).  
   - **Mitigation:** Use `https://` or `http://127.0.0.1:5000` and allow camera access.

7. **dlib / face_recognition install**  
   - Building dlib can fail on some systems (missing compiler, CMake).  
   - **Mitigation:** Install CMake and a C++ build toolchain; consider pre-built wheels if available for your platform.

---

## Project Structure

```
medoc_assidn/
├── app.py              # Flask app and API
├── config.py           # Paths, thresholds, spoof settings
├── requirements.txt
├── README.md           # This file
├── face_auth/
│   ├── __init__.py
│   ├── face_registry.py   # Register and store embeddings
│   ├── face_identifier.py # Identify face in frame
│   ├── spoof_detection.py # Lighting + optional blink
│   └── attendance.py      # Punch-in/out SQLite DB
├── data/
│   ├── embeddings/        # Stored face encodings and index
│   └── attendance.db      # SQLite attendance records
├── static/
│   ├── style.css
│   ├── camera.js
│   ├── register.js
│   └── attend.js
└── templates/
    ├── base.html
    ├── index.html
    ├── register.html
    ├── attend.html
    └── attendance.html
```

---

## Configuration

- **Paths:** `config.py` — `DATA_DIR`, `EMBEDDINGS_DIR`, `DB_PATH`.
- **Recognition:** `FACE_MATCH_THRESHOLD`, `NUM_JITTERS`, `MODEL` (hog/cnn).
- **Spoof:** `REQUIRE_BLINK`, `BLINK_EAR_THRESHOLD`, `MIN_BRIGHTNESS`, `MAX_BRIGHTNESS`.

---

## Evaluation Notes (Assignment)

- **Functional accuracy:** Face registration and identification work with real camera input; punch-in/out are recorded and viewable.
- **Reliability:** Single-face, front-facing, reasonable lighting and a good registration image give stable results; edge cases are documented above.
- **ML limitations:** No custom training; accuracy depends on pre-trained models and enrollment quality; spoof prevention is basic (lighting + optional blink with multi-frame).
- **Implementation:** Modular design (registry, identifier, spoof, attendance), config-driven thresholds, and a simple web UI suitable for local or hosted demo.
