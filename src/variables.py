import os
from typing import Optional

import structlog
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3

from src.logging_setup import LOG_LEVEL, masker
from src.utils.build_info import load_build_info
from src.utils.env import from_file_or_env, split_endpoints

logger = structlog.get_logger(__name__)

# EL node
WEB3_RPC_ENDPOINTS = split_endpoints(from_file_or_env("WEB3_RPC_ENDPOINTS"))

# Consensus Layer Beacon Node URLs, used in this order
CONSENSUS_CLIENT_URL = split_endpoints(from_file_or_env("CONSENSUS_CLIENT_URL"))

# Account private key
WALLET_PRIVATE_KEY = from_file_or_env("WALLET_PRIVATE_KEY")

PRIVATE_ENV_VARS = {
    "WEB3_RPC_ENDPOINTS": WEB3_RPC_ENDPOINTS,
    "CONSENSUS_CLIENT_URL": CONSENSUS_CLIENT_URL,
    "WALLET_PRIVATE_KEY": WALLET_PRIVATE_KEY,
}

# Before the first log line of this module: every later line, an import error included, is masked.
masker.add(PRIVATE_ENV_VARS)

BUILD_INFO = load_build_info()

LIDO_LOCATOR = Web3.to_checksum_address(
    os.getenv("LIDO_LOCATOR", "0xC1d0b3DE6792Bf6b4b37EccdcC24e45978Cfd2Eb")
)

ACCOUNT: Optional[LocalAccount] = None
if WALLET_PRIVATE_KEY:
    account = Account.from_key(WALLET_PRIVATE_KEY)
    logger.info({"msg": "Load account from private key.", "value": account.address})
    ACCOUNT = account
else:
    logger.warning({"msg": "Account not provided. Run in dry mode."})

# Transactions settings
DRY_RUN = os.getenv("DRY_RUN") == "true"

MIN_PRIORITY_FEE = Web3.to_wei(*os.getenv("MIN_PRIORITY_FEE", "50 mwei").split(" "))
MAX_PRIORITY_FEE = Web3.to_wei(*os.getenv("MAX_PRIORITY_FEE", "1 gwei").split(" "))

MAX_GAS_FEE = Web3.to_wei(*os.getenv("MAX_GAS_FEE", "10 gwei").split(" "))
CONTRACT_GAS_LIMIT = int(os.getenv("CONTRACT_GAS_LIMIT", 15 * 10**6))

# Curated module strategy
GAS_FEE_PERCENTILE_1: int = int(os.getenv("GAS_FEE_PERCENTILE_1", 15))
GAS_FEE_PERCENTILE_DAYS_HISTORY_1: int = int(
    os.getenv("GAS_FEE_PERCENTILE_DAYS_HISTORY_1", 1)
)

GAS_PRIORITY_FEE_PERCENTILE = int(os.getenv("GAS_PRIORITY_FEE_PERCENTILE", 25))

MAX_BUFFERED_ETHERS = Web3.to_wei(
    *os.getenv("MAX_BUFFERED_ETHERS", "5000 ether").split(" ")
)

# Metrics
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9000"))
PROMETHEUS_PREFIX = os.getenv("PROMETHEUS_PREFIX", "validator_exit_bot")
SERVER_PORT = int(os.getenv("SERVER_PORT", "9010"))

# Same as min deposit block distance on mainnet for all modules
# https://etherscan.io/address/0xFdDf38947aFB03C621C71b06C9C70bce73f12999#readProxyContract#F38
BLOCKS_BETWEEN_EXECUTION = int(os.getenv("BLOCKS_BETWEEN_EXECUTION", 25))

# Bot cycle sleep interval in seconds
SLEEP_INTERVAL_SECONDS = int(os.getenv("SLEEP_INTERVAL_SECONDS", 60))

# Lookback period in days for initial scan on bot startup
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", 7))

MAX_WITHDRAWAL_FEE_PER_VALIDATOR = Web3.to_wei(
    *os.getenv("MAX_WITHDRAWAL_FEE_PER_VALIDATOR", "5 gwei").split(" ")
)

# All non-private env variables to the logs in main
PUBLIC_ENV_VARS = {
    "LIDO_LOCATOR": LIDO_LOCATOR,
    "DRY_RUN": DRY_RUN,
    "MIN_PRIORITY_FEE": MIN_PRIORITY_FEE,
    "MAX_PRIORITY_FEE": MAX_PRIORITY_FEE,
    "MAX_GAS_FEE": MAX_GAS_FEE,
    "CONTRACT_GAS_LIMIT": CONTRACT_GAS_LIMIT,
    "GAS_FEE_PERCENTILE_1": GAS_FEE_PERCENTILE_1,
    "GAS_FEE_PERCENTILE_DAYS_HISTORY_1": GAS_FEE_PERCENTILE_DAYS_HISTORY_1,
    "GAS_PRIORITY_FEE_PERCENTILE": GAS_PRIORITY_FEE_PERCENTILE,
    "MAX_BUFFERED_ETHERS": MAX_BUFFERED_ETHERS,
    "LOG_LEVEL": LOG_LEVEL,
    "PROMETHEUS_PORT": PROMETHEUS_PORT,
    "PROMETHEUS_PREFIX": PROMETHEUS_PREFIX,
    "SERVER_PORT": SERVER_PORT,
    "ACCOUNT": "" if ACCOUNT is None else ACCOUNT.address,
    "BLOCKS_BETWEEN_EXECUTION": BLOCKS_BETWEEN_EXECUTION,
    "SLEEP_INTERVAL_SECONDS": SLEEP_INTERVAL_SECONDS,
    "LOOKBACK_DAYS": LOOKBACK_DAYS,
    "MAX_WITHDRAWAL_FEE_PER_VALIDATOR": MAX_WITHDRAWAL_FEE_PER_VALIDATOR,
    # The paths show which source each secret came from; the values stay in PRIVATE_ENV_VARS.
    "WEB3_RPC_ENDPOINTS_FILE": os.getenv("WEB3_RPC_ENDPOINTS_FILE", ""),
    "CONSENSUS_CLIENT_URL_FILE": os.getenv("CONSENSUS_CLIENT_URL_FILE", ""),
    "WALLET_PRIVATE_KEY_FILE": os.getenv("WALLET_PRIVATE_KEY_FILE", ""),
}

assert not set(PRIVATE_ENV_VARS.keys()).intersection(set(PUBLIC_ENV_VARS.keys()))

# Validate required configuration
if not WEB3_RPC_ENDPOINTS:
    raise ValueError("WEB3_RPC_ENDPOINTS environment variable is required")

if not CONSENSUS_CLIENT_URL:
    raise ValueError(
        "CONSENSUS_CLIENT_URL environment variable is required. "
        "Example: CONSENSUS_CLIENT_URL=http://localhost:5052"
    )
