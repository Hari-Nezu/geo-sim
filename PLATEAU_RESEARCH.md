# PLATEAU 3D都市モデル 調査メモ

## 概要

国土交通省 Project PLATEAUが提供する3D都市モデル。東京23区は2025年版データが整備済み。
3D Tiles形式で配信されており、CesiumJSから直接ストリーミング読み込みが可能。

## データカタログAPI

```
GET https://api.plateauview.mlit.go.jp/datacatalog/plateau-datasets
```

全国の全データセット一覧がJSON で返る。city_code・type_en でフィルタして使う。

## 対象3区の3D Tiles URL（2025年版）

### 千代田区 (13101)

| LOD | テクスチャ | URL |
|-----|----------|-----|
| LOD1 | あり | `https://assets.cms.plateau.reearth.io/assets/3f/e07412-5455-40c0-9f64-2ac43086a209/13101_chiyoda-ku_pref_2025_citygml_1_op_bldg_3dtiles_13101_chiyoda-ku_lod1/tileset.json` |
| LOD2 | あり | `https://assets.cms.plateau.reearth.io/assets/28/07d0a1-b6be-46ef-bd87-4f0683b5ef6e/13101_chiyoda-ku_pref_2025_citygml_1_op_bldg_3dtiles_13101_chiyoda-ku_lod2/tileset.json` |
| LOD2 | なし | `https://assets.cms.plateau.reearth.io/assets/72/e900e5-938c-4376-a9de-a124b270880c/13101_chiyoda-ku_pref_2025_citygml_1_op_bldg_3dtiles_13101_chiyoda-ku_lod2_no_texture/tileset.json` |

### 中央区 (13102)

| LOD | テクスチャ | URL |
|-----|----------|-----|
| LOD1 | あり | `https://assets.cms.plateau.reearth.io/assets/cf/ccca91-acfc-4e01-b114-a56f63c2cd6b/13102_chuo-ku_pref_2025_citygml_1_op_bldg_3dtiles_13102_chuo-ku_lod1/tileset.json` |
| LOD2 | あり | `https://assets.cms.plateau.reearth.io/assets/09/83a3f6-6605-477c-84dc-a973008b5a27/13102_chuo-ku_pref_2025_citygml_1_op_bldg_3dtiles_13102_chuo-ku_lod2/tileset.json` |
| LOD2 | なし | `https://assets.cms.plateau.reearth.io/assets/92/43303e-6eb5-44ad-b65f-e21e63bdf98a/13102_chuo-ku_pref_2025_citygml_1_op_bldg_3dtiles_13102_chuo-ku_lod2_no_texture/tileset.json` |

### 港区 (13103)

| LOD | テクスチャ | URL |
|-----|----------|-----|
| LOD1 | あり | `https://assets.cms.plateau.reearth.io/assets/71/15d8f0-c4e1-4866-8df4-e66cac71c248/13103_minato-ku_pref_2025_citygml_1_op_bldg_3dtiles_13103_minato-ku_lod1/tileset.json` |
| LOD2 | あり | `https://assets.cms.plateau.reearth.io/assets/b5/b5f79e-0c6c-4fc7-adde-6522014243a2/13103_minato-ku_pref_2025_citygml_1_op_bldg_3dtiles_13103_minato-ku_lod2/tileset.json` |
| LOD2 | なし | `https://assets.cms.plateau.reearth.io/assets/c7/1aabcb-eb54-4cfe-9b75-3a6458c9d29e/13103_minato-ku_pref_2025_citygml_1_op_bldg_3dtiles_13103_minato-ku_lod2_no_texture/tileset.json` |
| LOD3 | あり | `https://assets.cms.plateau.reearth.io/assets/c7/ffcc73-1d33-434b-a49a-aa0289160814/13103_minato-ku_pref_2025_citygml_1_op_bldg_3dtiles_13103_minato-ku_lod3/tileset.json` |
| LOD3 | なし | `https://assets.cms.plateau.reearth.io/assets/cb/a78f63-b217-4460-8f0c-b329c840ed2b/13103_minato-ku_pref_2025_citygml_1_op_bldg_3dtiles_13103_minato-ku_lod3_no_texture/tileset.json` |

## LOD（Level of Detail）の違い

| LOD | 内容 | 用途 |
|-----|------|------|
| LOD1 | 建物フットプリント + 一律高さの箱型 | 軽量、広域表示向き |
| LOD2 | 屋根形状あり、壁面テクスチャ対応 | 中距離〜近距離のビュー |
| LOD3 | 窓・入口など外装の詳細形状 | クローズアップ向き（港区のみ） |

## CesiumJSでの読み込みサンプル

```javascript
import { Viewer, Cesium3DTileset, Cartesian3, Math as CesiumMath } from "cesium";

const viewer = new Viewer("cesiumContainer", {
  terrain: Cesium.Terrain.fromWorldTerrain(),
});

// 千代田区 LOD2（テクスチャ付き）
const tileset = await Cesium3DTileset.fromUrl(
  "https://assets.cms.plateau.reearth.io/assets/28/07d0a1-b6be-46ef-bd87-4f0683b5ef6e/13101_chiyoda-ku_pref_2025_citygml_1_op_bldg_3dtiles_13101_chiyoda-ku_lod2/tileset.json"
);
viewer.scene.primitives.add(tileset);

// 東京駅付近にカメラ移動
viewer.camera.flyTo({
  destination: Cartesian3.fromDegrees(139.7671, 35.6812, 800),
  orientation: {
    heading: CesiumMath.toRadians(0),
    pitch: CesiumMath.toRadians(-45),
    roll: 0,
  },
});
```

## React (Next.js) での利用

`resium` パッケージがCesiumJSのReactバインディングを提供:

```bash
npm install cesium resium
```

```tsx
import { Viewer, Cesium3DTileset } from "resium";

<Viewer>
  <Cesium3DTileset url="https://assets.cms.plateau.reearth.io/assets/..." />
</Viewer>
```

注意: CesiumJSはバンドルサイズが大きい（数十MB）。Next.jsでは `dynamic(() => import(...), { ssr: false })` でクライアントのみ読み込む。

## 街プロファイルとの統合案

1. **3Dビル表示** — PLATEAUの3D Tilesで建物を表示
2. **施設カテゴリ色分け** — Overpass APIで取得した施設データの位置にマーカーやヒートマップをオーバーレイ
3. **賑わいヒートマップ** — 人流メッシュデータを地表面にヒートマップとして重ねる
4. **飛行モード** — CesiumJSの`flyTo`でエリア間をスムーズに移動

## ライセンス

- **CC BY 4.0**（クリエイティブ・コモンズ 表示 4.0 国際）
- 商用利用可
- クレジット表記: 「出典: 国土交通省 Project PLATEAU」

## 参考リンク

- PLATEAU公式: https://www.mlit.go.jp/plateau/
- PLATEAU VIEW: https://plateauview.mlit.go.jp/
- GitHub: https://github.com/Project-PLATEAU
- 配信チュートリアル: https://github.com/Project-PLATEAU/plateau-streaming-tutorial
- データカタログAPI: https://api.plateauview.mlit.go.jp/datacatalog/plateau-datasets
