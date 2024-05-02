import click


@click.group(short_help="doat CLI.")
def doat():
    """doat CLI.
    """
    pass


@doat.command()
@click.argument("name", default="doat")
def command(name):
    """Docs.
    """
    click.echo("Hello, {name}!".format(name=name))


def get_commands():
    return [doat]
