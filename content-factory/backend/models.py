from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Enum as SAEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class VideoStatus(str, enum.Enum):
    discovered = "discovered"
    downloading = "downloading"
    downloaded = "downloaded"
    transcribing = "transcribing"
    analyzing = "analyzing"
    scripting = "scripting"
    generating = "generating"
    completed = "completed"
    failed = "failed"


class DiscoveredVideo(Base):
    __tablename__ = "discovered_videos"

    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)           # youtube / tiktok / instagram / reddit
    original_url = Column(String, nullable=False)
    title = Column(String)
    author = Column(String)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    duration_sec = Column(Integer, default=0)
    language = Column(String)
    published_at = Column(DateTime)
    thumbnail_url = Column(String)
    tags = Column(JSON, default=list)

    # Processing
    status = Column(SAEnum(VideoStatus), default=VideoStatus.discovered)
    local_path = Column(String)
    audio_path = Column(String)
    storage_url = Column(String)

    # Analysis results
    transcript = Column(Text)
    viral_dna = Column(JSON)                            # extracted viral elements
    adapted_script = Column(JSON)                       # {tiktok, shorts, reels} versions
    generated_video_url = Column(String)

    error_message = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SearchSession(Base):
    __tablename__ = "search_sessions"

    id = Column(String, primary_key=True)
    query = Column(String)
    platforms = Column(JSON)
    niche = Column(String)
    total_found = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    status = Column(String, default="running")
    created_at = Column(DateTime, server_default=func.now())
