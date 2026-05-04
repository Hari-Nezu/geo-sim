"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { Sidebar } from "@/components/sidebar";
import type { TownProfile } from "@/lib/profile";

const MapView = dynamic(() => import("@/components/map-view"), { ssr: false });

export default function Home() {
  const [selectedPoint, setSelectedPoint] = useState<{
    lat: number;
    lng: number;
  } | null>(null);
  const [radius, setRadius] = useState(800);
  const [profile, setProfile] = useState<TownProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="flex h-full">
      <div className="flex-1">
        <MapView
          selectedPoint={selectedPoint}
          radius={radius}
          onPointSelect={setSelectedPoint}
        />
      </div>
      <Sidebar
        selectedPoint={selectedPoint}
        radius={radius}
        onRadiusChange={setRadius}
        profile={profile}
        loading={loading}
        error={error}
        onAnalyze={async () => {
          if (!selectedPoint) return;
          setLoading(true);
          setError(null);
          setProfile(null);
          try {
            const { analyzePoint } = await import("@/lib/analyzer");
            const result = await analyzePoint(
              selectedPoint.lat,
              selectedPoint.lng,
              radius
            );
            setProfile(result);
          } catch (e) {
            setError(e instanceof Error ? e.message : "不明なエラー");
          } finally {
            setLoading(false);
          }
        }}
      />
    </div>
  );
}
