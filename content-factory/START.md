# Content Factory — Запуск

## Требования
- Python 3.11+
- Node.js 18+
- Redis (для Celery queue)
- FFmpeg

## 1. Установка FFmpeg (Windows)
```
winget install ffmpeg
```
или скачать с https://ffmpeg.org/download.html и добавить в PATH

## 2. Установка Redis (Windows)
```
winget install Redis.Redis
```
или использовать WSL: `sudo apt install redis-server && redis-server`

## 3. Настройка backend

```bash
cd content-factory/backend

# Скопировать и заполнить env
cp .env.example .env
# Открыть .env и вставить API ключи

# Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate   # Windows

# Установить зависимости
pip install -r requirements.txt
```

## 4. Запуск backend

**Терминал 1 — FastAPI сервер:**
```bash
cd content-factory/backend
venv\Scripts\activate
python main.py
# Открыть: http://localhost:8000/docs
```

**Терминал 2 — Celery worker:**
```bash
cd content-factory/backend
venv\Scripts\activate
celery -A tasks worker --loglevel=info -P solo
```

## 5. Запуск frontend

```bash
cd content-factory/frontend
npm install
npm run dev
# Открыть: http://localhost:3001
```

## Минимальные API ключи для старта

Без них система не заработает:
- `OPENAI_API_KEY` — транскрипция (Whisper)
- `ANTHROPIC_API_KEY` — анализ + генерация сценариев (Claude)
- `YOUTUBE_API_KEY` — поиск вирусных на YouTube

Дополнительно (для генерации видео):
- `HEYGEN_API_KEY` — аватар-видео
- `ELEVENLABS_API_KEY` — голос
- `RUNWAY_API_KEY` — B-roll клипы

Для TikTok (опционально):
- `APIFY_API_KEY` — scraping TikTok ($5/мес)

## Архитектура пайплайна

```
[Dashboard :3001] → [FastAPI :8000] → [Celery Worker] → [Redis Queue]
                                              ↓
                          YouTube/TikTok/Reddit discovery
                                              ↓
                              yt-dlp download → storage
                                              ↓
                            Whisper transcription (99 langs)
                                              ↓
                          Claude: viral DNA extraction
                                              ↓
                         Claude: niche script generation (3 formats)
                                              ↓
                    ElevenLabs voice + HeyGen avatar + Runway B-roll
                                              ↓
                              FFmpeg: final video assembly
```
