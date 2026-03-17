"""
Script Generator — adapts viral video structure for the Marya skincare brand.
Generates 3 format variants: TikTok 60s, YouTube Shorts, Instagram Reels.
"""
import json
from anthropic import AsyncAnthropic
from config import settings


SCRIPT_PROMPT = """Ты — топ-контент-менеджер бренда "{brand_name}" (ниша: {niche}).

## О бренде:
- Тон голоса: {brand_tone}
- Целевая аудитория: {audience}
- Продукты: натуральная уходовая косметика — кремы, сыворотки, тоники, маски

## Вирусная ДНК исходного видео:
{viral_dna}

## Рекомендации по адаптации:
{adaptation_notes}

## Задача:
Напиши 3 варианта сценария для короткого видео (reels/shorts/tiktok), которые:
1. Используют ТОЧНО ту же вирусную структуру и хук что сделал оригинал популярным
2. Полностью адаптированы под нашу нишу и бренд
3. Звучат естественно, не рекламно
4. Заканчиваются мягким CTA

Верни JSON:
{{
  "tiktok_60s": {{
    "hook": "первые 3-5 слов — должны зацепить за 1 секунду",
    "script": "полный сценарий 60-90 секунд, разбитый на блоки \\n\\n[БЛОК: название]\\nтекст",
    "visual_notes": "что показывать на экране в каждый момент",
    "cta": "призыв к действию",
    "hashtags": ["#tag1", "#tag2"],
    "estimated_duration_sec": 60
  }},
  "youtube_shorts": {{
    "hook": "первые 3-5 слов",
    "script": "сценарий 45-60 секунд",
    "visual_notes": "визуальные заметки",
    "cta": "CTA",
    "hashtags": ["#tag1"],
    "estimated_duration_sec": 55
  }},
  "instagram_reels": {{
    "hook": "первые 3-5 слов",
    "script": "сценарий 30-45 секунд",
    "visual_notes": "визуальные заметки",
    "cta": "CTA",
    "hashtags": ["#tag1"],
    "estimated_duration_sec": 40
  }},
  "b_roll_ideas": ["идея 1", "идея 2", "идея 3"],
  "music_mood": "описание настроения фоновой музыки",
  "production_notes": "общие советы по съёмке/монтажу"
}}

Только JSON, без лишних комментариев."""


async def generate_niche_scripts(
    viral_dna: dict,
    adaptation_notes: dict,
    original_transcript: str = "",
) -> dict:
    """
    Generate adapted scripts for all 3 video formats based on viral DNA.
    Returns dict with tiktok_60s, youtube_shorts, instagram_reels scripts.
    """
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    prompt = SCRIPT_PROMPT.format(
        brand_name=settings.brand_name,
        niche=settings.niche_name,
        brand_tone=settings.brand_tone,
        audience=settings.niche_audience,
        viral_dna=json.dumps(viral_dna, ensure_ascii=False, indent=2),
        adaptation_notes=json.dumps(adaptation_notes, ensure_ascii=False, indent=2),
    )

    message = await client.messages.create(
        model="claude-opus-4-6",  # Use Opus for best script quality
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)


async def refine_script(script: str, feedback: str) -> str:
    """
    Refine a script based on user feedback.
    """
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": f"""Улучши этот сценарий для бренда "{settings.brand_name}":

## Текущий сценарий:
{script}

## Фидбек:
{feedback}

## Требования:
- Сохрани структуру и длину
- Тон: {settings.brand_tone}
- Верни только улучшенный сценарий без комментариев.""",
            }
        ],
    )

    return message.content[0].text.strip()


def format_script_for_display(script_dict: dict, format_type: str) -> str:
    """Format a script dict into readable text for display/export."""
    s = script_dict.get(format_type, {})
    lines = [
        f"ХOOK: {s.get('hook', '')}",
        "",
        "--- СЦЕНАРИЙ ---",
        s.get("script", ""),
        "",
        f"CTA: {s.get('cta', '')}",
        "",
        "--- ВИЗУАЛ ---",
        s.get("visual_notes", ""),
        "",
        f"Хэштеги: {' '.join(s.get('hashtags', []))}",
        f"Длительность: ~{s.get('estimated_duration_sec', '?')} сек",
    ]
    return "\n".join(lines)
