import click

from .utils import create_env
from .handle_message_sent import GroupMessageSentEvent


@click.group()
def main():
    pass


@click.command()
def run():
    create_env()
    from .bot import run

    run()


main.add_command(run)
