# geo-sim

街プロファイリングツール。地図上の任意の地点の「街の性格」を分析する。

## 構成

- `src/geo_sim/explorer/` — 街プロファイリング（OSM取得、類型判定、賑わい推定）
- `src/geo_sim/data/` — 座標計算、人流メッシュローダー
- `src/geo_sim/cli.py` — CLIエントリポイント
- `web/` — Next.js フロントエンド + APIサーバー
- `db/` — PostgreSQLスキーマ
- `destructed/` — 廃止済みモジュール（売上シミュレータ）
- `tests/` — pytest

## 実行

```bash
# CLI
python -m geo_sim.cli explore explore 35.6595 139.7005

# Web
docker compose up -d && cd web && npm run dev
```

## テスト

```bash
python -m pytest tests/
```
