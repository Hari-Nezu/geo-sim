import { NextRequest, NextResponse } from "next/server";
import { cacheKey, getCache, putCache } from "@/lib/cache";
import { fetchFacilitiesFromOverpass } from "@/lib/overpass";
import { buildProfile } from "@/lib/profile";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { lat, lon, radius } = body;

  if (typeof lat !== "number" || typeof lon !== "number") {
    return NextResponse.json(
      { error: "lat, lon are required as numbers" },
      { status: 400 }
    );
  }

  const r = typeof radius === "number" ? radius : 800;
  const key = cacheKey(lat, lon, r);

  // キャッシュ検索
  let facilities = await getCache(key);
  let cached = false;

  if (facilities) {
    cached = true;
  } else {
    // Overpass APIから取得
    try {
      facilities = await fetchFacilitiesFromOverpass(lat, lon, r);
    } catch (e) {
      return NextResponse.json(
        { error: e instanceof Error ? e.message : "Overpass API error" },
        { status: 502 }
      );
    }

    // キャッシュ保存
    await putCache(key, lat, lon, r, facilities);
  }

  const profile = buildProfile(facilities);

  return NextResponse.json({ profile, cached });
}
