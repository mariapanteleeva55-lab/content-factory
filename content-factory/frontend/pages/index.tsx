import { useState } from "react";
import Head from "next/head";
import DiscoverPanel from "../components/DiscoverPanel";
import ProcessPanel from "../components/ProcessPanel";
import ResultsPanel from "../components/ResultsPanel";

type Tab = "discover" | "process" | "results";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("discover");
  const [results, setResults] = useState<any[]>([]);

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: "discover", label: "Поиск вирусных", icon: "🔍" },
    { id: "process", label: "Обработать URL", icon: "⚡" },
    { id: "results", label: "Результаты", icon: "🎬" },
  ];

  return (
    <>
      <Head>
        <title>Content Factory — Марья</title>
        <meta name="description" content="Автоматизированный контент-завод" />
      </Head>

      <div className="min-h-screen" style={{ backgroundColor: "#fdfaf7" }}>
        {/* Header */}
        <header className="border-b border-brand-100 bg-white/70 backdrop-blur-sm sticky top-0 z-10">
          <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-brand-300 flex items-center justify-center text-white text-sm font-bold">
                М
              </div>
              <div>
                <h1 className="font-semibold text-gray-900">Content Factory</h1>
                <p className="text-xs text-gray-400">Марья • Контент-завод</p>
              </div>
            </div>
            <span className="text-xs bg-green-100 text-green-700 px-2.5 py-1 rounded-full font-medium">
              ● Онлайн
            </span>
          </div>
        </header>

        {/* Tabs */}
        <div className="max-w-6xl mx-auto px-6 pt-6">
          <div className="flex gap-1 bg-white border border-brand-100 rounded-xl p-1 w-fit">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? "bg-brand-300 text-white shadow-sm"
                    : "text-gray-500 hover:text-gray-800 hover:bg-brand-50"
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <main className="max-w-6xl mx-auto px-6 py-6">
          {activeTab === "discover" && (
            <DiscoverPanel
              onResultsFound={(videos) => {
                setResults(videos);
                setActiveTab("results");
              }}
            />
          )}
          {activeTab === "process" && <ProcessPanel />}
          {activeTab === "results" && (
            <ResultsPanel
              videos={results}
              onProcess={() => setActiveTab("process")}
            />
          )}
        </main>
      </div>
    </>
  );
}
