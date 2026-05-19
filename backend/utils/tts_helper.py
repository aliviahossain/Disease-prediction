import io
from gtts import gTTS


def generate_tts_audio(text: str, language: str = "english") -> io.BytesIO:
    """
    Generate Text-to-Speech audio from the provided text using gTTS.

    Args:
        text (str): The text to be converted to speech.
        language (str): The language name (english, hindi, gujarati, tamil).

    Returns:
        io.BytesIO: A bytes buffer containing the generated MP3 audio.
    """
    # Map UI language names to gTTS language codes
    lang_map = {
        "english": "en",
        "hindi": "hi",
        "gujarati": "gu",
        "tamil": "ta",
    }

    lang_code = lang_map.get(language.lower(), "en")

    # Generate TTS audio
    tts = gTTS(text=text, lang=lang_code, slow=False)

    # Write to an in-memory buffer (no temp files)
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)

    return buffer
