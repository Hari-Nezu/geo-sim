"""CLI エントリポイント。"""

import typer

from geo_sim.explorer.cli import app as explorer_app

app = typer.Typer(help="街プロファイリングツール")
app.add_typer(explorer_app, name="explore", help="街プロファイル探索")


@app.command()
def info():
    """プロジェクト情報を表示。"""
    typer.echo("geo-sim: 街プロファイリングツール")
    typer.echo("地図上の任意の地点の「街の性格」を分析する")


if __name__ == "__main__":
    app()
