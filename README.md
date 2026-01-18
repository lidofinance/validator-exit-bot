# <img src="docs/logo.svg" height="70px" align="center" alt="Lido Logo"/> Validator Exit Bot

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

An automated solution to exit late Lido validators using triggerable exit requests ([EIP-7002](https://eips.ethereum.org/EIPS/eip-7002)). Contains a CLI to generate exit data for manual submission. 

## 🤖 What the Bot Does

The Validator Exit Bot is an autonomous service that:

1. **Monitors** the VEBO contract for `ExitDataProcessing` events containing exit requests
2. **Decodes** exit request data to identify validators that need to exit
3. **Checks** each validator's current status on the Consensus Layer
4. **Triggers** exits automatically for validators that missed deadlines
5. **Pays** the withdrawal request fee for each exit from the bot's account

The bot runs continuously, processing historical events on first start (configurable lookback period) and then monitoring new events in real-time.

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Poetry for dependency management
- Access to Ethereum Execution Layer RPC endpoint(s)
- Access to Consensus Layer Beacon API endpoint(s)
- Ethereum account with ETH for gas and withdrawal fees (if running in transaction mode)

### Installation

```bash
# Install dependencies using Poetry
poetry install
```

### Configuration

Create a `.env` file in the project root with the following variables:

```bash
# Required: Ethereum RPC endpoints (comma-separated for fallback)
WEB3_RPC_ENDPOINTS=https://eth-mainnet.alchemyapi.io/v2/YOUR_KEY,https://mainnet.infura.io/v3/YOUR_KEY

# Required: Consensus Layer Beacon API endpoints (comma-separated)
CL_RPC_ENDPOINTS=https://beacon-node.example.com,https://backup-beacon.example.com

# Optional: Account private key (required for sending transactions)
# Without this, the bot will run in monitoring mode only
ACCOUNT=0x1234567890abcdef...

# Optional: Module IDs to process (comma-separated, defaults to all)
MODULES_WHITELIST=1,2

# Optional: Lookback period on first start (default: 7 days)
LOOKBACK_DAYS=7

# Optional: Sleep interval between cycles (default: 384 seconds)
SLEEP_INTERVAL_SECONDS=384

# Optional: Logging level (default: INFO)
LOG_LEVEL=INFO

# Optional: Health check server port (default: 9000)
SERVER_PORT=9000

# Optional: Prometheus metrics port (default: 9090)
PROMETHEUS_PORT=9090
```

See `env.example` for a complete template.

### Running the Bot

#### Using Docker (Recommended)

```bash
# Build the Docker image
docker build -t validator-exit-bot .

# Run the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

#### Using Poetry

```bash
# Run the bot directly
poetry run python src/main.py
```

#### Using Make

```bash
# Run the bot
make run

# Run in Docker
make docker-up

# View Docker logs
make docker-logs

# Stop Docker
make docker-down
```

### Health Check & Metrics

The bot exposes two endpoints:

- **Health check**: `http://localhost:9000/health` - Returns 200 OK when the bot is running
- **Prometheus metrics**: `http://localhost:9090/metrics` - Exposes metrics including:
  - `account_balance` - Bot account balance
  - `web3_requests_total` - Total Web3 requests
  - `unexpected_exceptions_total` - Exception counter by type

## 🔧 How the Bot Works

### Architecture

The bot consists of several key components:

- **TriggerExitBot** (`src/trigger_exit_bot.py`) - Core bot logic that processes events and triggers exits
- **Main Loop** (`src/main.py`) - Entry point that initializes services and runs the bot continuously
- **Blockchain Contracts** (`src/blockchain/contracts/`) - Web3 contract interfaces for VEBO, Node Operator Registry, etc.
- **CL Client** (`src/utils/cl_client.py`) - Consensus Layer API client for checking validator status
- **Exit Data Decoder** (`src/utils/exit_data_decoder.py`) - Decodes packed validator exit data

### Workflow

```
1. Bot fetches ExitDataProcessing events from VEBO contract
   ↓
2. Decodes exit request data from transaction input
   ↓
3. Stores validator data in memory (hashed for efficiency)
   ↓
4. For each validator in state:
   a. Check if validator already exited (CL API)
   b. If exited → remove from state
   c. If not exited → check if module is whitelisted
   d. Check if exit already processed by NO
   e. If exit deadline missed → add validator to trigger exit list
   ↓
5. Build and send trigger_exits transaction with:
   - Original exit data
   - Data format
   - Indexes of validators to exit
   - Refund recipient (bot's address)
   - Withdrawal fees (auto-calculated)
   ↓
6. Sleep for configured interval and repeat
```

## 📚 Utility Scripts

In addition to the automated bot, this repository includes utility scripts for manually generating calldata for validator exit requests. These are useful for one-off exits or testing.

### Generate Calldata Script

The `scripts/generate.py` tool generates properly formatted calldata for validator exit requests.

#### Available Commands

1. **`et-hash`** - Generate Easy Track hash submit calldata
2. **`veb-data`** - Generate Validator Exit Bus data reveal calldata

#### Basic Usage

```bash
# Generate Easy Track calldata for validator exits
poetry run python -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://localhost:5052 \
  et-hash \
  --vi 123456 \
  --vi 123457

# Generate VEB data reveal calldata
poetry run python -m scripts.generate \
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
poetry run python -m scripts.generate et-hash --vi 123456
poetry run python -m scripts.generate veb-data --vi 123456
```

### Command Reference

#### Global Options

| Option       | Description             | Default                    | Environment Variable |
|--------------|-------------------------|----------------------------|----------------------|
| `--debug`    | Enable debug logging    | `false`                    | -                    |
| `--kapi-url` | Keys API URL            | `https://keys-api.lido.fi` | `KAPI_URL`           |
| `--cl-url`   | Consensus Layer API URL | `http://localhost:5052`    | `CL_URL`             |

#### et-hash Command

Generate Easy Track hash submit calldata.

**Usage:**
```bash
poetry run python -m scripts.generate et-hash --vi <VALIDATOR_INDEX> [--vi <VALIDATOR_INDEX> ...]
```

**Options:**
- `--vi` (required, multiple): Validator index on the beacon chain

**Output Format:**
- ABI-encoded array of structs: `(uint256,uint256,uint64,bytes,uint256)[]`
- Each struct contains: `(module_id, operator_id, validator_index, validator_pubkey, key_index)`

**Example:**
```bash
poetry run python -m scripts.generate et-hash --vi 123456 --vi 123457 --vi 123458
```

#### veb-data Command

Generate Validator Exit Bus data reveal calldata.

**Usage:**
```bash
poetry run python -m scripts.generate veb-data --vi <VALIDATOR_INDEX> [--vi <VALIDATOR_INDEX> ...]
```

**Options:**
- `--vi` (required, multiple): Validator index on the beacon chain

**Output Format:**
- Raw tightly-packed bytes (64 bytes per validator)
- Each entry: `module_id (3B) | operator_id (5B) | validator_index (8B) | validator_pubkey (48B)`

**Example:**
```bash
poetry run python -m scripts.generate veb-data --vi 123456 --vi 123457 --vi 123458
```

### Exit Request Structure

Each exit request contains:

| Field              | Size     | Description                            |
|--------------------|----------|----------------------------------------|
| `module_id`        | 3 bytes  | Staking module ID                      |
| `operator_id`      | 5 bytes  | Node operator ID within the module     |
| `validator_index`  | 8 bytes  | Validator index on beacon chain        |
| `validator_pubkey` | 48 bytes | BLS public key of the validator        |
| `key_index`        | -        | Key index in operator's list (ET only) |

## 📋 Examples

### Running the Bot

```bash
# Basic bot operation with minimal configuration
WEB3_RPC_ENDPOINTS=https://eth-mainnet.alchemyapi.io/v2/YOUR_KEY \
CL_RPC_ENDPOINTS=https://beacon-node.example.com \
ACCOUNT=0x1234567890abcdef... \
poetry run python -m src.main
```

Example log output:
```json
{"msg": "TriggerExitBot initialized", "level": "info", "timestamp": "2025-12-19T10:00:00"}
{"msg": "Running bot cycle", "level": "info", "timestamp": "2025-12-19T10:00:01"}
{"msg": "Starting to fetch ExitDataProcessing events", "from_block": 18000000, "to_block": 18050400, "level": "info"}
{"msg": "Successfully fetched ExitDataProcessing events", "events_count": 2, "level": "info"}
{"msg": "Processing ExitDataProcessing event", "exit_requests_hash": "0xabc123...", "block_number": 18010000, "level": "info"}
{"msg": "Validator is reported but not exited, adding to trigger list", "pubkey": "0x8f3e...", "validator_index": 123456, "level": "info"}
{"msg": "Successfully triggered exits", "validators_count": 5, "level": "info"}
{"msg": "Bot cycle completed", "events_processed": 2, "sleeping_for_seconds": 12, "level": "info"}
```

### Utility Script Examples

#### Single Validator Exit

```bash
# Generate ET calldata for one validator
poetry run python -m scripts.generate et-hash --vi 123456

# Output can be used in Etherscan or governance tools
# Copy the hex output and use it as calldata
```

#### Multiple Validator Exits

```bash
# Exit multiple validators at once
poetry run python -m scripts.generate et-hash \
  --vi 123456 \
  --vi 123457 \
  --vi 123458 \
  --vi 123459 \
  --vi 123460
```

#### Save Output to File

```bash
# Save calldata to file for later use
poetry run python -m scripts.generate et-hash --vi 123456 > calldata.txt

# Or redirect stderr to see debug info while saving output
poetry run python -m scripts.generate --debug et-hash --vi 123456 2>&1 | tee output.log
```

#### Piping to Other Tools

```bash
# Pipe output to cast (Foundry) for transaction submission
poetry run python -m scripts.generate et-hash --vi 123456 | \
  cast send 0xContractAddress "submitExitRequests(bytes)" --rpc-url $RPC_URL
```

## 🛠️ Development

### Project Structure

```
validator-exit-bot/
├── src/
│   ├── main.py                          # Bot entry point and main loop
│   ├── trigger_exit_bot.py              # Core bot logic (TriggerExitBot)
│   ├── health_server.py                 # Health check HTTP server
│   ├── variables.py                     # Configuration from environment
│   ├── blockchain/
│   │   ├── contracts/                   # Web3 contract interfaces
│   │   │   ├── validator_exit_bus_oracle.py
│   │   │   ├── node_operator_registry.py
│   │   │   ├── staking_router.py
│   │   │   └── ...
│   │   └── web3_extentions/             # Custom Web3 extensions
│   ├── utils/
│   │   ├── cl_client.py                 # Consensus Layer API client
│   │   └── exit_data_decoder.py         # Exit data decoding logic
│   └── metrics/
│       └── metrics.py                   # Prometheus metrics
├── scripts/                             # Optional utility scripts
│   ├── generate.py                      # CLI tool for generating calldata
│   ├── exit_request.py                  # Exit request builder
│   ├── encode_exit_requests.py          # Calldata encoding
│   └── kapi_client.py                   # Keys API client
├── tests/                               # Test suite
│   ├── test_exit_data_decoding.py
│   └── scripts/                         # Script tests
├── interfaces/                          # Contract ABI files
├── docker-compose.yml                   # Docker deployment
├── Dockerfile                           # Container image
├── pyproject.toml                       # Poetry dependencies
└── README.md                            # This file
```

### Testing

#### Unit Tests

Run the comprehensive unit test suite covering the bot logic, exit data decoding, and utility scripts:

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run bot-specific tests
poetry run pytest tests/test_exit_data_decoding.py -v

# Run script tests
poetry run pytest tests/scripts/ -v
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

## ⚠️ Error Handling & Troubleshooting

### Bot Errors

The bot is designed to be resilient and will continue running even if individual operations fail:

| Error/Issue                      | Cause                                                     | Solution                                                                 |
|----------------------------------|-----------------------------------------------------------|--------------------------------------------------------------------------|
| Transaction check failed         | Insufficient balance, wrong data, or contract state issue | Check account balance and withdrawal vault fee, review logs for details  |
| Failed to trigger exits          | Transaction reverted or timed out                         | Review transaction logs, ensure network connectivity, check gas settings |
| Module not in whitelist          | Validator's module ID not in `MODULES_WHITELIST`          | Update whitelist or remove restriction                                   |
| Node operator registry not found | Unknown module ID                                         | Verify the staking module exists in StakingRouter                        |
| Connection errors                | RPC endpoint unreachable                                  | Check RPC URLs, add fallback endpoints                                   |
| Unexpected exceptions            | Various runtime errors                                    | Check logs for stack trace, reported in metrics                          |

The bot logs all errors with context and continues operation. Monitor the `/metrics` endpoint for `unexpected_exceptions_total` counter.

### Utility Script Errors

When using the utility scripts:

| Error                                | Cause                                   | Solution                            |
|--------------------------------------|-----------------------------------------|-------------------------------------|
| `Validator index X not found in CL`  | Validator doesn't exist on beacon chain | Verify validator index is correct   |
| `Validator pubkey not found in KAPI` | Validator not in Lido staking modules   | Ensure validator belongs to Lido    |
| Connection errors                    | Network issues or wrong URLs            | Check URLs and network connectivity |
| No validators specified              | Missing `--vi` flag                     | Add at least one `--vi` option      |

### Monitoring

Health and metrics endpoints help monitor bot operation:

- Health check fails → Bot process has died, restart required
- `account_balance` decreasing → Bot is sending transactions (expected)
- `unexpected_exceptions_total` increasing → Review logs for issues
- No new events processed → Either no new events or RPC connectivity issue

## 🔐 Security & Operations

### Account Security

- The bot requires an Ethereum account with a private key to send transactions
- Store the private key securely (e.g., in `.env` file with proper permissions, or use a secrets manager)
- Never commit private keys to version control
- The account needs sufficient ETH for:
  - Gas fees for `trigger_exits` transactions
  - Withdrawal request fees (paid to the Withdrawal Vault)

### Recommended Setup

- Use fallback RPC endpoints for resilience
- Run with Docker for easy deployment and management
- Monitor health endpoint (`/health`) with an uptime service
- Monitor Prometheus metrics for operational insights
- Set up log aggregation for debugging
- Configure appropriate `MODULES_WHITELIST` to only process specific staking modules

### Resource Requirements

- **CPU**: Minimal (< 1 core)
- **Memory**: ~100-200 MB
- **Network**: Requires stable connection to Ethereum execution and consensus layers
- **Storage**: Negligible (in-memory state only)

### Production Considerations

- The bot is stateless (no database required)
- All validator state is kept in memory and rebuilt from events on restart
- Configure `LOOKBACK_DAYS` appropriately for first-time startup
- Use `LOG_LEVEL=INFO` for production, `DEBUG` for troubleshooting
- The bot waits for finalized blocks to ensure data consistency

## 📄 License

2026 Lido <info@lido.fi>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the [GNU General Public License](LICENSE)
along with this program. If not, see <https://www.gnu.org/licenses/>.
