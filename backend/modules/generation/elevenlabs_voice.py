"""
Voice synthesis via ElevenLabs API.
Generates natural Russian/English voiceover from script text.
"""
import os
import httpx
import asyncio
from config import settings


# ElevenLabs voice IDs — recommended for Russian content
# You can browse voices at: https://elevenlabs.io/voice-library
VOICES = {
    "ru_female_warm": "21m00Tcm4TlvDq8ikWAM",     # Rachel — warm female
    "ru_female_news": "AZnzlk1XvdvUeBnXmlld",      # Domi — clear female
    "ru_male_calm": "VR6AewLTigWG4xSOukaG",         # Arnold — calm male
    "en_female": "EXAVITQu4vr4xnSDxMaL",            # Bella
}

DEFAULT_VOICE = "ru_female_warm"

ELEVEN_BASE = "https://api.elevenlabs.io/v1"


async def synthesize_voice(
    text: str,
    voice_id: str = None,
    output_path: str = None,
    stability: float = 0.5,
    similarity_boost: float = 0.8,
    style: float = 0.3,
) -> str:
    """
    Convert script text to speech using ElevenLabs.

    Args:
        text: Script text (max ~5000 chars per request)
        voice_id: ElevenLabs voice ID, defaults to warm female Russian voice
        output_path: Where to save the .mp3 file

    Returns:
        Path to generated audio file.
    """
    if not settings.elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY not set")

    voice_id = voice_id or VOICES[DEFAULT_VOICE]

    if not output_path:
        os.makedirs(settings.output_dir, exist_ok=True)
        import uuid
        output_path = os.path.join(settings.output_dir, f"voice_{uuid.uuid4().hex[:8]}.mp3")

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{ELEVEN_BASE}/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": settings.elevenlabs_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": True,
                },
            },
        )
        resp.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(resp.content)

    return output_path


async def get_available_voices() -> list[dict]:
    """Fetch available voices from ElevenLabs account."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{ELEVEN_BASE}/voices",
            headers={"xi-api-key": settings.elevenlabs_api_key},
        )
        resp.raise_for_status()
    return resp.json().get("voices", [])
