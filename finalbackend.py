from flask import Flask, render_template, request, jsonify
import cv2
import os
import openai
import numpy as np
import speech_recognition as sr
from moviepy import *


from moviepy.editor import VideoFileClip
from gtts import gTTS
from deepface import DeepFace
import setuptools.dist 
from dotenv import load_dotenv


load_dotenv()  # Load environment variables from .env file
openai_api_key = os.getenv("OPENAI_API_KEY")
app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#  to analyze emotions from a video frame
def analyze_emotion(video_path):
    capture = cv2.VideoCapture(video_path)
    emotions = []
    
    while capture.isOpened():
        ret, frame = capture.read()
        if not ret:
            break
        try:
            analysis = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False)
            emotions.append(analysis[0]['dominant_emotion'])
        except:
            pass
    
    capture.release()
    return max(set(emotions), key=emotions.count) if emotions else "Unknown"

# to extract audio from video
def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)

# to convert speech to text
def speech_to_text(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
    return recognizer.recognize_google(audio_data)

# to simplify text
def simplify_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"Make this easy to understand: {text}"}]
    )
    return response["choices"][0]["message"]["content"]

# to generate suggested responses
def generate_responses(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"Give simple responses someone can say in a conversation after hearing this: {text}"}]
    )
    return response["choices"][0]["message"]["content"].split("\n")

# to convert text to speech
def text_to_speech(text, output_path):
    tts = gTTS(text=text, lang="en")
    tts.save(output_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_video', methods=['POST'])
def process_video():
    '''if video_path.endswith(".webm"):
    fixed_path = video_path.replace(".webm", ".mp4")
    import subprocess
    command = ['ffmpeg', '-i', video_path, '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', fixed_path]
    subprocess.run(command, check=True)
    video_path = fixed_path'''

    file = request.files['video']
    video_path = os.path.join(UPLOAD_FOLDER, file.filename)
    audio_path = video_path.replace(".mp4", ".wav")
    output_audio_path = video_path.replace(".mp4", "_output.mp3")
    file.save(video_path)
    
    emotion = analyze_emotion(video_path)
    extract_audio(video_path, audio_path)
    text = speech_to_text(audio_path)
    simplified_text = simplify_text(text)
    responses = generate_responses(simplified_text)
    text_to_speech(simplified_text, output_audio_path)
    
    return jsonify({
        "emotion": emotion,
        "original_text": text,
        "simplified_text": simplified_text,
        "responses": responses,
        "audio_output": output_audio_path
    })

if __name__ == '__main__':
    app.run(port=5001,debug=True)