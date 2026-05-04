import { OVERPASS_URL, TAG_TO_CATEGORY } from "./constants";
import { buildProfile, type TownProfile } from "./profile";

export async function analyzePoint(
  lat: number,
  lon: number,
  radius: number
): Promise<TownProfile> {
  const facilities = await fetchFacilities(lat, lon, radius);
  return buildProfile(facilities);
}

async function fetchFacilities(
  lat: number,
  lon: number,
  radius: number
): Promise<Record<string, number>> {
  const query = `
[out:json][timeout:30];
(
  node(around:${radius},${lat},${lon})["amenity"];
  node(around:${radius},${lat},${lon})["shop"];
  node(around:${radius},${lat},${lon})["office"];
  node(around:${radius},${lat},${lon})["leisure"];
  node(around:${radius},${lat},${lon})["railway"="station"];
  node(around:${radius},${lat},${lon})["highway"="bus_stop"];
  way(around:${radius},${lat},${lon})["amenity"];
  way(around:${radius},${lat},${lon})["shop"];
  way(around:${radius},${lat},${lon})["office"];
  way(around:${radius},${lat},${lon})["leisure"="park"];
);
out center;`;

  const resp = await fetch(OVERPASS_URL, {
    method: "POST",
    body: "data=" + encodeURIComponent(query),
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  if (!resp.ok) {
    throw new Error(`Overpass API error: ${resp.status}`);
  }

  const data = await resp.json();

  const counts: Record<string, number> = {};
  for (const el of data.elements || []) {
    const tags: Record<string, string> = el.tags || {};
    const cats = categorize(tags);
    for (const c of cats) {
      counts[c] = (counts[c] || 0) + 1;
    }
  }
  return counts;
}

function categorize(tags: Record<string, string>): string[] {
  const results: string[] = [];
  for (const [key, cat] of Object.entries(TAG_TO_CATEGORY)) {
    const [k, v] = key.split("=");
    if (tags[k] === v) results.push(cat);
  }
  if (tags.cuisine === "ramen") results.push("ramen");
  if (results.length === 0) {
    if (tags.shop) results.push("shop");
    else if (tags.office) results.push("office");
  }
  return results;
}
