"""
Multilingual audio transcription using OpenAI Whisper API.
Supports 99 languages with automatic language detection.
"""
import os
import asyncio
from openai import AsyncOpenAI
from config import settings


# Max file size for Whisper API: 25MB
WHISPER_MAX_BYTES = 25 * 1024 * 1024


async def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribe audio file using OpenAI Whisper.

    Returns:
        {
            "text": str,              # full transcript
            "language": str,          # detected language code
            "segments": list[dict],   # [{start, end, text}]
            "duration_sec": float,
        }
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    file_size = os.path.getsize(audio_path)

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    if file_size <= WHISPER_MAX_BYTES:
        return await _transcribe_single(client, audio_path)
    else:
        return await _transcribe_chunked(client, audio_path)


async def _transcribe_single(client: AsyncOpenAI, audio_path: str) -> dict:
    with open(audio_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    segments = []
    if hasattr(response, "segments") and response.segments:
        segments = [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            }
            for seg in response.segments
        ]

    return {
        "text": response.text,
        "language": getattr(response, "language", "unknown"),
        "segments": segments,
        "duration_sec": segments[-1]["end"] if segments else 0,
    }


async def _transcribe_chunked(client: AsyncOpenAI, audio_path: str) -> dict:
    """
    Split large audio into 20MB chunks using ffmpeg and transcribe each chunk.
    """
    import subprocess
    import tempfile
    import json

    chunk_dir = tempfile.mkdtemp()
    chunk_pattern = os.path.join(chunk_dir, "chunk_%03d.mp3")

    # Split into 10-minute chunks
    subprocess.run([
        "ffmpeg", "-i", audio_path,
        "-f", "segment", "-segment_time", "600",
        "-c", "copy", chunk_pattern,
        "-y", "-loglevel", "error",
    ], check=True)

    chunks = sorted([
        os.path.join(chunk_dir, f)
        for f in os.listdir(chunk_dir)
        if f.startswith("chunk_")
    ])

    all_text = []
    all_segments = []
    detected_language = "unknown"
    time_offset = 0.0

    for chunk_path in chunks:
        result = await _transcribe_single(client, chunk_path)
        all_text.append(result["text"])
        detected_language = result["language"]

        for seg in result["segments"]:
            all_segments.append({
                "start": seg["start"] + time_offset,
                "end": seg["end"] + time_offset,
                "text": seg["text"],
            })

        if result["segments"]:
            time_offset += result["segments"][-1]["end"]
        else:
            time_offset += result.get("duration_sec", 0)

        os.remove(chunk_path)

    return {
        "text": " ".join(all_text),
        "language": detected_language,
        "segments": all_segments,
        "duration_sec": time_offset,
    }


def extract_timed_hooks(segments: list[dict], hook_duration_sec: float = 5.0) -> str:
    """
    Extract the hook — the first N seconds of the transcript.
    Critical for understanding why the video grabbed attention.
    """
    hook_segments = [s for s in segments if s["start"] < hook_duration_sec]
    return " ".join(s["text"] for s in hook_segments).strip()
