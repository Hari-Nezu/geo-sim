"""town-explorer CLIコマンド。"""

from __future__ import annotations

import typer

app = typer.Typer(help="街プロファイル探索")


@app.command()
def explore(
    lat: float = typer.Argument(..., help="緯度"),
    lon: float = typer.Argument(..., help="経度"),
    radius: int = typer.Option(800, help="探索半径 (m)"),
    offline: bool = typer.Option(False, help="オフラインモード（サンプルデータ使用）"),
):
    """指定地点の街プロファイルを生成。"""
    from geo_sim.explorer.osm_fetcher import fetch_facilities, fetch_facilities_offline
    from geo_sim.explorer.profile import build_profile
    from geo_sim.explorer.crowd_pattern import estimate_crowd_pattern

    typer.echo(f"探索中: ({lat}, {lon}) 半径{radius}m ...")

    if offline:
        facilities = fetch_facilities_offline()
        typer.echo("(オフラインモード: サンプルデータ使用)")
    else:
        try:
            facilities = fetch_facilities(lat, lon, radius)
        except Exception as e:
            typer.echo(f"OSMデータ取得失敗: {e}")
            typer.echo("--offline オプションでサンプルデータを使用できます")
            raise typer.Exit(1)

    typer.echo(f"取得施設数: {sum(facilities.values())}")
    typer.echo("")

    # プロファイル生成
    profile = build_profile(lat, lon, facilities, radius_m=radius)
    typer.echo(profile.summary())

    # 賑わいパターン
    typer.echo("")
    typer.echo("─" * 40)
    typer.echo("時間帯別の賑わい推定:")
    crowd = estimate_crowd_pattern(profile.type_scores)
    typer.echo(crowd.describe())
    typer.echo("")
    typer.echo(crowd.hourly_bar_chart())


@app.command()
def compare(
    lat1: float = typer.Argument(..., help="地点1の緯度"),
    lon1: float = typer.Argument(..., help="地点1の経度"),
    lat2: float = typer.Argument(..., help="地点2の緯度"),
    lon2: float = typer.Argument(..., help="地点2の経度"),
    radius: int = typer.Option(800, help="探索半径 (m)"),
):
    """2地点の街プロファイルを比較。"""
    from geo_sim.explorer.osm_fetcher import fetch_facilities
    from geo_sim.explorer.profile import build_profile, TOWN_TYPES
    from geo_sim.explorer.crowd_pattern import estimate_crowd_pattern

    typer.echo("2地点を比較中...")
    typer.echo("")

    profiles = []
    for i, (lat, lon) in enumerate([(lat1, lon1), (lat2, lon2)], 1):
        try:
            facilities = fetch_facilities(lat, lon, radius)
        except Exception as e:
            typer.echo(f"地点{i} OSMデータ取得失敗: {e}")
            raise typer.Exit(1)
        profiles.append(build_profile(lat, lon, facilities, radius_m=radius))

    # 比較表示
    typer.echo(f"{'項目':<12} {'地点1':<20} {'地点2':<20}")
    typer.echo("─" * 52)
    typer.echo(f"{'街タイプ':<12} {profiles[0].primary_type_label:<20} {profiles[1].primary_type_label:<20}")
    typer.echo(f"{'施設総数':<12} {sum(profiles[0].facility_counts.values()):<20} {sum(profiles[1].facility_counts.values()):<20}")

    typer.echo("")
    typer.echo("生活利便性比較:")
    all_keys = set(profiles[0].livability_scores.keys()) | set(profiles[1].livability_scores.keys())
    for key in sorted(all_keys):
        s1 = profiles[0].livability_scores.get(key, 0)
        s2 = profiles[1].livability_scores.get(key, 0)
        bar1 = "★" * int(s1) + "☆" * (5 - int(s1))
        bar2 = "★" * int(s2) + "☆" * (5 - int(s2))
        typer.echo(f"  {key:<8} {bar1}  vs  {bar2}")
