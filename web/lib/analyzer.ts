import type { TownProfile } from "./profile";

export async function analyzePoint(
  lat: number,
  lon: number,
  radius: number
): Promise<TownProfile> {
  const resp = await fetch("/api/explore", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lon, radius }),
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(err.error || `API error: ${resp.status}`);
  }

  const { profile } = await resp.json();
  return profile;
}
