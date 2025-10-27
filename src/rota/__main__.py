"""Allow running rota as a module: python -m rota"""

from .cli.main import cli

if __name__ == '__main__':
    cli()
