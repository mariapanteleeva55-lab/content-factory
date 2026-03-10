"""
Google Trends discovery — finds rising skincare keywords.
Uses pytrends (unofficial Google Trends API).
"""
from pytrends.request import TrendReq
from typing import Optional


SEED_KEYWORDS = [
    "skincare routine", "face serum", "moisturizer", "retinol",
    "vitamin c serum", "hyaluronic acid", "toner", "face mask",
    "уход за кожей", "крем для лица", "сыворотка для лица",
]


def get_rising_skincare_keywords(
    seed: Optional[list[str]] = None,
    geo: str = "",          # "" = worldwide, "RU" = Russia
    timeframe: str = "now 7-d",
) -> list[dict]:
    """
    Returns list of rising search keywords related to skincare.
    Each item: {"keyword": str, "value": int, "rising": bool}
    """
    pytrends = TrendReq(hl="en-US", tz=360)
    keywords = seed or SEED_KEYWORDS

    # Build payload for 5 keywords at a time (Google Trends limit)
    results = []
    for i in range(0, len(keywords), 5):
        chunk = keywords[i:i+5]
        try:
            pytrends.build_payload(chunk, timeframe=timeframe, geo=geo)
            related = pytrends.related_queries()
            for kw in chunk:
                rising_df = related.get(kw, {}).get("rising")
                if rising_df is not None and not rising_df.empty:
                    for _, row in rising_df.head(5).iterrows():
                        results.append({
                            "keyword": row["query"],
                            "value": int(row["value"]),
                            "rising": True,
                            "seed": kw,
                        })
        except Exception:
            continue

    results.sort(key=lambda x: x["value"], reverse=True)
    return results


def get_trending_topics_for_search() -> list[str]:
    """
    Returns top trending search queries to use in YouTube/TikTok discovery.
    """
    rising = get_rising_skincare_keywords()
    return [r["keyword"] for r in rising[:10]]
