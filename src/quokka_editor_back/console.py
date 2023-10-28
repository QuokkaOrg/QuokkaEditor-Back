import click
import uvicorn


@click.group()
def cli():
    pass


@cli.command()
def run():
    from quokka_editor_back.settings import LOGGING, settings

    uvicorn.run(
        "quokka_editor_back.app:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug,
        log_config=LOGGING,
    )
