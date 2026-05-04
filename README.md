# geo-sim

人流データとオープンデータを活用した地理シミュレーションツール群。

1. **Town Explorer** — 街のキャラクター・生活利便性を可視化する街探索ツール
2. **店舗売上シミュレータ** — 重力モデルによる新規出店ポテンシャル推定

## Town Explorer

地図をクリックするだけで、その街の「性格」を把握できるWebツール。

- 街の類型判定（ビジネス街 / 繁華街 / ファミリー住宅街 / 単身者住宅街 / 学生街）
- 生活利便性スコア（買い物・飲食・医療・教育・公園・交通の6軸）
- 時間帯別の賑わいパターン推定

### Web版 (Next.js)

```bash
# PostgreSQL起動
docker compose up -d

# 開発サーバー起動
cd web && cp .env.example .env.local && npm install && npm run dev
```

構成: Next.js (App Router) + PostgreSQL (Overpass APIキャッシュ)

```
ブラウザ → POST /api/explore → キャッシュ検索(PostgreSQL)
                                   ├─ ヒット → 即レスポンス
                                   └─ ミス → Overpass API → DB保存 → レスポンス
```

### CLI版

```bash
# 指定地点の街プロファイル
python -m geo_sim.cli explore explore 35.6595 139.7005

# 2地点を比較
python -m geo_sim.cli explore compare 35.6595 139.7005 35.7080 139.7521

# オフラインモード（サンプルデータ）
python -m geo_sim.cli explore explore 35.6812 139.7671 --offline
```

## 店舗売上シミュレータ

修正Huff型重力モデルで候補地点の集客ポテンシャルと推定年間売上を算出する。

```
P(駅iの利用者が地点jを選ぶ) = (Aj / dij^β) / Σk(Ak / dik^β)
```

### 使い方

```bash
# デフォルト（カフェ業態）で実行
python -m geo_sim.cli simulate

# パラメータ指定
python -m geo_sim.cli simulate \
  --store-type convenience \
  --beta 2.0 \
  --max-distance 1.5 \
  --grid-step 0.2 \
  --top-n 20
```

### 業態別パラメータ

| 業態 | β目安 | 来店率 | 客単価 |
|------|-------|--------|--------|
| コンビニ | 2.0 | 0.5% | ¥650 |
| カフェ | 1.8 | 0.3% | ¥580 |
| 飲食 | 1.5 | 0.2% | ¥1,100 |
| 小売 | 1.2 | 0.25% | ¥2,500 |

## セットアップ

```bash
# インフラ
docker compose up -d

# Python CLI
pip install -e .

# Web
cd web && npm install
```

## テスト

```bash
python -m pytest tests/
```

## データソース

- **施設データ**: [OpenStreetMap](https://www.openstreetmap.org/) (Overpass API)
- **駅別乗降客数**: [国土数値情報](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-v3_0.html) (CC BY 4.0)
- **人流メッシュ** (将来統合予定): [国土交通省 人流オープンデータ](https://www.geospatial.jp/ckan/dataset/mlit-1702)

## ライセンス

MIT
