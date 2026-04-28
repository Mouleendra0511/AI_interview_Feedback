# AI Interview Feedback

A full-stack app that analyzes an interview video and returns:
- **Audio extracted** from the video
- **Transcript** of the spoken content
- **Emotion analysis** from extracted video frames (face emotion detection)
- **Speaking metrics** (Words Per Minute + filler word counts)
- **AI feedback summary** generated from the transcript (Gemini)

## Repository Structure

- `client/` — React frontend (Create React App)
- `server/` — Flask backend APIs for video processing and analysis

## Features (What the app does)

### Frontend (`client/`)
The React UI lets a user:
1. Select and upload a **video file**
2. Receive:
   - Extracted audio playback
   - Transcript text
   - Emotion breakdown (percentages)
   - Speaking analysis (WPM + filler word counts)
   - AI-generated feedback summary

Main UI logic:
- `client/src/App.js` (primary UI + calls backend endpoints)
- UI component:
  - `client/src/components/ui/card.jsx` (simple Card components)

### Backend (`server/`)
The Flask server provides endpoints to:
- **Upload & process** a video: extract frames, extract audio, and transcribe audio
- **Analyze emotions** across extracted frames using `FER`
- **Generate feedback** from transcript using Gemini

Key files:
- `server/app.py` — upload + emotion analysis endpoints (no AI feedback endpoint here)
- `server/app1.py` — upload + emotion analysis + **/feedback (Gemini)** endpoint
- `server/video_utils.py` — helper utilities:
  - `extract_frames()`
  - `extract_audio()`
  - `transcribe_audio()` (Google Speech Recognition via `speech_recognition`)
- `server/requirements.txt` — currently includes a minimal set of dependencies

## API Endpoints

Backend runs on `http://localhost:5000` (as used by the frontend).

### `POST /upload`
Accepts multipart form-data with a file field named `video`.

Returns JSON including:
- `frames_extracted`
- `audio_file` (path/url)
- `transcript`
- (in `app1.py`) `duration` for WPM calculation

### `POST /analyze-emotions`
Analyzes face emotions across saved frames in the `frames/` folder.

Returns:
- `frame_emotions`
- `summary`
- `percentage_summary`
- `formatted_summary`

### `POST /feedback`  *(only in `server/app1.py`)*
Takes JSON:
```json
{ "transcript": "..." }
```
Returns an OpenAI-like shaped response:
```json
{
  "choices": [
    { "message": { "content": "..." } }
  ]
}
```

## Running the Project (Local)

### 1) Start the backend (Flask)
```bash
cd server
python -m venv .venv
# activate venv (windows): .venv\Scripts\activate
# activate venv (mac/linux): source .venv/bin/activate

pip install -r requirements.txt
python app1.py
```

> Note: The frontend calls `/feedback`, which exists in `app1.py`.  
> So for full functionality, run **`app1.py`** (not `app.py`).

#### Gemini API Key (required for `/feedback`)
Create a `.env` file inside `server/`:
```env
GEMINI_API_KEY=your_key_here
```

### 2) Start the frontend (React)
```bash
cd client
npm install
npm start
```

Frontend will start at:
- `http://localhost:3000`

Backend should be running at:
- `http://localhost:5000`

## Notes / Known Gaps

- `server/requirements.txt` is incomplete relative to the imports in the code.  
  Your server code uses packages like `opencv-python`, `fer`, `SpeechRecognition`, `google-generativeai`, `python-dotenv`, etc., but they are not listed in `requirements.txt` yet.
- There are two server entrypoints:
  - `app.py` (no `/feedback`)
  - `app1.py` (includes `/feedback` with Gemini)
- The server writes to folders in the backend working directory:
  - `uploads/`, `frames/`, `audio/`

## Tech Stack

- Frontend: React (Create React App)
- Backend: Flask + Flask-CORS
- Video/Audio:
  - OpenCV (`cv2`) for frame extraction
  - MoviePy for audio extraction
  - SpeechRecognition (Google recognizer) for transcription
- Emotion detection: `FER` (facial emotion recognition)
- AI feedback: Google Gemini (`google.generativeai`)
