# audio_setup.py
import os
from pydub import AudioSegment

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IS_STREAMLIT_CLOUD = os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud"

if IS_STREAMLIT_CLOUD:
    # Linux (Streamlit Cloud)
    AudioSegment.converter = os.path.join(BASE_DIR, "ffmpeg", "ffmpeg")
    AudioSegment.ffmpeg = AudioSegment.converter
    AudioSegment.ffprobe = os.path.join(BASE_DIR, "ffmpeg", "ffprobe")
else:
    # Local dev (macOS / Linux)
    AudioSegment.converter = "ffmpeg"
    AudioSegment.ffmpeg = "ffmpeg"
    AudioSegment.ffprobe = "ffprobe"