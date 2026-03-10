"""
Reddit viral video discovery.
Searches beauty/skincare subreddits for viral video posts.
"""
import httpx
from config import settings


BEAUTY_SUBREDDITS = [
    "SkincareAddiction", "AsianBeauty", "30PlusSkinCare",
    "tretinoin", "beauty", "MakeupAddiction", "NaturalBeauty",
    "videos",
]


async def search_viral_reddit(
    subreddits: list[str] = BEAUTY_SUBREDDITS,
    time_filter: str = "week",   # hour, day, week, month, year
    max_per_sub: int = 25,
    min_upvotes: int = 500,
) -> list[dict]:
    """
    Search Reddit for viral video posts in beauty subreddits.
    Uses Reddit's public JSON API (no auth required for read-only).
    """
    all_videos = []
    seen_ids = set()

    async with httpx.AsyncClient(
        timeout=30,
        headers={"User-Agent": settings.reddit_user_agent}
    ) as client:
        for sub in subreddits:
            posts = await _get_top_videos(client, sub, time_filter, max_per_sub)
            for p in posts:
                if p["id"] not in seen_ids and p.get("likes", 0) >= min_upvotes:
                    seen_ids.add(p["id"])
                    all_videos.append(p)

    all_videos.sort(key=lambda x: x.get("likes", 0), reverse=True)
    return all_videos


async def _get_top_videos(client, subreddit: str, time_filter: str, limit: int) -> list[dict]:
    resp = await client.get(
        f"https://www.reddit.com/r/{subreddit}/top.json",
        params={"t": time_filter, "limit": limit},
    )
    if resp.status_code != 200:
        return []

    posts = resp.json().get("data", {}).get("children", [])
    results = []
    for post in posts:
        data = post.get("data", {})
        # Only include video posts
        url = data.get("url", "")
        is_video = (
            data.get("is_video", False)
            or "youtube.com" in url
            or "youtu.be" in url
            or "tiktok.com" in url
            or "v.redd.it" in url
        )
        if not is_video:
            continue

        # Resolve Reddit video URL
        if data.get("is_video"):
            media = data.get("media", {}) or {}
            reddit_video = media.get("reddit_video", {})
            video_url = reddit_video.get("fallback_url", url)
        else:
            video_url = url

        results.append({
            "id": data.get("id", ""),
            "platform": "reddit",
            "original_url": video_url,
            "title": data.get("title", ""),
            "author": data.get("author", ""),
            "views": data.get("view_count") or 0,
            "likes": data.get("ups", 0),
            "comments": data.get("num_comments", 0),
            "duration_sec": 0,
            "published_at": None,
            "thumbnail_url": data.get("thumbnail"),
            "tags": data.get("link_flair_text", ""),
            "subreddit": subreddit,
        })

    return results
