"""
AI Avatar video generation via HeyGen API.
Creates talking-head videos from script + voice.
"""
import asyncio
import httpx
from config import settings


HEYGEN_BASE = "https://api.heygen.com"

# HeyGen avatar IDs — browse at app.heygen.com
# These are example IDs; replace with actual avatars from your account
DEFAULT_AVATARS = {
    "woman_professional": "Angela-insuit-20220820",
    "woman_casual": "Kayla-incasualsuit-20220818",
    "woman_beauty": "Monica-ingreendress-20230313",
}


async def create_avatar_video(
    script: str,
    voice_audio_url: str = None,
    avatar_id: str = None,
    background_color: str = "#F5F0EB",  # warm cream — matches Marya brand
    caption: bool = True,
) -> dict:
    """
    Create an AI avatar video using HeyGen.
    Can use either HeyGen's built-in TTS or a custom ElevenLabs audio URL.

    Returns:
        {"video_id": str, "status": "processing"}
    """
    if not settings.heygen_api_key:
        raise ValueError("HEYGEN_API_KEY not set")

    avatar_id = avatar_id or DEFAULT_AVATARS["woman_beauty"]

    # Build voice config
    if voice_audio_url:
        voice = {"type": "audio", "audio_url": voice_audio_url}
    else:
        # Use HeyGen's multilingual TTS
        voice = {
            "type": "text",
            "input_text": script,
            "voice_id": "ru-RU-SvetlanaNeural",  # Russian female TTS
        }

    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": voice,
                "background": {
                    "type": "color",
                    "value": background_color,
                },
            }
        ],
        "dimension": {"width": 1080, "height": 1920},  # vertical 9:16
        "caption": caption,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{HEYGEN_BASE}/v2/video/generate",
            headers={
                "X-Api-Key": settings.heygen_api_key,
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()

    data = resp.json().get("data", {})
    return {
        "video_id": data.get("video_id"),
        "status": "processing",
    }


async def wait_for_video(video_id: str, max_wait_sec: int = 300) -> dict:
    """
    Poll HeyGen until video is ready or timeout.

    Returns:
        {"video_url": str, "thumbnail_url": str, "duration": float}
    """
    async with httpx.AsyncClient(timeout=30) as client:
        for _ in range(max_wait_sec // 10):
            await asyncio.sleep(10)

            resp = await client.get(
                f"{HEYGEN_BASE}/v1/video_status.get",
                headers={"X-Api-Key": settings.heygen_api_key},
                params={"video_id": video_id},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            status = data.get("status")

            if status == "completed":
                return {
                    "video_url": data.get("video_url"),
                    "thumbnail_url": data.get("thumbnail_url"),
                    "duration": data.get("duration"),
                    "status": "completed",
                }
            elif status == "failed":
                raise RuntimeError(f"HeyGen video generation failed: {data.get('error')}")

    raise TimeoutError(f"HeyGen video {video_id} not ready after {max_wait_sec}s")


async def list_avatars() -> list[dict]:
    """List all available avatars in your HeyGen account."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{HEYGEN_BASE}/v2/avatars",
            headers={"X-Api-Key": settings.heygen_api_key},
        )
        resp.raise_for_status()
    return resp.json().get("data", {}).get("avatars", [])
