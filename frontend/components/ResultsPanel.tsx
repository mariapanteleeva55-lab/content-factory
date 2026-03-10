import { useState } from "react";

interface Video {
  id: string;
  platform: string;
  original_url: string;
  title: string;
  author: string;
  views: number;
  likes: number;
  thumbnail_url?: string;
  language?: string;
  velocity?: number;
}

interface Props {
  videos: Video[];
}

const PLATFORM_EMOJI: Record<string, string> = {
  youtube: "▶️",
  tiktok: "🎵",
  instagram: "📸",
  reddit: "🟠",
};

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

export default function ResultsPanel({ videos }: Props) {
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());
  const [taskMap, setTaskMap] = useState<Record<string, string>>({});

  const processVideo = async (video: Video) => {
    setProcessingIds((prev) => new Set([...prev, video.id]));
    try {
      const res = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          original_url: video.original_url,
          title: video.title,
          platform: video.platform,
          views: video.views,
          likes: video.likes,
        }),
      });
      const data = await res.json();
      setTaskMap((prev) => ({ ...prev, [video.id]: data.task_id }));
    } catch {
      setProcessingIds((prev) => {
        const next = new Set(prev);
        next.delete(video.id);
        return next;
      });
    }
  };

  if (videos.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-brand-100 p-12 text-center">
        <div className="text-4xl mb-3">🔍</div>
        <p className="text-gray-500 text-sm">
          Нет результатов. Запусти поиск на вкладке «Поиск вирусных».
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-900">
          Найдено вирусных видео: <span className="text-brand-400">{videos.length}</span>
        </h2>
        <span className="text-xs text-gray-400">Сортировка по velocity (просмотры/час)</span>
      </div>

      <div className="grid gap-3">
        {videos.map((video) => (
          <div
            key={video.id}
            className="bg-white rounded-2xl border border-brand-100 p-4 flex gap-4 hover:border-brand-200 transition-all"
          >
            {/* Thumbnail */}
            {video.thumbnail_url ? (
              <img
                src={video.thumbnail_url}
                alt=""
                className="w-24 h-16 object-cover rounded-xl flex-shrink-0"
              />
            ) : (
              <div className="w-24 h-16 bg-brand-50 rounded-xl flex-shrink-0 flex items-center justify-center text-2xl">
                {PLATFORM_EMOJI[video.platform] || "🎬"}
              </div>
            )}

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs">{PLATFORM_EMOJI[video.platform]}</span>
                <span className="text-xs text-gray-400 capitalize">{video.platform}</span>
                {video.language && (
                  <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">
                    {video.language.toUpperCase()}
                  </span>
                )}
              </div>
              <h3 className="text-sm font-medium text-gray-900 line-clamp-2 leading-snug">
                {video.title}
              </h3>
              <div className="flex items-center gap-3 mt-1.5">
                <span className="text-xs text-gray-400">
                  👁 {formatNumber(video.views)}
                </span>
                <span className="text-xs text-gray-400">
                  ❤️ {formatNumber(video.likes)}
                </span>
                {video.velocity && (
                  <span className="text-xs text-brand-400 font-medium">
                    ⚡ {Math.round(video.velocity).toLocaleString()} views/h
                  </span>
                )}
              </div>
            </div>

            {/* Action */}
            <div className="flex flex-col justify-center flex-shrink-0">
              {taskMap[video.id] ? (
                <a
                  href={`/?task=${taskMap[video.id]}`}
                  className="text-xs text-brand-500 hover:underline"
                >
                  Смотреть результат →
                </a>
              ) : (
                <button
                  onClick={() => processVideo(video)}
                  disabled={processingIds.has(video.id)}
                  className="bg-brand-300 hover:bg-brand-400 text-white text-xs font-semibold px-4 py-2 rounded-xl transition-all disabled:opacity-50"
                >
                  {processingIds.has(video.id) ? (
                    <span className="animate-pulse">⏳</span>
                  ) : (
                    "Обработать"
                  )}
                </button>
              )}
              <a
                href={video.original_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-gray-400 hover:text-gray-600 text-center mt-1.5"
              >
                Открыть ↗
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
