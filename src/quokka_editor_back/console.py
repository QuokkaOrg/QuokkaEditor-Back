import click
import uvicorn


@click.group()
def cli():
    pass


@cli.command()
@click.option("--debug", type=bool, default=False, is_flag=True)
def run(debug):
    uvicorn.run(
        "quokka_editor_back.app:app",
        host="0.0.0.0",
        port=8080,
        reload=debug,
    )
