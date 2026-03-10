"""
Video download pipeline using yt-dlp.
Supports YouTube, TikTok, Instagram, Reddit, VK, Twitter/X, and 1000+ other sites.
"""
import os
import asyncio
import uuid
from pathlib import Path
import yt_dlp
from config import settings


def _get_ytdlp_opts(output_dir: str, video_id: str) -> dict:
    return {
        "outtmpl": os.path.join(output_dir, f"{video_id}.%(ext)s"),
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "noplaylist": True,
        # Limit file size to 500MB
        "max_filesize": 500 * 1024 * 1024,
        # Retries
        "retries": 3,
        "fragment_retries": 3,
        # Cookies / auth workarounds for age-restricted content
        "cookiesfrombrowser": None,
        # Postprocessors: extract audio separately
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
                "nopostoverwrites": True,
            }
        ],
        # Keep original video after audio extraction
        "keepvideo": True,
    }


async def download_video(url: str, video_id: str = None) -> dict:
    """
    Download video from any supported platform URL.

    Returns:
        {
            "video_path": str,
            "audio_path": str,
            "duration_sec": int,
            "title": str,
            "ext": str,
        }

    Raises:
        Exception on download failure.
    """
    if not video_id:
        video_id = str(uuid.uuid4())[:8]

    output_dir = settings.download_dir
    os.makedirs(output_dir, exist_ok=True)

    opts = _get_ytdlp_opts(output_dir, video_id)

    # Run yt-dlp in a thread pool (it's sync)
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, _run_download, url, opts, video_id, output_dir)
    return info


def _run_download(url: str, opts: dict, video_id: str, output_dir: str) -> dict:
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    # Find downloaded files
    video_path = _find_file(output_dir, video_id, [".mp4", ".webm", ".mkv"])
    audio_path = _find_file(output_dir, video_id, [".mp3", ".m4a", ".wav"])

    return {
        "video_path": video_path,
        "audio_path": audio_path,
        "duration_sec": int(info.get("duration") or 0),
        "title": info.get("title", ""),
        "ext": info.get("ext", "mp4"),
        "uploader": info.get("uploader", ""),
        "view_count": info.get("view_count", 0),
        "like_count": info.get("like_count", 0),
    }


def _find_file(directory: str, prefix: str, extensions: list[str]) -> str | None:
    for f in Path(directory).glob(f"{prefix}*"):
        if f.suffix.lower() in extensions:
            return str(f)
    return None


async def get_video_info(url: str) -> dict:
    """Fetch video metadata without downloading."""
    loop = asyncio.get_event_loop()

    def _extract():
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            return ydl.extract_info(url, download=False)

    info = await loop.run_in_executor(None, _extract)
    return {
        "title": info.get("title", ""),
        "duration_sec": int(info.get("duration") or 0),
        "uploader": info.get("uploader", ""),
        "view_count": info.get("view_count", 0),
        "like_count": info.get("like_count", 0),
        "language": info.get("language", ""),
        "thumbnail": info.get("thumbnail", ""),
        "description": info.get("description", ""),
    }
