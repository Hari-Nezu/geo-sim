# geo-sim

店舗売上ポテンシャルシミュレータ。駅別乗降客数データと修正Huff型重力モデルを用いて、
候補地点の集客ポテンシャルと推定年間売上を算出する。

## 構成

- `src/geo_sim/data/` — データ読み込み・座標計算
- `src/geo_sim/model/` — 重力モデル・商圏分析・売上推定
- `src/geo_sim/cli.py` — CLIエントリポイント
- `data/raw/` — 入力データ (CSV/GeoJSON)
- `tests/` — pytest

## 実行

```bash
python -m geo_sim.cli simulate
python -m geo_sim.cli simulate --store-type cafe --beta 1.8 --grid-step 0.2
```

## テスト

```bash
python -m pytest tests/
```

## 対象エリア

港区・千代田区・中央区 (BBOX: 139.719-139.790, 35.626-35.703)
