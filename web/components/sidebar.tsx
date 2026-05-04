"use client";

import { TOWN_TYPE_LABELS } from "@/lib/constants";
import type { TownProfile } from "@/lib/profile";
import { ScoreBar } from "./score-bar";
import { HourlyChart } from "./hourly-chart";

interface SidebarProps {
  selectedPoint: { lat: number; lng: number } | null;
  radius: number;
  onRadiusChange: (r: number) => void;
  profile: TownProfile | null;
  loading: boolean;
  error: string | null;
  onAnalyze: () => void;
}

export function Sidebar({
  selectedPoint,
  radius,
  onRadiusChange,
  profile,
  loading,
  error,
  onAnalyze,
}: SidebarProps) {
  return (
    <aside className="w-[380px] border-l border-gray-200 bg-white p-5 overflow-y-auto flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-bold">Town Explorer</h1>
        <p className="text-sm text-gray-500">
          地図をクリックして街の雰囲気を調べる
        </p>
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-xs text-gray-500">探索半径</label>
        <select
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          value={radius}
          onChange={(e) => onRadiusChange(Number(e.target.value))}
        >
          <option value={400}>400m（徒歩5分）</option>
          <option value={800}>800m（徒歩10分）</option>
          <option value={1200}>1200m（徒歩15分）</option>
        </select>
        <button
          className="w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          disabled={!selectedPoint || loading}
          onClick={onAnalyze}
        >
          {loading
            ? "分析中..."
            : selectedPoint
            ? "この地点を分析する"
            : "地図をクリックしてください"}
        </button>
      </div>

      {error && (
        <p className="text-sm text-red-600">エラー: {error}</p>
      )}

      {profile && <ProfileResult profile={profile} />}

      <p className="text-xs text-gray-400 mt-auto">
        データ: OpenStreetMap Overpass API
      </p>
    </aside>
  );
}

function ProfileResult({ profile }: { profile: TownProfile }) {
  const sortedTypes = Object.entries(profile.typeScores).sort(
    (a, b) => b[1] - a[1]
  );
  const sortedFacilities = Object.entries(profile.facilities)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-sm font-medium text-gray-600">分析結果</h2>
        <p className="text-2xl font-bold text-blue-600">
          {TOWN_TYPE_LABELS[profile.primaryType]}
        </p>
        <p className="text-xs text-gray-500">
          施設数: {profile.totalFacilities}
        </p>
      </div>

      <div>
        <h3 className="text-xs font-medium text-gray-500 mb-2">
          街の類型スコア
        </h3>
        {sortedTypes.map(([type, score]) => (
          <ScoreBar
            key={type}
            label={TOWN_TYPE_LABELS[type]}
            value={score * 100}
            max={100}
            color="blue"
          />
        ))}
      </div>

      <div>
        <h3 className="text-xs font-medium text-gray-500 mb-2">生活利便性</h3>
        {Object.entries(profile.livability).map(([label, score]) => (
          <ScoreBar
            key={label}
            label={label}
            value={score}
            max={5}
            color="green"
          />
        ))}
      </div>

      <div>
        <h3 className="text-xs font-medium text-gray-500 mb-2">施設内訳</h3>
        <div className="flex flex-wrap gap-1">
          {sortedFacilities.map(([cat, count]) => (
            <span
              key={cat}
              className="inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
            >
              {cat}: {count}
            </span>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-medium text-gray-500 mb-2">
          時間帯別の賑わい推定
        </h3>
        <HourlyChart data={profile.hourly} />
      </div>
    </div>
  );
}
