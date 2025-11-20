# <img src="docs/logo.svg" height="70px" align="center" alt="Lido Logo"/> Validator Exit Bot

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Validator Exit Requester bot for late validators in Lido. Contains easy-to-use scripts to generate calldata for triggering validator exits through Easy Track governance and Validator Exit Bus (VEB) contract.

## 🚀 Quick Start

### Installation

```bash
# Install dependencies using Poetry
poetry install

# Verify installation
poetry run python scripts/generate.py --help
```

## 📚 Usage Guide

### Generate Calldata Script

The main tool is `scripts/generate.py`, which generates properly formatted calldata for validator exit requests.

#### Available Commands

1. **`et-hash`** - Generate Easy Track hash submit calldata
2. **`veb-data`** - Generate Validator Exit Bus data reveal calldata

#### Basic Usage

```bash
# Generate Easy Track calldata for validator exits
poetry run python scripts/generate.py \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://localhost:5052 \
  et-hash \
  --vi 123456 \
  --vi 123457

# Generate VEB data reveal calldata
poetry run python scripts/generate.py \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://localhost:5052 \
  veb-data \
  --vi 123456 \
  --vi 123457
```

#### Using Environment Variables

Set default URLs to avoid typing them each time:

```bash
export KAPI_URL=https://keys-api.lido.fi
export CL_URL=http://localhost:5052

# Now you can run commands without URL flags
poetry run python scripts/generate.py et-hash --vi 123456
poetry run python scripts/generate.py veb-data --vi 123456
```

#### Debug Mode

Enable debug output to see detailed execution steps:

```bash
poetry run python scripts/generate.py \
  --debug \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://localhost:5052 \
  et-hash \
  --vi 123456
```

Output example:
```
[DEBUG] Connected to KAPI: https://keys-api.lido.fi
[DEBUG] Connected to CL: http://localhost:5052
[DEBUG] CLI initialized successfully
[DEBUG] Generating ET hash submit for validators: (123456,)
[DEBUG] Fetching validator data from CL and KAPI...
[DEBUG] Built 1 exit requests
[DEBUG]   1. VI=123456, Module=1, Operator=42, KeyIdx=100
[DEBUG] Successfully generated ET calldata
[DEBUG] Calldata length: 324 characters (162 bytes)
0x000000000000000000000000000000000000000000000000000000000000002000000...
```

### Using with Ape Framework

If you have the Ape framework configured:

```bash
ape run generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://localhost:5052 \
  et-hash \
  --vi 123456
```

### Command Reference

#### Global Options

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `--debug` | Enable debug logging | `false` | - |
| `--kapi-url` | Keys API URL | `https://keys-api.lido.fi` | `KAPI_URL` |
| `--cl-url` | Consensus Layer API URL | `http://localhost:5052` | `CL_URL` |

#### et-hash Command

Generate Easy Track hash submit calldata.

**Usage:**
```bash
poetry run python scripts/generate.py et-hash --vi <VALIDATOR_INDEX> [--vi <VALIDATOR_INDEX> ...]
```

**Options:**
- `--vi` (required, multiple): Validator index on the beacon chain

**Output Format:**
- ABI-encoded array of structs: `(uint256,uint256,uint64,bytes,uint256)[]`
- Each struct contains: `(module_id, operator_id, validator_index, validator_pubkey, key_index)`

**Example:**
```bash
poetry run python scripts/generate.py et-hash --vi 123456 --vi 123457 --vi 123458
```

#### veb-data Command

Generate Validator Exit Bus data reveal calldata.

**Usage:**
```bash
poetry run python scripts/generate.py veb-data --vi <VALIDATOR_INDEX> [--vi <VALIDATOR_INDEX> ...]
```

**Options:**
- `--vi` (required, multiple): Validator index on the beacon chain

**Output Format:**
- Raw tightly-packed bytes (64 bytes per validator)
- Each entry: `module_id (3B) | operator_id (5B) | validator_index (8B) | validator_pubkey (48B)`

**Example:**
```bash
poetry run python scripts/generate.py veb-data --vi 123456 --vi 123457 --vi 123458
```

## 🔍 How It Works

### Data Flow

1. **Input**: Validator indexes provided via `--vi` flags
2. **Consensus Layer Query**: Fetches validator public keys from CL API
3. **Keys API Query**: Fetches Lido staking module metadata (module ID, operator ID, key index)
4. **Data Matching**: Matches validators with their metadata
5. **Sorting**: Sorts requests by (module_id, operator_id, validator_index)
6. **Encoding**: Encodes data in requested format (ET or VEB)
7. **Output**: Hex-encoded calldata to stdout

### Exit Request Structure

Each exit request contains:

| Field | Size | Description |
|-------|------|-------------|
| `module_id` | 3 bytes | Staking module ID |
| `operator_id` | 5 bytes | Node operator ID within the module |
| `validator_index` | 8 bytes | Validator index on beacon chain |
| `validator_pubkey` | 48 bytes | BLS public key of the validator |
| `key_index` | - | Key index in operator's list (ET only) |

### Format Differences

**Easy Track (et-hash):**
- ABI-encoded array of structs
- Includes `key_index` field
- Used for submitting via Easy Track governance

**VEB (veb-data):**
- Raw packed bytes (no ABI encoding)
- Does NOT include `key_index`
- 64 bytes per validator
- Used for revealing data to VEB contract

## 📋 Examples

### Single Validator Exit

```bash
# Generate ET calldata for one validator
poetry run python scripts/generate.py et-hash --vi 123456

# Output can be used in Etherscan or governance tools
# Copy the hex output and use it as calldata
```

### Multiple Validator Exits

```bash
# Exit multiple validators at once
poetry run python scripts/generate.py et-hash \
  --vi 123456 \
  --vi 123457 \
  --vi 123458 \
  --vi 123459 \
  --vi 123460
```

### Save Output to File

```bash
# Save calldata to file for later use
poetry run python scripts/generate.py et-hash --vi 123456 > calldata.txt

# Or redirect stderr to see debug info while saving output
poetry run python scripts/generate.py --debug et-hash --vi 123456 2>&1 | tee output.log
```

### Piping to Other Tools

```bash
# Pipe output to cast (Foundry) for transaction submission
poetry run python scripts/generate.py et-hash --vi 123456 | \
  cast send 0xContractAddress "submitExitRequests(bytes)" --rpc-url $RPC_URL
```

## 🛠️ Development

### Project Structure

```
validator-exit-bot/
├── scripts/
│   └── generate.py          # Main CLI tool for generating calldata
├── utils/
│   ├── cl_client.py         # Consensus Layer API client
│   ├── kapi_client.py       # Keys API client
│   ├── exit_request.py      # Exit request builder
│   ├── encode_exit_requests.py  # Calldata encoding
│   └── types.py             # Data structures
├── pyproject.toml           # Poetry dependencies
└── README.md                # This file
```

### Testing

```bash
# Test with Holesky testnet
export KAPI_URL=https://keys-api-holesky.testnet.fi
export CL_URL=https://beacon-holesky.example.com

poetry run python scripts/generate.py et-hash --vi 123456
```

## ⚠️ Error Handling

The script will fail with a clear error message if:

| Error | Cause | Solution |
|-------|-------|----------|
| `Validator index X not found in CL` | Validator doesn't exist on beacon chain | Verify validator index is correct |
| `Validator pubkey not found in KAPI` | Validator not in Lido staking modules | Ensure validator belongs to Lido |
| Connection errors | Network issues or wrong URLs | Check URLs and network connectivity |
| No validators specified | Missing `--vi` flag | Add at least one `--vi` option |

## 📞 Support

For issues or questions:
- GitHub Issues: [validator-exit-bot/issues](https://github.com/lidofinance/validator-exit-bot/issues)
- Lido Discord: [discord.lido.fi](https://discord.lido.fi)

## 📄 License

2025 Lido <info@lido.fi>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the [GNU General Public License](LICENSE)
along with this program. If not, see <https://www.gnu.org/licenses/>.

