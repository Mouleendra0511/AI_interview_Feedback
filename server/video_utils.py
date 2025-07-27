import cv2
import os
import moviepy.editor as mp
import speech_recognition as sr
import uuid

def extract_frames(video_path, output_folder='frames'):
    os.makedirs(output_folder, exist_ok=True)

    vidcap = cv2.VideoCapture(video_path)
    success, image = vidcap.read()
    count = 0

    while success:
        frame_path = os.path.join(output_folder, f"frame_{count}.jpg")
        cv2.imwrite(frame_path, image)
        success, image = vidcap.read()
        count += 1

    vidcap.release()
    return count

def extract_audio(video_path, output_folder='audio'):
    os.makedirs(output_folder, exist_ok=True)

    clip = mp.VideoFileClip(video_path)
    audio_filename = f"audio_{uuid.uuid4().hex}.wav"
    audio_path = os.path.join(output_folder, audio_filename)
    clip.audio.write_audiofile(audio_path)

    return audio_path

def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        text = "Could not understand the audio."
    except sr.RequestError:
        text = "Could not request results; check internet connection."

    return text
