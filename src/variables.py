import os
from typing import Optional

import structlog
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3

logger = structlog.get_logger(__name__)

# EL node
WEB3_RPC_ENDPOINTS = os.getenv("WEB3_RPC_ENDPOINTS", "").split(",")

# CL node
CL_RPC_ENDPOINTS = os.getenv("CL_RPC_ENDPOINTS", "").split(",")

# Account private key
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY", None)

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

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Metrics
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9000"))
PROMETHEUS_PREFIX = os.getenv("PROMETHEUS_PREFIX", "validator_exit_bot")
SERVER_PORT = int(os.getenv("SERVER_PORT", "9010"))

# List of ids of staking modules in which the depositor bot will make deposits
_env_whitelist = os.getenv("MODULES_WHITELIST", "").strip()
MODULES_WHITELIST = (
    [int(module_id) for module_id in _env_whitelist.split(",")]
    if _env_whitelist
    else []
)
DEPOSIT_MODULES_WHITELIST = MODULES_WHITELIST  # Alias for metrics compatibility
# Same as min deposit block distance on mainnet for all modules
# https://etherscan.io/address/0xFdDf38947aFB03C621C71b06C9C70bce73f12999#readProxyContract#F38
BLOCKS_BETWEEN_EXECUTION = int(os.getenv("BLOCKS_BETWEEN_EXECUTION", 25))

# Bot cycle sleep interval in seconds
SLEEP_INTERVAL_SECONDS = int(os.getenv("SLEEP_INTERVAL_SECONDS", 60))

# Lookback period in days for initial scan on bot startup
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", 7))

# All non-private env variables to the logs in main
PUBLIC_ENV_VARS = {
    "LIDO_LOCATOR": LIDO_LOCATOR,
    "DRY_RUN": DRY_RUN,
    "MIN_PRIORITY_FEE": MIN_PRIORITY_FEE,
    "MAX_PRIORITY_FEE": MAX_PRIORITY_FEE,
    "MAX_GAS_FEE": MAX_GAS_FEE,
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
}

PRIVATE_ENV_VARS = {
    "WEB3_RPC_ENDPOINTS": WEB3_RPC_ENDPOINTS,
    "WALLET_PRIVATE_KEY": WALLET_PRIVATE_KEY,
}

assert not set(PRIVATE_ENV_VARS.keys()).intersection(set(PUBLIC_ENV_VARS.keys()))
