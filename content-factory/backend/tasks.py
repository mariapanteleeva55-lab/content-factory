"""
Celery task queue — orchestrates the full content factory pipeline.
Each task is async-friendly and updates DB status at each stage.
"""
import asyncio
import uuid
from celery import Celery
from config import settings

celery_app = Celery(
    "content_factory",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


def _run(coro):
    """Run a coroutine in a new event loop (Celery workers are sync)."""
    return asyncio.run(coro)


@celery_app.task(bind=True, name="tasks.process_video_full_pipeline")
def process_video_full_pipeline(self, video_data: dict) -> dict:
    """
    Full pipeline: download → transcribe → analyze → script → generate video.
    video_data: {id, original_url, title, platform, views, likes, duration_sec, language}
    """
    video_id = video_data.get("id") or uuid.uuid4().hex[:8]

    try:
        # Stage 1: Download
        self.update_state(state="PROGRESS", meta={"stage": "downloading", "video_id": video_id})
        from modules.ingestion import download_video
        download_result = _run(download_video(video_data["original_url"], video_id))

        audio_path = download_result.get("audio_path")
        video_path = download_result.get("video_path")

        if not audio_path:
            raise RuntimeError("Audio extraction failed")

        # Stage 2: Transcribe
        self.update_state(state="PROGRESS", meta={"stage": "transcribing", "video_id": video_id})
        from modules.transcription import transcribe_audio, extract_timed_hooks
        transcription = _run(transcribe_audio(audio_path))
        hook = extract_timed_hooks(transcription["segments"])

        # Stage 3: Extract Viral DNA
        self.update_state(state="PROGRESS", meta={"stage": "analyzing", "video_id": video_id})
        from modules.analysis import extract_viral_dna, score_video_for_niche
        viral_dna = _run(extract_viral_dna(
            transcript=transcription["text"],
            hook=hook,
            title=video_data.get("title", ""),
            platform=video_data.get("platform", ""),
            views=video_data.get("views", 0),
            likes=video_data.get("likes", 0),
            duration_sec=video_data.get("duration_sec", 0),
            language=transcription.get("language", ""),
        ))

        adaptation_notes = _run(score_video_for_niche(
            viral_dna=viral_dna,
            niche=settings.niche_name,
            audience=settings.niche_audience,
        ))

        # Stage 4: Generate Scripts
        self.update_state(state="PROGRESS", meta={"stage": "scripting", "video_id": video_id})
        from modules.scripting import generate_niche_scripts
        scripts = _run(generate_niche_scripts(
            viral_dna=viral_dna,
            adaptation_notes=adaptation_notes,
            original_transcript=transcription["text"],
        ))

        # Stage 5: Generate Video
        self.update_state(state="PROGRESS", meta={"stage": "generating", "video_id": video_id})
        generated_video_url = _generate_video(scripts, transcription["segments"], video_id)

        return {
            "video_id": video_id,
            "status": "completed",
            "transcript": transcription["text"],
            "language": transcription["language"],
            "viral_dna": viral_dna,
            "adaptation_notes": adaptation_notes,
            "scripts": scripts,
            "generated_video_url": generated_video_url,
        }

    except Exception as exc:
        self.update_state(state="FAILURE", meta={"stage": "failed", "error": str(exc)})
        raise


def _generate_video(scripts: dict, segments: list, video_id: str) -> str | None:
    """Generate video for TikTok format (primary)."""
    tiktok_script = scripts.get("tiktok_60s", {})
    script_text = tiktok_script.get("script", "")

    if not script_text:
        return None

    try:
        from modules.generation import synthesize_voice, create_avatar_video, wait_for_video, transcript_to_srt
        import os

        # Generate voice
        voice_path = _run(synthesize_voice(script_text))

        # Generate avatar video with HeyGen
        video_result = _run(create_avatar_video(script_text))
        video_id_heygen = video_result.get("video_id")

        if not video_id_heygen:
            return None

        final = _run(wait_for_video(video_id_heygen))
        return final.get("video_url")

    except Exception:
        return None


@celery_app.task(name="tasks.discover_viral_videos")
def discover_viral_videos(platforms: list[str] = None, query: str = None) -> dict:
    """
    Run multi-platform viral video discovery.
    Returns list of discovered video metadata.
    """
    platforms = platforms or ["youtube", "reddit"]
    all_videos = []

    if "youtube" in platforms:
        from modules.discovery import search_viral_youtube
        yt_videos = _run(search_viral_youtube(query=query))
        all_videos.extend(yt_videos[:20])

    if "tiktok" in platforms:
        from modules.discovery import search_viral_tiktok
        tt_videos = _run(search_viral_tiktok())
        all_videos.extend(tt_videos[:20])

    if "reddit" in platforms:
        from modules.discovery import search_viral_reddit
        rd_videos = _run(search_viral_reddit())
        all_videos.extend(rd_videos[:10])

    return {
        "total": len(all_videos),
        "videos": all_videos,
    }
