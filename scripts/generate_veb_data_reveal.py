# Generate calldata for VEB
# Usage:
#   ape run generate --kapi-url ... --cl-url ... --vi 1234 --vi 1235
#   or
#   poetry run python -m scripts.generate_veb_data_reveal generate --kapi-url ... --cl-url ... --vi 1234 --vi 1235

import sys

import click
from ape._cli import cli as ape_cli

from utils.cl_client import CLClient
from utils.encode_exit_requests import ValidatorExitData
from utils.exit_request import build_exit_request
from utils.kapi_client import KeysAPIClient


@click.command()
@click.option("--kapi-url", type=str, required=True)
@click.option("--cl-url", type=str, required=True)
@click.option("--vi", type=int, multiple=True, required=True)
def cli(kapi_url, cl_url, vi):
    kapi = KeysAPIClient(kapi_url)
    cl = CLClient(cl_url)
    keys_to_exit = build_exit_request(kapi, cl, vi)
    click.echo(ValidatorExitData(keys_to_exit).to_veb_calldata())


if __name__ == "__main__":
    sys.argv = ['ape', 'run', 'generate_veb_data_reveal', *sys.argv[1:]]
    ape_cli()
