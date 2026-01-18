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


def generate_subtitles(audio):
    openai_client = get_openai_client()
    audio_file = BytesIO(audio)
    audio_file.name = "audio.mp3"
    transcript = openai_client.audio.transcriptions.create(
        file=audio_file,
        model=AUDIO_TRANSCRIBE_MODEL,
        response_format="srt",
    )

    return transcript


def transcribe_audio(audio_bytes):
    openai_client = get_openai_client()
    audio_file = BytesIO(audio_bytes)
    audio_file.name = "audio.mp3"
    transcript = openai_client.audio.transcriptions.create(
        file=audio_file,
        model=AUDIO_TRANSCRIBE_MODEL,
        response_format="verbose_json",
    )
    return transcript

def get_sentences(transcript):
    sentences = []

    for segment in transcript.segments:
        sentences.append({
            "start": float(segment.start),
            "end": float(segment.end),
            "text": segment.text.strip()
        })

    return sentences



def sentences_to_text(sentences):
    lines = []
    for s in sentences:
        # Convert start and end times to minutes and seconds
        start_minutes, start_seconds = divmod(int(s['start']), 60)
        end_minutes, end_seconds = divmod(int(s['end']), 60)

        # Format the time as MM:SS
        lines.append(
            f"[{start_minutes:02d}:{start_seconds:02d} – {end_minutes:02d}:{end_seconds:02d}] {s['text']}"
        )
    return "\n".join(lines)


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

if "audio_file_path" not in st.session_state:
    st.session_state["audio_file_path"] = None

if "video_bytes" not in st.session_state:
    st.session_state["video_bytes"] = None

if "transcript" not in st.session_state:
    st.session_state["transcript"] = None

if "edtitable_text" not in st.session_state:
    st.session_state["edtitable_text"] = None

st.title("SUBTITLE GENERATOR")

uploaded_file = st.file_uploader("Send a file for transcription", type=["mp3", "mp4", "m4a", "wav", "mov"], key="video_file")
if uploaded_file:
    file_extension = uploaded_file.name.split(".")[-1].lower()  # Get file extension
    file_bytes = uploaded_file.read()
    video_bytes = uploaded_file.read()
    # video_bytes_md5 = md5(video_bytes).hexdigest()
    # Placeholder for dynamic messages
    info_audio_placeholder = st.empty()
    if file_extension in ["mp3", "wav", "m4a"]:  # Check if the file is audio
        st.session_state["audio_file_path"] = None
        st.audio(file_bytes, format=f"audio/{file_extension}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_audio_file:
            temp_audio_file.write(file_bytes)
            st.session_state["audio_file_path"] = temp_audio_file.name
        st.success("Audio file uploaded successfully. Ready for transcription.")
    
    
    # to do: use md5 hash to optimize
    elif file_extension in ["mp4", "mov"]:  # Check if the file is video
        st.video(file_bytes, format="video/mp4", width="stretch")
        if file_bytes != st.session_state["video_bytes"]:
            st.session_state["video_bytes"] = file_bytes
            # Save uploaded video to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
                temp_video_file.write(video_bytes)
                temp_video_path = temp_video_file.name
            info_audio_placeholder.info("Extracting audio, please wait...")
            # Convert video to audio
            audio = AudioSegment.from_file(temp_video_path, format="mp4")
            st.session_state["audio"] = audio
            # Save audio to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
                audio.export(temp_audio_file.name, format="mp3")
                st.session_state["audio_file_path"] = temp_audio_file.name  
                info_audio_placeholder.success("Audio was extracted.")
                st.audio(temp_audio_file.name, format="audio/mp3")

        else:
            info_audio_placeholder.success("Audio was extracted.")
            st.audio(st.session_state["audio_file_path"], format="audio/mp3")
        
    srt = st.toggle("Subtitle format (.srt)", value=False, key="srt_format")
    info_transcribe_placeholder = st.empty()
    if st.button("Start Transcription"):
        info_transcribe_placeholder.info("Transcribing audio, please wait... (this may take a while depending on the length of the audio)")
        if srt:
            text_value = generate_subtitles(open(st.session_state["audio_file_path"], "rb").read())
        else:    
            text_value = transcribe_audio(open(st.session_state["audio_file_path"], "rb").read()) 
        st.session_state["transcript"] = text_value

    if st.session_state["transcript"]:
        info_transcribe_placeholder.success("Transcription completed.")
        if srt:
            st.session_state["edtitable_text"] = st.session_state["transcript"]
            st.text_area(
                "Transcription", 
                value=st.session_state["transcript"], 
                height=300, 
                key="subtitles"
            )
        else:
            sentences = get_sentences(st.session_state["transcript"])
            st.session_state["edtitable_text"] = sentences_to_text(sentences)
            edited_text = st.text_area(
                "Transkrypcja (edytowalna)",
                value=st.session_state["edtitable_text"],
                height=400,
                key="editable_text"
            )   
        
        # Determine the download button parameters based on the subtitle format
        if srt:
            download_label = "Download as .srt file"
            file_name = "transcription.srt"
        else:
            download_label = "Download as .txt file"
            file_name = "transcription.txt"

        # Create the download button
        st.download_button(
            label=download_label, 
            data=st.session_state["edtitable_text"], 
            file_name=file_name, 
            mime="text/plain"
        )

   
