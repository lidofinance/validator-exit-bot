#!/usr/bin/env python3
"""
Validator Exit Request Calldata Generator

This script generates calldata for validator exit requests in two formats:
1. Easy Track (ET) hash submit - for submitting exit request hashes via Easy Track governance
2. Validator Exit Bus (VEB) data reveal - for revealing exit request data to the VEB contract

The script fetches validator information from:
- Consensus Layer (CL) client: For validator indexes and public keys
- Keys API (KAPI): For Lido staking module metadata (module_id, operator_id, key_index)

Usage Examples:
---------------

1. Generate Easy Track hash submit calldata:
   poetry run python scripts/generate.py --kapi-url https://keys-api.lido.fi --cl-url http://localhost:5052 et-hash --vi 123456 --vi 123457

2. Generate VEB data reveal calldata:
   poetry run python scripts/generate.py --kapi-url https://keys-api.lido.fi --cl-url http://localhost:5052 veb-data --vi 123456 --vi 123457

3. With debug output:
   poetry run python scripts/generate.py --debug --kapi-url https://keys-api.lido.fi --cl-url http://localhost:5052 et-hash --vi 123456

4. Using with Ape:
   ape run generate --kapi-url https://keys-api.lido.fi --cl-url http://localhost:5052 et-hash --vi 123456

Environment Variables (optional):
----------------------------------
You can set default URLs via environment variables:
- KAPI_URL: Default Keys API URL (default: https://keys-api.lido.fi)
- CL_URL: Default Consensus Layer URL (default: http://localhost:5052)

Example:
   export KAPI_URL=https://keys-api.lido.fi
   export CL_URL=http://localhost:5052
   poetry run python scripts/generate.py et-hash --vi 123456

Process Flow:
-------------
1. Script connects to the Consensus Layer client to fetch validator data
2. Script connects to Keys API to fetch Lido staking module metadata
3. For each validator index provided:
   - Fetches validator public key from CL
   - Matches public key with KAPI data to get module_id, operator_id, and key_index
   - Builds an exit request structure
4. Sorts all exit requests by (module_id, operator_id, validator_index)
5. Encodes the data in the requested format (ET or VEB)
6. Outputs the hex-encoded calldata to stdout

Output Format:
--------------
The script outputs hex-encoded calldata that can be:
- Copied directly into Etherscan for contract interaction
- Used in governance proposals
- Passed to other scripts or tools for transaction submission

Exit Request Structure:
-----------------------
Each exit request contains:
- module_id: Staking module ID (3 bytes)
- operator_id: Node operator ID (5 bytes)
- validator_index: Validator index on beacon chain (8 bytes)
- validator_pubkey: BLS public key (48 bytes)
- key_index: Index in the operator's key list (for ET only)

Error Handling:
---------------
The script will fail with an error message if:
- Validator index is not found in CL
- Validator public key is not found in KAPI
- Network connection fails
- Invalid URLs are provided
"""

import sys
from pathlib import Path

# Add parent directory to Python path to import utils
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import click

from scripts.exit_request import build_exit_request
from scripts.kapi_client import KeysAPIClient
from scripts.encode_exit_requests import ValidatorExitData
from src.utils.cl_client import CLClient


class AppContext:
    """
    Application context shared across CLI commands.

    Attributes:
        debug: Enable debug logging
        kapi: Keys API client instance
        cl_client: Consensus Layer client instance
    """

    def __init__(self, debug: bool, kapi_url: str, cl_url: str):
        self.debug = debug
        self.kapi = KeysAPIClient(kapi_url)
        self.cl_client = CLClient(cl_url)
        self.log(f"Connected to KAPI: {kapi_url}")
        self.log(f"Connected to CL: {cl_url}")

    def log(self, msg: str) -> None:
        """Print debug message if debug mode is enabled."""
        if self.debug:
            click.secho(f"[DEBUG] {msg}", fg="yellow")


@click.group()
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Enable debug logging to see detailed execution steps",
)
@click.option(
    "--kapi-url",
    type=str,
    envvar="KAPI_URL",
    default="https://keys-api.lido.fi",
    help="Keys API URL (default: https://keys-api.lido.fi, or KAPI_URL env var)",
)
@click.option(
    "--cl-url",
    type=str,
    envvar="CL_URL",
    default="http://localhost:5052",
    help="Consensus Layer (Beacon) API URL (default: http://localhost:5052, or CL_URL env var)",
)
@click.pass_context
def cli(ctx, debug: bool, kapi_url: str, cl_url: str):
    """
    Generate validator exit request calldata for Lido protocol.

    This tool helps create properly formatted calldata for validator exits
    through Easy Track governance or Validator Exit Bus contract.

    Use 'poetry run python scripts/generate.py COMMAND --help' for command-specific help.
    """
    try:
        ctx.obj = AppContext(debug=debug, kapi_url=kapi_url, cl_url=cl_url)
        ctx.obj.log("CLI initialized successfully")
    except Exception as e:
        click.secho(f"Error initializing CLI: {e}", fg="red", err=True)
        sys.exit(1)


@cli.command(name="et-hash")
@click.option(
    "--vi",
    type=int,
    multiple=True,
    required=True,
    help="Validator index to include in exit request (can be specified multiple times: --vi 123 --vi 456)",
)
@click.pass_context
def et_hash(ctx, vi: list[int]):
    """
    Generate Easy Track hash submit calldata.

    This command generates ABI-encoded calldata for submitting validator exit
    request hashes via Easy Track governance mechanism.

    The output format matches: SubmitExitRequestHashesUtils.ExitRequestInput[] memory

    Each request includes:
    - module_id (uint256): Staking module ID
    - operator_id (uint256): Node operator ID
    - validator_index (uint64): Beacon chain validator index
    - validator_pubkey (bytes): 48-byte BLS public key
    - key_index (uint256): Index in operator's key list

    Example:
        poetry run python scripts/generate.py et-hash --vi 123456 --vi 123457

    Output:
        Hex-encoded ABI calldata suitable for Easy Track submission
    """
    try:
        ctx.obj.log(f"Generating ET hash submit for validators: {vi}")
        ctx.obj.log("Fetching validator data from CL and KAPI...")

        keys_to_exit = build_exit_request(ctx.obj.kapi, ctx.obj.cl_client, vi)

        ctx.obj.log(f"Built {len(keys_to_exit)} exit requests")
        if ctx.obj.debug:
            for i, key in enumerate(keys_to_exit, 1):
                ctx.obj.log(
                    f"  {i}. VI={key.validator_index}, "
                    f"Module={key.module_id}, "
                    f"Operator={key.no_id}, "
                    f"KeyIdx={key.pub_key_index}"
                )

        validator_exit_data = ValidatorExitData(keys_to_exit)
        calldata = validator_exit_data.to_et_calldata()

        ctx.obj.log("Successfully generated ET calldata")
        ctx.obj.log(
            f"Calldata length: {len(calldata)} characters ({len(calldata)//2} bytes)"
        )

        # Output the result (this is the main output - don't add prefixes)
        click.echo(calldata)

    except ValueError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"Unexpected error: {e}", fg="red", err=True)
        if ctx.obj.debug:
            import traceback

            click.secho(traceback.format_exc(), fg="red", err=True)
        sys.exit(1)


@cli.command(name="veb-data")
@click.option(
    "--vi",
    type=int,
    multiple=True,
    required=True,
    help="Validator index to include in exit request (can be specified multiple times: --vi 123 --vi 456)",
)
@click.pass_context
def veb_data(ctx, vi: list[int]):
    """
    Generate Validator Exit Bus (VEB) data reveal calldata.

    This command generates raw bytes calldata for revealing validator exit
    request data to the Validator Exit Bus contract.

    The output format is tightly packed bytes (NO ABI encoding) with structure:

    For each validator (64 bytes total):
    - module_id (3 bytes): Staking module ID
    - operator_id (5 bytes): Node operator ID
    - validator_index (8 bytes): Beacon chain validator index
    - validator_pubkey (48 bytes): BLS public key

    Note: This format does NOT include key_index (unlike ET format)

    The data is sorted by (module_id, operator_id, validator_index) as required
    by the VEB contract specification.

    Example:
        poetry run python scripts/generate.py veb-data --vi 123456 --vi 123457

    Output:
        Hex-encoded raw bytes data suitable for VEB data reveal
    """
    try:
        ctx.obj.log(f"Generating VEB data reveal for validators: {vi}")
        ctx.obj.log("Fetching validator data from CL and KAPI...")

        keys_to_exit = build_exit_request(ctx.obj.kapi, ctx.obj.cl_client, vi)

        ctx.obj.log(f"Built {len(keys_to_exit)} exit requests")
        if ctx.obj.debug:
            for i, key in enumerate(keys_to_exit, 1):
                ctx.obj.log(
                    f"  {i}. VI={key.validator_index}, "
                    f"Module={key.module_id}, "
                    f"Operator={key.no_id}"
                )

        validator_exit_data = ValidatorExitData(keys_to_exit)
        calldata = validator_exit_data.to_veb_calldata()

        ctx.obj.log("Successfully generated VEB calldata")
        ctx.obj.log(
            f"Calldata length: {len(calldata)} characters ({len(calldata)//2} bytes)"
        )
        ctx.obj.log(f"Number of validators: {(len(calldata)//2) // 64}")

        # Output the result (this is the main output - don't add prefixes)
        click.echo(calldata)

    except ValueError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"Unexpected error: {e}", fg="red", err=True)
        if ctx.obj.debug:
            import traceback

            click.secho(traceback.format_exc(), fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
