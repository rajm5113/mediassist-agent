"""
tools/voice.py — Voice Mode: Speech-to-Text & Text-to-Speech

🎓 HOW IT WORKS:
   STT (Speech → Text):
     - The user records audio via Streamlit's built-in `st.audio_input()` widget.
     - We send the audio bytes to Groq's Whisper Large v3 Turbo via API.
     - Whisper is OpenAI's state-of-the-art model — far more accurate than
       basic browser APIs, especially for medical terms, drug names & accents.
     - Falls back to Google's free API if the Groq key is unavailable.

   TTS (Text → Speech):
     - After the agent responds, we pass the reply text to gTTS.
     - gTTS generates an MP3 in memory (no file saved to disk).
     - `st.audio()` plays it directly in the browser.
"""

import io
import tempfile
import os
import config
from openai import OpenAI
from gtts import gTTS


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribes audio bytes to text using Groq's Whisper Large v3 Turbo.
    This is dramatically more accurate than Google's basic Web Speech API,
    especially for medical terminology, drug names, and non-native accents.

    Falls back to Google's free API if Groq key is not configured.
    Returns the transcribed string, or an empty string if it fails.
    """
    # ── PRIMARY: Groq Whisper (high accuracy, free) ──
    if config.GROQ_API_KEY:
        try:
            client = OpenAI(
                api_key=config.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )

            # Groq Whisper expects a file-like object with a filename
            # We name it .wav so the API knows the format
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"

            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                language="en",          # Specify English for better accuracy
                temperature=0.0,        # Deterministic — no creative guessing
                # This "primes" Whisper to expect medical language
                prompt="MediAssist healthcare assistant. Medical terms: ibuprofen, lisinopril, acetaminophen, symptom, severity, dosage, prescription, fever, headache, nausea."
            )
            return transcription.text.strip()

        except Exception as e:
            print(f"  [Voice] Groq Whisper failed: {e}. Falling back to Google STT...")

    # ── FALLBACK: Google Web Speech API ──
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            with sr.AudioFile(tmp_path) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio_data = recognizer.record(source)
            return recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            return f"[Speech Recognition Error: {e}]"
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        return f"[Voice Error: {e}]"


def text_to_speech(text: str) -> bytes:
    """
    Converts a text string to MP3 audio bytes using gTTS.
    Returns the raw MP3 bytes so st.audio() can play them.
    Strips markdown symbols (*, #, `) before speaking so it sounds clean.
    """
    import re

    # Clean up markdown so the TTS doesn't read "asterisk asterisk bold text asterisk asterisk"
    clean_text = re.sub(r"[*#`_>~|]", "", text)
    clean_text = re.sub(r"\n+", ". ", clean_text)  # Replace newlines with pauses
    clean_text = clean_text.strip()

    # Limit to 500 chars so TTS stays snappy and doesn't time out
    if len(clean_text) > 500:
        clean_text = clean_text[:497] + "..."

    # Generate the audio in memory (no disk I/O)
    mp3_buffer = io.BytesIO()
    tts = gTTS(text=clean_text, lang="en", slow=False)
    tts.write_to_fp(mp3_buffer)
    mp3_buffer.seek(0)

    return mp3_buffer.read()
