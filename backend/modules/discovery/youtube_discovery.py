"""
YouTube viral video discovery via YouTube Data API v3.
Finds trending videos across 99+ regions and categories.
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional
from config import settings


BEAUTY_CATEGORY_ID = "26"   # Howto & Style
ENTERTAINMENT_CATEGORY_ID = "24"

# ISO 3166-1 alpha-2 region codes to scan
REGIONS = [
    "US", "RU", "GB", "DE", "FR", "IN", "BR", "KR", "JP", "ID",
    "TR", "MX", "IT", "ES", "PL", "UA", "NL", "SA", "AE", "TH",
]

BEAUTY_KEYWORDS = [
    "skincare routine", "skin care", "косметика", "уход за кожей",
    "серум", "serum", "moisturizer", "toner", "face mask",
    "beauty routine", "glowing skin", "anti aging", "acne",
    "тоник", "маска для лица", "крем для лица",
]


async def search_viral_youtube(
    query: Optional[str] = None,
    regions: list[str] = REGIONS,
    max_per_region: int = 10,
    min_views: int = 100_000,
) -> list[dict]:
    """
    Search YouTube for viral beauty/skincare videos across multiple regions.
    Returns list of video metadata dicts.
    """
    if not settings.youtube_api_key:
        raise ValueError("YOUTUBE_API_KEY not set")

    base_url = "https://www.googleapis.com/youtube/v3"
    all_videos = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for region in regions:
            # 1. Trending videos in this region
            trending = await _get_trending(client, base_url, region, max_per_region)
            for v in trending:
                if v["id"] not in seen_ids and v.get("views", 0) >= min_views:
                    seen_ids.add(v["id"])
                    all_videos.append(v)

            # 2. Search by keywords in this region
            search_query = query or _pick_keyword()
            search_results = await _search_videos(
                client, base_url, search_query, region, max_per_region
            )
            for v in search_results:
                if v["id"] not in seen_ids and v.get("views", 0) >= min_views:
                    seen_ids.add(v["id"])
                    all_videos.append(v)

    # Sort by engagement velocity (views / age in hours)
    for v in all_videos:
        age_hours = max(1, _hours_since(v.get("published_at")))
        v["velocity"] = v.get("views", 0) / age_hours

    all_videos.sort(key=lambda x: x["velocity"], reverse=True)
    return all_videos


async def _get_trending(client, base_url, region, max_results) -> list[dict]:
    resp = await client.get(f"{base_url}/videos", params={
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "regionCode": region,
        "videoCategoryId": BEAUTY_CATEGORY_ID,
        "maxResults": max_results,
        "key": settings.youtube_api_key,
    })
    if resp.status_code != 200:
        return []
    return _parse_videos(resp.json().get("items", []), region)


async def _search_videos(client, base_url, query, region, max_results) -> list[dict]:
    # First get video IDs from search
    search_resp = await client.get(f"{base_url}/search", params={
        "part": "snippet",
        "q": query,
        "type": "video",
        "regionCode": region,
        "order": "viewCount",
        "publishedAfter": (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z",
        "maxResults": max_results,
        "key": settings.youtube_api_key,
    })
    if search_resp.status_code != 200:
        return []

    ids = [item["id"]["videoId"] for item in search_resp.json().get("items", [])]
    if not ids:
        return []

    # Then fetch full stats for those IDs
    stats_resp = await client.get(f"{base_url}/videos", params={
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(ids),
        "key": settings.youtube_api_key,
    })
    if stats_resp.status_code != 200:
        return []

    return _parse_videos(stats_resp.json().get("items", []), region)


def _parse_videos(items: list, region: str) -> list[dict]:
    results = []
    for item in items:
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})
        content = item.get("contentDetails", {})

        results.append({
            "id": item["id"],
            "platform": "youtube",
            "original_url": f"https://www.youtube.com/watch?v={item['id']}",
            "title": snippet.get("title", ""),
            "author": snippet.get("channelTitle", ""),
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "language": snippet.get("defaultAudioLanguage", ""),
            "published_at": snippet.get("publishedAt"),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            "tags": snippet.get("tags", []),
            "region": region,
            "duration": content.get("duration", ""),
        })
    return results


def _hours_since(published_at: Optional[str]) -> float:
    if not published_at:
        return 168  # assume 1 week old
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        delta = datetime.now(dt.tzinfo) - dt
        return max(1.0, delta.total_seconds() / 3600)
    except Exception:
        return 168


def _pick_keyword() -> str:
    import random
    return random.choice(BEAUTY_KEYWORDS)
