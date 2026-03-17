from .youtube_discovery import search_viral_youtube
from .tiktok_discovery import search_viral_tiktok
from .reddit_discovery import search_viral_reddit
from .trends_discovery import get_trending_topics_for_search

__all__ = [
    "search_viral_youtube",
    "search_viral_tiktok",
    "search_viral_reddit",
    "get_trending_topics_for_search",
]
