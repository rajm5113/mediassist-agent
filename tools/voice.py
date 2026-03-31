"""
tools/voice.py — Voice Mode: Speech-to-Text & Text-to-Speech

🎓 HOW IT WORKS:
   STT (Speech → Text):
     - The user records audio via Streamlit's built-in `st.audio_input()` widget.
     - We save the bytes to a temp WAV file.
     - Google's free Speech Recognition API transcribes it to text.
     - That text is sent to the agent exactly like a typed message.

   TTS (Text → Speech):
     - After the agent responds, we pass the reply text to gTTS (Google Text-to-Speech).
     - gTTS generates an MP3 in memory (no file saved to disk).
     - `st.audio()` plays it directly in the browser with an auto-play flag.
"""

import io
import tempfile
import os
import speech_recognition as sr
from gtts import gTTS


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Takes raw audio bytes from st.audio_input() and transcribes them to text.
    Uses Google's free Web Speech API (no API key required for basic use).
    Returns the transcribed string, or an empty string if it fails.
    """
    recognizer = sr.Recognizer()

    # We need to save the audio to a temp WAV file because SpeechRecognition
    # can't read raw bytes directly — it needs a file object.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with sr.AudioFile(tmp_path) as source:
            # Adjust for ambient noise to improve accuracy
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio_data = recognizer.record(source)

        # Use Google's free speech recognition
        text = recognizer.recognize_google(audio_data)
        return text

    except sr.UnknownValueError:
        # Audio was too quiet or unclear
        return ""
    except sr.RequestError as e:
        # Couldn't reach Google's servers
        return f"[Speech Recognition Error: {e}]"
    finally:
        # Always clean up the temp file
        os.unlink(tmp_path)


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
