from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from flask import send_from_directory
from fer import FER
import cv2
import json
from video_utils import extract_frames, extract_audio, transcribe_audio

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
FRAMES_FOLDER = 'frames'
AUDIO_FOLDER = 'audio'

# Create necessary folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FRAMES_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

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
        audio_path = extract_audio(filepath, output_folder=AUDIO_FOLDER)

        # Transcribe audio
        transcript = transcribe_audio(audio_path)

        audio_url = audio_path.replace("\\", "/")

        return jsonify({
            "message": "Video processed successfully!",
            "frames_extracted": frame_count,
            "audio_file": audio_url,
            "transcript": transcript
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
from flask import send_from_directory

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory("audio", filename)

    
@app.route('/analyze-emotions', methods=['POST'])
def analyze_emotions():
    folder_path = FRAMES_FOLDER  # use the correct folder where frames are saved
    emotions = []
    
    # Check if the folder exists
    if not os.path.exists(folder_path):
        return jsonify({"error": "Frames folder not found."}), 404

    frame_files = sorted([f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png'))])

    # Check if folder contains frames
    if not frame_files:
        return jsonify({"error": "No frame images found in folder."}), 400

    detector = FER(mtcnn=True)

    for frame in frame_files:
        frame_path = os.path.join(folder_path, frame)
        img = cv2.imread(frame_path)

        if img is None:
            emotions.append("Invalid image")
            continue
        
        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            
        result = detector.detect_emotions(img)

        if result:
            top_emotion = max(result[0]['emotions'], key=result[0]['emotions'].get)
            emotions.append(top_emotion)
        else:
            emotions.append("No face")

    # Summarize
    valid_emotions = [e for e in emotions if e not in ["No face", "Invalid image"]]
    total = len(valid_emotions)

    summary = {emotion: valid_emotions.count(emotion) for emotion in set(valid_emotions)}
    percentage_summary = {emotion: f"{(count / total) * 100:.2f}%" for emotion, count in summary.items()} if total > 0 else {}
    formatted_result = "\n".join([f"{emotion} : {percentage}" for emotion, percentage in percentage_summary.items()])

    return jsonify({
    "frame_emotions": emotions,
    "summary": summary,
    "percentage_summary": percentage_summary,
    "formatted_summary": "\n".join([f"{emotion.capitalize()} : {percentage}" for emotion, percentage in percentage_summary.items()])
})

if __name__ == '__main__':
    app.run(debug=True)
