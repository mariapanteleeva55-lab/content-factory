import { useState } from "react";

const PLATFORMS = [
  { id: "youtube", label: "YouTube", emoji: "▶️" },
  { id: "tiktok", label: "TikTok", emoji: "🎵" },
  { id: "reddit", label: "Reddit", emoji: "🟠" },
];

interface Props {
  onResultsFound: (videos: any[]) => void;
}

export default function DiscoverPanel({ onResultsFound }: Props) {
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(["youtube", "reddit"]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState("");

  const togglePlatform = (id: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const startDiscovery = async () => {
    if (selectedPlatforms.length === 0) return;
    setLoading(true);
    setStatus("Запускаем поиск...");

    try {
      const res = await fetch("/api/discover", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platforms: selectedPlatforms, query: query || null }),
      });
      const data = await res.json();
      setTaskId(data.task_id);
      pollTask(data.task_id);
    } catch {
      setStatus("Ошибка запуска");
      setLoading(false);
    }
  };

  const pollTask = async (id: string) => {
    const interval = setInterval(async () => {
      const res = await fetch(`/api/task/${id}`);
      const data = await res.json();

      if (data.status === "completed") {
        clearInterval(interval);
        setLoading(false);
        const videos = data.result?.videos || [];
        setStatus(`Найдено ${videos.length} видео`);
        onResultsFound(videos);
      } else if (data.status === "failed") {
        clearInterval(interval);
        setLoading(false);
        setStatus(`Ошибка: ${data.error}`);
      } else {
        setStatus("Ищем вирусные видео по всему интернету...");
      }
    }, 3000);
  };

  return (
    <div className="space-y-6">
      {/* Description */}
      <div className="bg-white rounded-2xl border border-brand-100 p-6">
        <h2 className="font-semibold text-gray-900 mb-1">Trench Watching</h2>
        <p className="text-sm text-gray-500">
          Ищем вирусные видео по всему интернету, анализируем что залетело и адаптируем под бренд Марья
        </p>
      </div>

      {/* Platform selection */}
      <div className="bg-white rounded-2xl border border-brand-100 p-6 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700">Платформы</h3>
        <div className="flex gap-3 flex-wrap">
          {PLATFORMS.map((p) => (
            <button
              key={p.id}
              onClick={() => togglePlatform(p.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium transition-all ${
                selectedPlatforms.includes(p.id)
                  ? "border-brand-300 bg-brand-50 text-brand-600"
                  : "border-gray-200 text-gray-500 hover:border-brand-200"
              }`}
            >
              <span>{p.emoji}</span>
              {p.label}
            </button>
          ))}
        </div>

        {/* Optional keyword */}
        <div>
          <label className="text-xs text-gray-500 block mb-1.5">Ключевое слово (опционально)</label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="skincare routine, тоник для лица..."
            className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
          />
        </div>

        <button
          onClick={startDiscovery}
          disabled={loading || selectedPlatforms.length === 0}
          className="w-full bg-brand-300 hover:bg-brand-400 text-white font-semibold py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⏳</span> {status}
            </span>
          ) : (
            "Найти вирусные видео"
          )}
        </button>
      </div>

      {/* How it works */}
      <div className="bg-brand-50 rounded-2xl border border-brand-100 p-6">
        <h3 className="text-sm font-semibold text-brand-600 mb-3">Как работает пайплайн</h3>
        <div className="space-y-2">
          {[
            ["🔍", "Поиск", "Скачиваем список топ-вирусных видео по платформам и регионам"],
            ["⬇️", "Загрузка", "yt-dlp скачивает видео и аудио (1000+ сайтов)"],
            ["🎙️", "Транскрипция", "OpenAI Whisper переводит речь в текст (99 языков)"],
            ["🧬", "ДНК анализ", "Claude выявляет хуки, триггеры и структуру нарратива"],
            ["✍️", "Сценарий", "Генерируем 3 варианта под TikTok, Shorts, Reels"],
            ["🎬", "Видео", "HeyGen + ElevenLabs создают готовое видео"],
          ].map(([emoji, title, desc]) => (
            <div key={title as string} className="flex items-start gap-3">
              <span className="text-lg">{emoji}</span>
              <div>
                <span className="text-xs font-semibold text-brand-600">{title}</span>
                <span className="text-xs text-gray-500 ml-1.5">{desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
