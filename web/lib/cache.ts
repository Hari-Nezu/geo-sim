import pool from "./db";

const TTL_DAYS = 14;

export function cacheKey(lat: number, lon: number, radius: number): string {
  return `${lat.toFixed(3)}_${lon.toFixed(3)}_${radius}`;
}

export async function getCache(
  key: string
): Promise<Record<string, number> | null> {
  const result = await pool.query(
    `SELECT facilities, fetched_at FROM overpass_cache
     WHERE cache_key = $1 AND expires_at > NOW()`,
    [key]
  );
  if (result.rows.length === 0) return null;
  return result.rows[0].facilities;
}

export async function putCache(
  key: string,
  lat: number,
  lon: number,
  radius: number,
  facilities: Record<string, number>
): Promise<void> {
  await pool.query(
    `INSERT INTO overpass_cache (cache_key, lat, lon, radius, facilities, fetched_at, expires_at)
     VALUES ($1, $2, $3, $4, $5, NOW(), NOW() + INTERVAL '${TTL_DAYS} days')
     ON CONFLICT (cache_key) DO UPDATE SET
       facilities = EXCLUDED.facilities,
       fetched_at = EXCLUDED.fetched_at,
       expires_at = EXCLUDED.expires_at`,
    [key, lat, lon, radius, JSON.stringify(facilities)]
  );
}

export async function cleanExpired(): Promise<number> {
  const result = await pool.query(
    `DELETE FROM overpass_cache WHERE expires_at < NOW()`
  );
  return result.rowCount ?? 0;
}
