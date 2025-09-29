
# Gamified-yoga-website

**A gamified yoga practice web app with pose-sensing backend and a static/JS frontend.**
This project contains a simple frontend (web UI) and a Python backend that leverages prebuilt pose/hand landmarker task files (Mediapipe-style `.task` files), a small local SQLite database, and a `requirements.txt` for dependencies. The repo structure and filenames were taken from the repository listing. ([GitHub][1])

---

## Quick highlights

* Frontend: static site with HTML/CSS/JS (served as static files). ([GitHub][2])
* Backend: Python app(s) to process keypoints, score similarity, and expose any REST endpoints (project root shows `backend` folder). ([GitHub][3])
* Pretrained task files: `hand_landmarker.task` and `pose_landmarker_heavy.task` — likely Mediapipe/TF Lite task files used for landmark detection. ([GitHub][1])
* Local database: `yoga_platform.db` (SQLite) — likely used to persist user or pose session data. ([GitHub][1])

---

## Recommended `README.md` (paste into your repo)

```markdown
# Gamified Yoga Website

A gamified yoga practice platform: web frontend + Python backend for pose detection, scoring, and simple persistence.

> **Repository structure (high-level)**  
> This README describes each top-level file and folder and gives instructions to run the project locally.

---

## Repo layout

```

.
├── backend/                       # Python backend code (API, pose-processing, utils)
├── frontend/                      # Static site (HTML/CSS/JS) — the user-facing gamified UI
├── data/                          # Pose data and JSON examples (poses / references)
├── **pycache**/                   # Python caches (ignored in git normally)
├── .gitignore
├── main.py                        # Top-level launcher / integration script (if present)
├── hand_landmarker.task           # Prebuilt hand landmarker task file (Mediapipe/TF Lite task)
├── pose_landmarker_heavy.task     # Prebuilt pose landmarker / heavy model task file
├── requirements.txt               # Python dependencies
├── yoga_platform.db               # SQLite DB with app tables (users/sessions/poses)

````

> The file and folder names above were taken from the repository listing. If any file has a different role than described, update the README accordingly. :contentReference[oaicite:6]{index=6}

---

## What each file/folder is for

### `frontend/`
Contains the static website files (HTML, CSS, JS). This is the gamified UI that interacts with the backend (via fetch/XHR). Typical files:
- `index.html` — landing page / main SPA entry.
- `assets/`, `css/`, `js/` — styling, images and client-side code.
**How it works:** the frontend captures user actions, shows pose references, score, gamified UI (points/badges), and pushes camera frames / keypoints or session metadata to the backend for analysis.

*(Source: repository frontend folder listing.)* :contentReference[oaicite:7]{index=7}

### `backend/`
Python code to run the server and pose-processing logic. Typical responsibilities:
- Start a web server (Flask/FastAPI) with endpoints to accept keypoint data or video/frames.
- Load model/task files (`pose_landmarker_heavy.task`, `hand_landmarker.task`) to perform landmark detection if the backend does detection.
- Normalize landmarks, compute similarity to reference poses, generate scoring and feedback.
- Interact with `yoga_platform.db` to persist sessions, scores, or user progress.

*(Source: repository backend folder listing.)* :contentReference[oaicite:8]{index=8}

### `main.py`
Top-level script — likely starts the backend (or integrates frontend/backend for local dev). If this script is the app entry, run it to launch the service (see run instructions below). :contentReference[oaicite:9]{index=9}

### `hand_landmarker.task` and `pose_landmarker_heavy.task`
Pre-built model/task files — these are typically Mediapipe/TF Lite Task artifacts that can be loaded by the appropriate SDK (for example MediaPipe Tasks API or TensorFlow Lite Task library) to run on-device landmark detection. They allow fast hand and pose landmark extraction without training from scratch. :contentReference[oaicite:10]{index=10}

### `yoga_platform.db`
A SQLite database bundled in the repo. Likely contains tables for:
- `users` — user profiles or accounts,
- `sessions` — recorded pose sessions,
- `poses` — reference pose templates,
- `scores` — session scoring history.

**Note:** Always avoid committing production user data to Git. If this DB contains sample/demo data, that’s fine; otherwise regenerate or sanitize before publishing. :contentReference[oaicite:11]{index=11}

### `requirements.txt`
Python dependencies needed for the backend (e.g., `flask`/`fastapi`, `uvicorn`, `numpy`, `opencv-python`, `mediapipe`/`tflite-runtime` etc.). Install them in a virtualenv prior to running the backend. :contentReference[oaicite:12]{index=12}

---

## Quick start (development)

> These are step-by-step local instructions that should work in most setups. If `main.py` or backend uses a specific framework, adapt the run command accordingly.

1. Clone the repo and enter the folder:
   ```bash
   git clone https://github.com/Harishk2508/Gamified-yoga-website.git
   cd Gamified-yoga-website
````

2. Create & activate a Python virtual environment (recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate      # Windows (PowerShell)
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Backend:

   * If `main.py` is the app launcher:

     ```bash
     python main.py
     ```
   * If backend has `app.py` with FastAPI:

     ```bash
     uvicorn backend.app:app --reload
     ```
   * If using Flask:

     ```bash
     export FLASK_APP=backend.app
     flask run
     ```

   (Adjust the command if the actual backend uses a different entrypoint.)

5. Frontend:

   * For development you can open `frontend/index.html` in your browser.
   * To connect to the backend: ensure frontend requests point to `http://localhost:<backend_port>` (default `5000` or `8000` depending on framework).

6. Visit the app in your browser (e.g., `http://localhost:8080` or open the `index.html` directly).

---

## How pose detection & scoring are expected to work (conceptual)

1. **Capture & detect** — The app either:

   * Runs the `.task` files in the client (if using WASM/TF Lite on client), or
   * Sends frames/landmarks to the backend which loads `pose_landmarker_heavy.task` & `hand_landmarker.task` to produce landmarks.

2. **Normalize** — Normalize joint coordinates to body size (scale/translate) so comparisons are invariant to distance/zoom.

3. **Similarity & scoring** — Compute a similarity metric between user landmarks and reference pose landmarks (e.g., weighted joint angle differences or normalized Euclidean distance). Convert similarity to a human-friendly score and gamification feedback (points, badges).

4. **Persistence** — Save session metrics and progress to `yoga_platform.db`.

---

## Notes & security

* The `.task` files may be large and are model artifacts — ensure distribution is permitted by the model license.
* The `yoga_platform.db` file is included in the repo — verify it doesn't contain private user data. If it does, remove and add an example DB with sanitized content. ([GitHub][1])

---

## Testing & development tips

* If you have a `_keypoints.json` reference for each pose (you mentioned having one), place them under `data/refs/` and ensure the scoring code reads from that folder.
* Unit-test the normalization and similarity functions with a few synthetic examples to ensure stability across scale/rotation.

---

## Contribution

If you want to submit changes:

1. Fork the repo
2. Create a branch per feature/fix
3. Open a PR describing the change

---

## Contact / License

Add a license file (e.g., `MIT`) if you want open source contributions. Add contact/author lines here.

```

---

## What I could not fully confirm (and how you can help me make the README exact)
I generated the README using the repository listing (folder & filenames) as the authoritative source. I could not read individual file contents (dynamic GitHub view blocked raw reads in this session), so I made conservative, commonly-correct assumptions about:
- The exact backend entrypoint name (`main.py`, `app.py`, or something else).
- The precise web framework used (Flask vs FastAPI).
- Exact dependency names inside `requirements.txt`.

If you paste here the top ~100 lines of `backend/<main file>` (or paste `requirements.txt` and the first 80 lines of `main.py`), I’ll immediately update the README to include precise run commands, exact endpoints, and any missing details — no waiting. Alternatively, give me permission to fetch raw files and I’ll re-generate the README with direct citations to the exact file contents.

---

Would you like me to:
1. Update the README now if you paste `requirements.txt` + backend entrypoint file contents? **(fastest, exact)**  
2. Or fetch the raw files from GitHub (I can try again to pull `raw.githubusercontent.com` URLs) and produce a fully exact README with concrete run commands and endpoint descriptions? **(I already attempted; it failed earlier — I can try again if you prefer)**

Tell me which option you prefer (or paste the files) and I’ll finalize the README exactly to your code.
```

[1]: https://github.com/Harishk2508/Gamified-yoga-website "GitHub - Harishk2508/Gamified-yoga-website"
[2]: https://github.com/Harishk2508/Gamified-yoga-website/tree/main/frontend "Gamified-yoga-website/frontend at main · Harishk2508/Gamified-yoga-website · GitHub"
[3]: https://github.com/Harishk2508/Gamified-yoga-website/tree/main/backend "Gamified-yoga-website/backend at main · Harishk2508/Gamified-yoga-website · GitHub"
