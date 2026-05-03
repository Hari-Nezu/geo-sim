# geo-sim

駅別乗降客数データと修正Huff型重力モデルを用いた、店舗売上ポテンシャルシミュレータ。

候補地点の集客ポテンシャルと推定年間売上を算出し、新規出店の立地判断を支援する。

## 対象エリア

港区・千代田区・中央区（東京都心3区）

## モデル概要

**修正Huff型重力モデル**を採用。各駅の乗降客数を需要源とし、距離減衰と競合を考慮して候補地点への流入人数を推定する。

```
P(駅iの利用者が地点jを選ぶ) = (Aj / dij^β) / Σk(Ak / dik^β)
```

- `Aj`: 地点jの魅力度
- `dij`: 駅iから地点jまでの距離 (km)
- `β`: 距離減衰パラメータ（業態別に設定）

## セットアップ

```bash
pip install -e .
```

## 使い方

```bash
# デフォルト（コンビニ業態）で実行
python -m geo_sim.cli simulate

# パラメータ指定
python -m geo_sim.cli simulate \
  --store-type cafe \
  --beta 1.8 \
  --max-distance 1.5 \
  --grid-step 0.2 \
  --top-n 20
```

### オプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--stations-csv` | `data/raw/stations_central3.csv` | 駅データCSVパス |
| `--store-type` | `convenience` | 業態 (`convenience`, `cafe`, `restaurant`, `retail`) |
| `--beta` | `2.0` | 距離減衰パラメータ |
| `--max-distance` | `2.0` | 最大影響距離 (km) |
| `--grid-step` | `0.3` | 候補グリッド間隔 (km) |
| `--top-n` | `10` | 表示する上位地点数 |

## 業態別パラメータ

| 業態 | β目安 | 来店率 | 客単価 |
|------|-------|--------|--------|
| コンビニ | 2.0 | 0.5% | ¥650 |
| カフェ | 1.8 | 0.3% | ¥580 |
| 飲食 | 1.5 | 0.2% | ¥1,100 |
| 小売 | 1.2 | 0.25% | ¥2,500 |

## データソース

- **駅別乗降客数**: [国土数値情報](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-v3_0.html) (CC BY 4.0)
- **人流メッシュ** (将来統合予定): [国土交通省 人流オープンデータ](https://www.geospatial.jp/ckan/dataset/mlit-1702)

## テスト

```bash
python -m pytest tests/
```

## ライセンス

MIT
