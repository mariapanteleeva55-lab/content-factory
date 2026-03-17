"""
Viral DNA Analyzer — extracts what made a video go viral.
Uses Claude API to analyze transcript, hook, structure, and emotional triggers.
"""
import json
from anthropic import AsyncAnthropic
from config import settings


VIRAL_DNA_PROMPT = """Ты — эксперт по вирусному контенту и контент-стратегии. Проанализируй транскрипт видео и извлеки его "вирусную ДНК" — всё, что сделало это видео вирусным.

## Исходные данные:
- Платформа: {platform}
- Название: {title}
- Просмотры: {views:,}
- Лайки: {likes:,}
- Длительность: {duration_sec} сек
- Язык оригинала: {language}
- Хук (первые 5 сек): "{hook}"

## Полный транскрипт:
{transcript}

## Твоя задача:
Верни JSON объект с полями:

{{
  "hook_analysis": {{
    "hook_text": "точная цитата первых 2-3 предложений",
    "hook_type": "вопрос | провокация | статистика | история | обещание | болевая точка | юмор",
    "hook_strength": 1-10,
    "why_it_works": "объяснение почему хук цепляет"
  }},
  "emotional_triggers": [
    {{
      "trigger": "название триггера",
      "example": "цитата из видео где это используется",
      "intensity": 1-10
    }}
  ],
  "narrative_structure": {{
    "type": "PAS | AIDA | история | список | трансформация | шок | до/после",
    "stages": ["описание каждого этапа нарратива"]
  }},
  "viral_mechanics": {{
    "shareability_reason": "почему это хочется переслать",
    "relatability": "с чем идентифицирует себя аудитория",
    "unique_angle": "что нового/неожиданного в этом видео",
    "trending_topic": "какой тренд/момент это использует"
  }},
  "content_atoms": [
    {{
      "type": "инсайт | факт | история | совет | провокация | вывод",
      "content": "суть атома",
      "virality_score": 1-10
    }}
  ],
  "pacing": {{
    "avg_sentence_length": "короткие/средние/длинные",
    "energy_level": "низкий/средний/высокий/динамичный",
    "cta_exists": true/false,
    "cta_text": "текст призыва к действию"
  }},
  "adaptability_score": 1-10,
  "key_insight": "одно предложение — главный вирусный элемент этого видео"
}}

Отвечай ТОЛЬКО валидным JSON без комментариев."""


async def extract_viral_dna(
    transcript: str,
    hook: str,
    title: str,
    platform: str,
    views: int,
    likes: int,
    duration_sec: int,
    language: str,
) -> dict:
    """
    Extract viral elements from video transcript using Claude.
    Returns structured viral DNA dict.
    """
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    prompt = VIRAL_DNA_PROMPT.format(
        platform=platform,
        title=title,
        views=views,
        likes=likes,
        duration_sec=duration_sec,
        language=language,
        hook=hook,
        transcript=transcript[:8000],  # truncate very long transcripts
    )

    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Clean up if wrapped in markdown
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)


async def score_video_for_niche(viral_dna: dict, niche: str, audience: str) -> dict:
    """
    Score how adaptable the viral video is for a specific niche.
    Returns adaptation recommendations.
    """
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    prompt = f"""Ты — контент-стратег ниши "{niche}".

## Вирусная ДНК видео:
{json.dumps(viral_dna, ensure_ascii=False, indent=2)}

## Целевая аудитория: {audience}

Оцени, насколько хорошо этот вирусный паттерн можно адаптировать под нишу.
Верни JSON:
{{
  "adaptation_score": 1-10,
  "transferable_elements": ["список элементов которые точно перенесутся"],
  "needs_change": ["что нужно заменить/переработать"],
  "niche_hook_idea": "конкретная идея хука для нашей ниши",
  "best_format": "TikTok 60s | YouTube Shorts | Instagram Reels | все",
  "recommended_angle": "описание угла подачи для нашей аудитории"
}}

Только JSON, без комментариев."""

    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)
