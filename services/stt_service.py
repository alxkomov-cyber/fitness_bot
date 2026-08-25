import io
from groq import AsyncGroq
from config import config

groq_client = AsyncGroq(api_key=config.GROQ_API_KEY)

async def transcribe_voice(audio_bytes: bytes, filename: str = "voice.ogg") -> str:
    """Транскрибирует голосовое аудио в текст через Groq Whisper."""
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename
    
    transcription = await groq_client.audio.transcriptions.create(
        file=audio_file,
        model="whisper-large-v3",
        language="ru",
        response_format="text"
    )
    return str(transcription).strip()