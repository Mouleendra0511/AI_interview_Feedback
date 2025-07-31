from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import cv2
from fer import FER
from video_utils import extract_frames, extract_audio, transcribe_audio
from flask import send_from_directory
import google.generativeai as genai
from dotenv import load_dotenv

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = "SET_YOUR_OWN_KEY"  # Fallback key
genai.configure(api_key=api_key)

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
FRAMES_FOLDER = 'frames'
AUDIO_FOLDER = 'audio'

# Create necessary folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FRAMES_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Store your API key in environment variables
genai.configure(api_key="AIzaSyD1uTUq20yZpLJAb0XJRoA_u3Qth-cD8qY")

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    video = request.files['video']
    if video.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filepath = os.path.join(UPLOAD_FOLDER, video.filename)
    video.save(filepath)

    try:
        # Extract frames
        frame_count = extract_frames(filepath, output_folder=FRAMES_FOLDER)

        # Extract audio
        audio_path, duration = extract_audio(filepath, output_folder=AUDIO_FOLDER)

        # Transcribe audio
        transcript = transcribe_audio(audio_path)

        audio_url = audio_path.replace("\\", "/")

        return jsonify({
            "message": "Video processed successfully!",
            "frames_extracted": frame_count,
            "audio_file": audio_url,
            "transcript": transcript,
            "duration": duration  # Include duration for WPM calculation
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory("audio", filename)

@app.route('/analyze-emotions', methods=['POST'])
def analyze_emotions():
    folder_path = FRAMES_FOLDER
    emotions = []

    if not os.path.exists(folder_path):
        return jsonify({"error": "Frames folder not found."}), 404

    frame_files = sorted([f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png'))])

    if not frame_files:
        return jsonify({"error": "No frame images found in folder."}), 400

    detector = FER(mtcnn=True)

    for frame in frame_files:
        frame_path = os.path.join(folder_path, frame)
        img = cv2.imread(frame_path)

        if img is None:
            emotions.append("Invalid image")
            continue

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = detector.detect_emotions(img)

        if result:
            top_emotion = max(result[0]['emotions'], key=result[0]['emotions'].get)
            emotions.append(top_emotion)
        else:
            emotions.append("No face")

    valid_emotions = [e for e in emotions if e not in ["No face", "Invalid image"]]
    total = len(valid_emotions)

    summary = {emotion: valid_emotions.count(emotion) for emotion in set(valid_emotions)}
    percentage_summary = {emotion: f"{(count / total) * 100:.2f}%" for emotion, count in summary.items()}

    return jsonify({
        "frame_emotions": emotions,
        "summary": summary,
        "percentage_summary": percentage_summary,
        "formatted_summary": "\n".join([f"{emotion.capitalize()} : {percentage}" for emotion, percentage in percentage_summary.items()])
    })

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    transcript = data.get('transcript')

    if not transcript:
        return jsonify({"error": "No transcript provided."}), 400

    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-pro')
        print(f"Generating feedback for transcript: {transcript[:100]}...")  # Log first 100 chars

        # Prepare the prompt for feedback analysis
        prompt = f"""
        You are an AI interview coach. Analyze the following interview transcript and provide a concise feedback summary (150-200 words). Focus on:
        - Clarity and coherence of responses
        - Use of filler words
        - Confidence and tone
        - Suggestions for improvement
        Transcript: {transcript}
        """

        # Generate feedback using Gemini API
        response = model.generate_content(prompt)
        print(f"Gemini API Response: {response.text[:200]}...")  # Log first 200 chars of response

        if response.text:
            feedback_text = response.text
            return jsonify({
                "choices": [{
                    "message": {
                        "content": feedback_text
                    }
                }]
            }), 200
        else:
            return jsonify({"error": "No text returned from Gemini API."}), 500

    except Exception as e:
        print(f"Error in feedback generation: {str(e)}")
        return jsonify({"error": f"Feedback generation failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
