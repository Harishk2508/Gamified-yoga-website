# Gamified Yoga Website

A gamified yoga practice platform: web frontend + Python backend for pose detection, scoring, and simple persistence.


---

## Repo layout

```

├── backend/ # Python backend code (API, pose-processing, utils)
├── frontend/ # Static site (HTML/CSS/JS) — the user-facing gamified UI
├── data/ # Pose data and JSON examples (poses / references)
├── pycache/ # Python caches (ignored in git normally)
├── .gitignore
├── main.py # Top-level launcher / integration script (if present)
├── hand_landmarker.task # Prebuilt hand landmarker task file (Mediapipe/TF Lite task)
├── pose_landmarker_heavy.task # Prebuilt pose landmarker / heavy model task file
├── requirements.txt # Python dependencies
├── yoga_platform.db # SQLite DB with app tables (users/sessions/poses)

````


---

## What each file/folder is for

### `frontend/`
Contains the static website files (HTML, CSS, JS). This is the gamified UI that interacts with the backend (via fetch/XHR). Typical files:
- `index.html` — landing page / main SPA entry.
- `assets/`, `css/`, `js/` — styling, images and client-side code.
**How it works:** the frontend captures user actions, shows pose references, score, gamified UI (points/badges), and pushes camera frames / keypoints or session metadata to the backend for analysis.


### `backend/`
Python code to run the server and pose-processing logic. Typical responsibilities:
- Start a web server (Flask/FastAPI) with endpoints to accept keypoint data or video/frames.
- Load model/task files (`pose_landmarker_heavy.task`, `hand_landmarker.task`) to perform landmark detection.
- Normalize landmarks, compute similarity to reference poses, generate scoring and feedback.
- Interact with `yoga_platform.db` to persist sessions, scores, or user progress.


### `main.py`
Top-level script — likely starts the backend (or integrates frontend/backend for local dev).

### `hand_landmarker.task` and `pose_landmarker_heavy.task`
Pre-built model/task files — these are typically Mediapipe/TF Lite Task artifacts that can be loaded by the appropriate SDK (for example MediaPipe Tasks API or TensorFlow Lite Task library) to run on-device landmark detection. They allow fast hand and pose landmark extraction without training from scratch. :contentReference[oaicite:10]{index=10}

### `yoga_platform.db`
A SQLite database bundled in the repo. Likely contains tables for:
- `users` — user profiles or accounts,
- `sessions` — recorded pose sessions,
- `poses` — reference pose templates,
- `scores` — session scoring history.


### `requirements.txt`
Python dependencies needed for the backend (e.g., `flask`/`fastapi`, `uvicorn`, `numpy`, `opencv-python`, `mediapipe`/`tflite-runtime` etc.). Install them in a virtualenv prior to running the backend. 

---

## Quick start (development)

> These are step-by-step local instructions that should work in most setups. If `main.py` or backend uses a specific framework, adapt the run command accordingly.

1. Clone the repo and enter the folder:
   ```bash
   git clone https://github.com/Harishk2508/Gamified-yoga-website.git
   cd Gamified-yoga-website

2. Create & activate a Python virtual environment (recommended):

python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate      # Windows (PowerShell)

3. Install dependencies:

pip install -r requirements.txt

4. Backend:

uvicorn backend.app:app --reload

5. Visit the app in your browser (e.g., `http://localhost:8080`).

---
