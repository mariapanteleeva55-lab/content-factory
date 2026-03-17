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
    "natural skincare", "натуральная косметика", "уход за лицом",
    "lifestyle beauty", "self care routine", "утренний уход",
    "вечерний уход", "organic skincare", "чистая кожа",
    "омоложение", "увлажнение кожи", "glow skin",
]

# Слова которые должны быть в заголовке/тегах чтобы видео прошло фильтр
RELEVANCE_KEYWORDS = [
    "skin", "face", "beauty", "skincare", "cream", "serum", "routine",
    "косметик", "уход", "кожа", "лицо", "крем", "маска", "тоник",
    "lifestyle", "self care", "glow", "natural", "organic",
    "макияж", "makeup", "moisture", "антивозраст", "anti age",
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

    # Фильтр по релевантности — оставляем только видео про косметику/уход
    all_videos = [v for v in all_videos if _is_relevant(v)]

    # Получаем количество подписчиков для расчёта вирусности
    async with httpx.AsyncClient(timeout=30) as client:
        channel_ids = list({v["channel_id"] for v in all_videos if v.get("channel_id")})
        subscribers = await _get_channel_subscribers(client, base_url, channel_ids)

    # Считаем метрики вирусности
    for v in all_videos:
        age_hours = max(1, _hours_since(v.get("published_at")))
        views = v.get("views", 0)
        subs = subscribers.get(v.get("channel_id", ""), 1)

        # Скорость набора просмотров
        v["velocity"] = views / age_hours
        # Вирусный коэффициент: во сколько раз просмотры превышают подписчиков
        v["viral_ratio"] = round(views / max(subs, 1), 2)
        v["subscribers"] = subs

    # Фильтр: оставляем только те где просмотры хотя бы в 0.5 раза больше подписчиков
    all_videos = [v for v in all_videos if v.get("viral_ratio", 0) >= 0.5]

    # Сортируем по вирусному коэффициенту
    all_videos.sort(key=lambda x: x["viral_ratio"], reverse=True)
    return all_videos[:50]  # возвращаем топ-50


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
            "channel_id": snippet.get("channelId", ""),
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


def _is_relevant(video: dict) -> bool:
    """Проверяет что видео относится к красоте/уходу/лайфстайлу."""
    title = (video.get("title") or "").lower()
    tags = " ".join(video.get("tags") or []).lower()
    text = f"{title} {tags}"
    return any(kw.lower() in text for kw in RELEVANCE_KEYWORDS)


async def _get_channel_subscribers(client, base_url, channel_ids: list) -> dict:
    """Возвращает словарь {channel_id: subscribers}."""
    if not channel_ids:
        return {}
    result = {}
    # Запрашиваем по 50 каналов за раз
    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i:i+50]
        resp = await client.get(f"{base_url}/channels", params={
            "part": "statistics",
            "id": ",".join(batch),
            "key": settings.youtube_api_key,
        })
        if resp.status_code != 200:
            continue
        for item in resp.json().get("items", []):
            subs = int(item.get("statistics", {}).get("subscriberCount", 0))
            result[item["id"]] = subs
    return result


def _pick_keyword() -> str:
    import random
    return random.choice(BEAUTY_KEYWORDS)
