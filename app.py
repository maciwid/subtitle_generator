import streamlit as st
from dotenv import dotenv_values
from openai import OpenAI
from hashlib import md5
from pydub import AudioSegment
import tempfile
from io import BytesIO


AUDIO_TRANSCRIBE_MODEL = "whisper-1"
env = dotenv_values(".env")

def get_openai_client():
    return OpenAI(api_key=st.session_state["openai_api_key"])

def transcribe_audio(audio_bytes):
    openai_client = get_openai_client()
    audio_file = BytesIO(audio_bytes)
    audio_file.name = "audio.mp3"
    transcript = openai_client.audio.transcriptions.create(
        file=audio_file,
        model=AUDIO_TRANSCRIBE_MODEL,
        response_format="verbose_json",
    )

    return transcript.text

# OpenAI API key protection
if not st.session_state.get("openai_api_key"):
    if "OPENAI_API_KEY" in env:
        st.session_state["openai_api_key"] = env["OPENAI_API_KEY"]

    else:
        st.info("Add your OpenAI API key to use the app.")
        st.session_state["openai_api_key"] = st.text_input("Klucz API", type="password")
        if st.session_state["openai_api_key"]:
            st.rerun()

if not st.session_state.get("openai_api_key"):
    st.stop()


### MAIN

# Session state initialization
if "video_bytes_md5" not in st.session_state:
    st.session_state["video_bytes_md5"] = None

if "video_bytes" not in st.session_state:
    st.session_state["video_bytes"] = None

st.title("SUBTITLE GENERATOR")

uploaded_file = st.file_uploader("Send a file for transcription", type=["mp3", "mp4", "m4a", "wav"], key="video_file")
if uploaded_file:
    video_bytes = uploaded_file.read()
    st.video(video_bytes, format="video/mp4", width="stretch")
    
     # Placeholder for dynamic messages
    info_audio_placeholder = st.empty()
    info_audio_placeholder.info("Extracting audio, please wait...")

    # Save uploaded video to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
        temp_video_file.write(video_bytes)
        temp_video_path = temp_video_file.name

    # Convert video to audio
    audio = AudioSegment.from_file(temp_video_path, format="mp4")

      # Save audio to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
        audio.export(temp_audio_file.name, format="mp3")
        info_audio_placeholder.success("Audio was extracted.")
        st.audio(temp_audio_file.name, format="audio/mp3")
    
    info_transcribe_placeholder = st.empty()
    info_transcribe_placeholder.info("Transcribing audio, please wait... (this may take a while depending on the length of the video)")
    if st.text_area("Transcription", value=transcribe_audio(open(temp_audio_file.name, "rb").read()), height=300):
        info_transcribe_placeholder.success("Transcription completed.")
