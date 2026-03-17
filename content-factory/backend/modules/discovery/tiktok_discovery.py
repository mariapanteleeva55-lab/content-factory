"""
TikTok viral video discovery via Apify TikTok Scraper.
Official TikTok Research API requires academic verification,
so we use Apify as the reliable alternative.
"""
import httpx
from config import settings


APIFY_TIKTOK_ACTOR = "clockworks/free-tiktok-scraper"

SKINCARE_HASHTAGS = [
    "skincare", "skincarecheck", "skincareroutine", "glowingskin",
    "skincaretips", "antiaging", "acneskin", "moisturizer",
    "косметика", "уходзакожей", "скинкер", "бьюти",
    "koreanskincare", "10stepskincare", "cleanbeauty",
]


async def search_viral_tiktok(
    hashtags: list[str] = SKINCARE_HASHTAGS,
    max_per_hashtag: int = 20,
    min_plays: int = 500_000,
) -> list[dict]:
    """
    Search TikTok for viral skincare videos via Apify.
    Returns list of video metadata dicts.
    """
    if not settings.apify_api_key:
        raise ValueError("APIFY_API_KEY not set — needed for TikTok scraping")

    all_videos = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=60) as client:
        for hashtag in hashtags[:8]:  # limit to avoid excessive API calls
            videos = await _scrape_hashtag(client, hashtag, max_per_hashtag)
            for v in videos:
                if v["id"] not in seen_ids and v.get("views", 0) >= min_plays:
                    seen_ids.add(v["id"])
                    all_videos.append(v)

    all_videos.sort(key=lambda x: x.get("views", 0), reverse=True)
    return all_videos


async def _scrape_hashtag(client, hashtag: str, max_results: int) -> list[dict]:
    """Run Apify TikTok scraper actor for a hashtag."""
    # Start the actor run
    run_resp = await client.post(
        f"https://api.apify.com/v2/acts/{APIFY_TIKTOK_ACTOR}/runs",
        headers={"Authorization": f"Bearer {settings.apify_api_key}"},
        json={
            "hashtags": [hashtag],
            "resultsPerPage": max_results,
            "maxProfilesPerQuery": 1,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
        },
    )
    if run_resp.status_code not in (200, 201):
        return []

    run_id = run_resp.json()["data"]["id"]

    # Wait for completion (poll)
    import asyncio
    for _ in range(30):
        await asyncio.sleep(5)
        status_resp = await client.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}",
            headers={"Authorization": f"Bearer {settings.apify_api_key}"},
        )
        if status_resp.json()["data"]["status"] in ("SUCCEEDED", "FAILED"):
            break

    if status_resp.json()["data"]["status"] != "SUCCEEDED":
        return []

    # Fetch results
    dataset_id = status_resp.json()["data"]["defaultDatasetId"]
    items_resp = await client.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items",
        headers={"Authorization": f"Bearer {settings.apify_api_key}"},
        params={"limit": max_results},
    )
    if items_resp.status_code != 200:
        return []

    return [_parse_tiktok_item(item) for item in items_resp.json()]


def _parse_tiktok_item(item: dict) -> dict:
    author = item.get("authorMeta", {})
    stats = item.get("diggCount", 0)

    return {
        "id": item.get("id", ""),
        "platform": "tiktok",
        "original_url": item.get("webVideoUrl", ""),
        "title": item.get("text", ""),
        "author": author.get("name", ""),
        "views": item.get("playCount", 0),
        "likes": item.get("diggCount", 0),
        "comments": item.get("commentCount", 0),
        "shares": item.get("shareCount", 0),
        "duration_sec": item.get("videoMeta", {}).get("duration", 0),
        "published_at": None,
        "thumbnail_url": item.get("covers", [None])[0],
        "tags": [h.get("name", "") for h in item.get("hashtags", [])],
        "language": item.get("authorMeta", {}).get("region", ""),
    }
