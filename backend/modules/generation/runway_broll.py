"""
B-roll video generation via Runway ML Gen-3 API.
Generates cinematic product/lifestyle shots for video assembly.
"""
import asyncio
import httpx
from config import settings


RUNWAY_BASE = "https://api.dev.runwayml.com/v1"

# Cinematic prompts for Marya skincare brand
BROLL_PROMPT_TEMPLATES = {
    "product_closeup": (
        "Cinematic close-up of a glass skincare bottle with golden serum, "
        "soft morning light, bokeh background, luxury beauty aesthetic, "
        "4K, warm tones, slow motion"
    ),
    "skin_texture": (
        "Macro shot of glowing healthy skin, woman applying moisturizer, "
        "soft natural daylight, warm skincare aesthetic, smooth motion"
    ),
    "ritual": (
        "Woman doing morning skincare routine by a window, peaceful atmosphere, "
        "golden hour light, natural beauty, slow cinematic pan"
    ),
    "ingredients": (
        "Flat lay of natural skincare ingredients: roses, aloe vera, hyaluronic drops, "
        "white background, luxury beauty editorial, camera slowly zooming"
    ),
    "before_after": (
        "Split screen before and after skincare transformation, "
        "glowing radiant skin, clean beauty aesthetic, warm tones"
    ),
}


async def generate_broll(
    prompt: str = None,
    scene_type: str = "product_closeup",
    duration_sec: int = 5,
    resolution: str = "1080p",
) -> dict:
    """
    Generate a B-roll clip using Runway Gen-3.

    Returns:
        {"task_id": str, "status": "processing"}
    """
    if not settings.runway_api_key:
        raise ValueError("RUNWAY_API_KEY not set")

    text_prompt = prompt or BROLL_PROMPT_TEMPLATES.get(scene_type, BROLL_PROMPT_TEMPLATES["product_closeup"])

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{RUNWAY_BASE}/image_to_video",
            headers={
                "Authorization": f"Bearer {settings.runway_api_key}",
                "Content-Type": "application/json",
                "X-Runway-Version": "2024-11-06",
            },
            json={
                "promptText": text_prompt,
                "model": "gen3a_turbo",
                "duration": duration_sec,
                "ratio": "720:1280",  # 9:16 vertical
                "watermark": False,
            },
        )
        resp.raise_for_status()

    data = resp.json()
    return {
        "task_id": data.get("id"),
        "status": "processing",
    }


async def wait_for_broll(task_id: str, max_wait_sec: int = 300) -> str:
    """
    Poll Runway until the clip is ready.
    Returns the video URL.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        for _ in range(max_wait_sec // 10):
            await asyncio.sleep(10)

            resp = await client.get(
                f"{RUNWAY_BASE}/tasks/{task_id}",
                headers={
                    "Authorization": f"Bearer {settings.runway_api_key}",
                    "X-Runway-Version": "2024-11-06",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")

            if status == "SUCCEEDED":
                output = data.get("output", [])
                return output[0] if output else None
            elif status == "FAILED":
                raise RuntimeError(f"Runway task failed: {data.get('failure')}")

    raise TimeoutError(f"Runway task {task_id} not ready after {max_wait_sec}s")


async def generate_multiple_broll(scene_types: list[str]) -> list[dict]:
    """Generate multiple B-roll clips in parallel."""
    tasks = [generate_broll(scene_type=st) for st in scene_types]
    return await asyncio.gather(*tasks)
