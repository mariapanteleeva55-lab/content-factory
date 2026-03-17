"""
Content Factory — FastAPI backend.
Full pipeline: discover → download → transcribe → analyze → script → generate video.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

from tasks import celery_app, discover_viral_videos, process_video_full_pipeline
from config import settings

app = FastAPI(
    title="Content Factory API",
    description="Automated viral content repurposing for Marya skincare brand",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Request/Response schemas
# ──────────────────────────────────────────────

class DiscoverRequest(BaseModel):
    platforms: list[str] = ["youtube", "reddit"]
    query: Optional[str] = None


class ProcessVideoRequest(BaseModel):
    original_url: str
    title: Optional[str] = ""
    platform: Optional[str] = "youtube"
    views: Optional[int] = 0
    likes: Optional[int] = 0
    duration_sec: Optional[int] = 0
    language: Optional[str] = ""


class RefineScriptRequest(BaseModel):
    script: str
    feedback: str


# ──────────────────────────────────────────────
# API Routes
# ──────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "brand": settings.brand_name}


@app.post("/api/discover")
async def discover(req: DiscoverRequest):
    """
    Launch multi-platform viral video discovery.
    Returns a Celery task ID to poll for results.
    """
    task = discover_viral_videos.delay(
        platforms=req.platforms,
        query=req.query,
    )
    return {"task_id": task.id, "status": "queued"}


@app.post("/api/process")
async def process_video(req: ProcessVideoRequest):
    """
    Launch full pipeline for a single video URL.
    Returns task_id to track progress.
    """
    video_data = {
        "id": uuid.uuid4().hex[:8],
        "original_url": req.original_url,
        "title": req.title,
        "platform": req.platform,
        "views": req.views,
        "likes": req.likes,
        "duration_sec": req.duration_sec,
        "language": req.language,
    }
    task = process_video_full_pipeline.delay(video_data)
    return {"task_id": task.id, "video_id": video_data["id"], "status": "queued"}


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Poll task status and result.
    States: PENDING → PROGRESS (stage: downloading/transcribing/analyzing/scripting/generating) → SUCCESS/FAILURE
    """
    result = celery_app.AsyncResult(task_id)

    if result.state == "PENDING":
        return {"task_id": task_id, "status": "pending"}

    elif result.state == "PROGRESS":
        return {
            "task_id": task_id,
            "status": "processing",
            "stage": result.info.get("stage", ""),
            "video_id": result.info.get("video_id", ""),
        }

    elif result.state == "SUCCESS":
        return {
            "task_id": task_id,
            "status": "completed",
            "result": result.result,
        }

    elif result.state == "FAILURE":
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(result.info),
        }

    return {"task_id": task_id, "status": result.state.lower()}


@app.post("/api/refine-script")
async def refine_script(req: RefineScriptRequest):
    """Refine a generated script based on user feedback."""
    from modules.scripting import refine_script as _refine
    improved = await _refine(req.script, req.feedback)
    return {"script": improved}


@app.post("/api/synthesize-voice")
async def synthesize_voice_endpoint(text: str, voice_id: str = None):
    """Generate voiceover audio from text."""
    from modules.generation import synthesize_voice
    audio_path = await synthesize_voice(text, voice_id=voice_id)
    return {"audio_path": audio_path}


@app.get("/api/trends")
async def get_trends(geo: str = "RU"):
    """Get rising skincare keyword trends from Google Trends."""
    from modules.discovery.trends_discovery import get_rising_skincare_keywords
    keywords = get_rising_skincare_keywords(geo=geo)
    return {"keywords": keywords}


@app.get("/api/avatars")
async def get_avatars():
    """List available HeyGen avatars."""
    from modules.generation import list_avatars
    avatars = await list_avatars()
    return {"avatars": avatars}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
