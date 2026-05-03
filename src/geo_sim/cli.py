"""CLI エントリポイント。"""

from pathlib import Path

import numpy as np
import typer

from geo_sim.explorer.cli import app as explorer_app

app = typer.Typer(help="店舗売上ポテンシャルシミュレータ & 街探索ツール")
app.add_typer(explorer_app, name="explore", help="街プロファイル探索")


@app.command()
def simulate(
    stations_csv: Path = typer.Option(
        Path("data/raw/stations_central3.csv"),
        help="駅データCSVパス (station_name, lat, lon, passengers)",
    ),
    store_type: str = typer.Option("cafe", help="業態 (convenience, cafe, restaurant, retail)"),
    beta: float = typer.Option(2.0, help="距離減衰パラメータβ"),
    max_distance: float = typer.Option(2.0, help="最大影響距離 (km)"),
    grid_step: float = typer.Option(0.3, help="候補グリッド間隔 (km)"),
    top_n: int = typer.Option(10, help="表示する上位地点数"),
):
    """候補地点のポテンシャルスコアを計算し、ランキングを表示。"""
    from geo_sim.data.station_loader import load_stations_from_csv
    from geo_sim.data.geocoding import distance_matrix
    from geo_sim.model.gravity import GravityModel
    from geo_sim.model.catchment import generate_grid_candidates, CENTRAL_3WARDS_BBOX
    from geo_sim.model.sales_estimator import estimate_annual_sales

    # 駅データ読み込み
    stations = load_stations_from_csv(stations_csv)
    typer.echo(f"読み込み駅数: {len(stations)}")

    # 候補グリッド生成
    candidates = generate_grid_candidates(CENTRAL_3WARDS_BBOX, step_km=grid_step)
    typer.echo(f"候補地点数: {len(candidates)}")

    # 距離行列
    station_coords = np.array(list(zip(stations.geometry.y, stations.geometry.x)))
    dist_mat = distance_matrix(station_coords, candidates)

    # 重力モデルでスコア計算
    model = GravityModel(beta=beta, max_distance_km=max_distance)
    passengers = stations["passengers"].values.astype(float)
    inflow = model.score(dist_mat, passengers)

    # 売上推定
    annual_sales = estimate_annual_sales(inflow, store_type=store_type)

    # ランキング表示
    ranking = np.argsort(annual_sales)[::-1][:top_n]

    typer.echo(f"\n{'='*60}")
    typer.echo(f"業態: {store_type} | β={beta} | 最大距離={max_distance}km")
    typer.echo(f"{'='*60}")
    typer.echo(f"{'順位':<4} {'緯度':<10} {'経度':<11} {'日次流入':<10} {'年間売上推定':<15}")
    typer.echo(f"{'-'*60}")

    for rank, idx in enumerate(ranking, 1):
        lat, lon = candidates[idx]
        typer.echo(
            f"{rank:<4} {lat:<10.5f} {lon:<11.5f} "
            f"{inflow[idx]:<10.0f} ¥{annual_sales[idx]:>13,.0f}"
        )

    typer.echo(f"\n上位地点の座標をGoogle Mapsで確認:")
    for rank, idx in enumerate(ranking[:3], 1):
        lat, lon = candidates[idx]
        typer.echo(f"  {rank}. https://maps.google.com/maps?q={lat:.5f},{lon:.5f}")


@app.command()
def info():
    """プロジェクト情報を表示。"""
    typer.echo("geo-sim: 店舗売上ポテンシャルシミュレータ")
    typer.echo("対象エリア: 港区・千代田区・中央区")
    typer.echo("モデル: 修正Huff型重力モデル")


if __name__ == "__main__":
    app()
