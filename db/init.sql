CREATE TABLE overpass_cache (
    id         SERIAL PRIMARY KEY,
    cache_key  TEXT UNIQUE NOT NULL,
    lat        NUMERIC(8,5) NOT NULL,
    lon        NUMERIC(9,5) NOT NULL,
    radius     INTEGER NOT NULL,
    facilities JSONB NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_cache_key ON overpass_cache(cache_key);
CREATE INDEX idx_expires ON overpass_cache(expires_at);
