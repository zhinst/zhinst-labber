import click

@click.group()
def main():
    """Fancy zhinst-labber cli script"""

@main.command(help="generate driver")
@click.argument(
    "name",
    required=True,
    type=str,
)
def generate(name):
    print(f"TODO: generate driver for {name}")
