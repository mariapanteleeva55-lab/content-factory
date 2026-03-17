import { useState } from "react";

const STAGES = [
  { id: "downloading", label: "Загрузка видео", icon: "⬇️" },
  { id: "transcribing", label: "Транскрипция", icon: "🎙️" },
  { id: "analyzing", label: "Анализ вирусной ДНК", icon: "🧬" },
  { id: "scripting", label: "Генерация сценария", icon: "✍️" },
  { id: "generating", label: "Создание видео", icon: "🎬" },
];

export default function ProcessPanel() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [activeScript, setActiveScript] = useState<"tiktok_60s" | "youtube_shorts" | "instagram_reels">("tiktok_60s");

  const startProcessing = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setResult(null);
    setError("");
    setCurrentStage("downloading");

    try {
      const res = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ original_url: url }),
      });
      const data = await res.json();
      pollTask(data.task_id);
    } catch {
      setError("Ошибка запуска обработки");
      setLoading(false);
    }
  };

  const pollTask = async (taskId: string) => {
    const interval = setInterval(async () => {
      const res = await fetch(`/api/task/${taskId}`);
      const data = await res.json();

      if (data.stage) setCurrentStage(data.stage);

      if (data.status === "completed") {
        clearInterval(interval);
        setLoading(false);
        setCurrentStage(null);
        setResult(data.result);
      } else if (data.status === "failed") {
        clearInterval(interval);
        setLoading(false);
        setCurrentStage(null);
        setError(data.error || "Неизвестная ошибка");
      }
    }, 3000);
  };

  const stageIndex = STAGES.findIndex((s) => s.id === currentStage);

  return (
    <div className="space-y-6">
      {/* URL input */}
      <div className="bg-white rounded-2xl border border-brand-100 p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">Обработать конкретное видео</h2>
        <p className="text-sm text-gray-500">
          Вставь ссылку на любое вирусное видео — YouTube, TikTok, Instagram, VK, Twitter/X
        </p>
        <div className="flex gap-3">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
          />
          <button
            onClick={startProcessing}
            disabled={loading || !url.trim()}
            className="bg-brand-300 hover:bg-brand-400 text-white font-semibold px-6 py-3 rounded-xl transition-all disabled:opacity-50"
          >
            {loading ? "..." : "Запустить"}
          </button>
        </div>
      </div>

      {/* Progress pipeline */}
      {loading && (
        <div className="bg-white rounded-2xl border border-brand-100 p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Прогресс обработки</h3>
          <div className="space-y-3">
            {STAGES.map((stage, idx) => {
              const isDone = idx < stageIndex;
              const isActive = stage.id === currentStage;
              return (
                <div key={stage.id} className={`flex items-center gap-3 p-3 rounded-xl transition-all ${
                  isActive ? "bg-brand-50 border border-brand-200" :
                  isDone ? "opacity-50" : "opacity-30"
                }`}>
                  <span className={`text-lg ${isActive ? "animate-pulse" : ""}`}>{stage.icon}</span>
                  <span className={`text-sm font-medium ${isActive ? "text-brand-600" : "text-gray-600"}`}>
                    {stage.label}
                  </span>
                  {isDone && <span className="ml-auto text-green-500 text-sm">✓</span>}
                  {isActive && <span className="ml-auto text-brand-400 text-xs animate-pulse">В процессе...</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-100 rounded-2xl p-4 text-sm text-red-600">
          ❌ {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Viral DNA */}
          {result.viral_dna && (
            <div className="bg-white rounded-2xl border border-brand-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-3">🧬 Вирусная ДНК</h3>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-brand-50 rounded-xl p-3">
                  <div className="text-xs text-brand-500 mb-1">Тип хука</div>
                  <div className="text-sm font-medium">{result.viral_dna.hook_analysis?.hook_type}</div>
                </div>
                <div className="bg-brand-50 rounded-xl p-3">
                  <div className="text-xs text-brand-500 mb-1">Сила хука</div>
                  <div className="text-sm font-medium">{result.viral_dna.hook_analysis?.hook_strength}/10</div>
                </div>
                <div className="bg-brand-50 rounded-xl p-3">
                  <div className="text-xs text-brand-500 mb-1">Структура</div>
                  <div className="text-sm font-medium">{result.viral_dna.narrative_structure?.type}</div>
                </div>
                <div className="bg-brand-50 rounded-xl p-3">
                  <div className="text-xs text-brand-500 mb-1">Адаптируемость</div>
                  <div className="text-sm font-medium">{result.viral_dna.adaptability_score}/10</div>
                </div>
              </div>
              <div className="bg-amber-50 border border-amber-100 rounded-xl p-3">
                <div className="text-xs text-amber-600 mb-1">Ключевой инсайт</div>
                <div className="text-sm">{result.viral_dna.key_insight}</div>
              </div>
            </div>
          )}

          {/* Scripts */}
          {result.scripts && (
            <div className="bg-white rounded-2xl border border-brand-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-3">✍️ Сценарии</h3>
              <div className="flex gap-2 mb-4">
                {[
                  { key: "tiktok_60s", label: "TikTok 60s" },
                  { key: "youtube_shorts", label: "YouTube Shorts" },
                  { key: "instagram_reels", label: "Instagram Reels" },
                ].map(({ key, label }) => (
                  <button
                    key={key}
                    onClick={() => setActiveScript(key as any)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      activeScript === key
                        ? "bg-brand-300 text-white"
                        : "bg-brand-50 text-brand-600 hover:bg-brand-100"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {result.scripts[activeScript] && (
                <div className="space-y-3">
                  <div className="bg-gray-50 rounded-xl p-3">
                    <div className="text-xs text-gray-500 mb-1">ХУК (первые секунды)</div>
                    <div className="text-sm font-semibold">{result.scripts[activeScript].hook}</div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-3 max-h-48 overflow-y-auto">
                    <div className="text-xs text-gray-500 mb-1">СЦЕНАРИЙ</div>
                    <pre className="text-sm whitespace-pre-wrap font-sans">
                      {result.scripts[activeScript].script}
                    </pre>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {result.scripts[activeScript].hashtags?.map((h: string) => (
                      <span key={h} className="text-xs bg-brand-50 text-brand-500 px-2 py-1 rounded-full">{h}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Generated video */}
          {result.generated_video_url && (
            <div className="bg-white rounded-2xl border border-brand-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-3">🎬 Готовое видео</h3>
              <video
                src={result.generated_video_url}
                controls
                className="w-full max-w-sm mx-auto rounded-xl"
              />
              <a
                href={result.generated_video_url}
                download
                className="mt-3 flex items-center justify-center gap-2 bg-brand-300 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-brand-400 transition-all"
              >
                ⬇️ Скачать видео
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
