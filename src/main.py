import logging
import time

import structlog
import web3_multi_provider
from prometheus_client import start_http_server
from web3_multi_provider import FallbackProvider
from web3_multi_provider.metrics import MetricsConfig

from src.blockchain.constants import SLOT_TIME
from src.blockchain.typings import Web3
from src.blockchain.web3_extentions.lido_contracts import LidoContracts
from src.blockchain.web3_extentions.transaction import TransactionUtils
from src.health_server import pulse, start_health_server
from src.metrics import metrics
from src.metrics.metrics import (
    BOT_CYCLE_DURATION,
    LAST_PROCESSED_BLOCK,
    UNEXPECTED_EXCEPTIONS,
)
from src.trigger_exit_bot import TriggerExitBot
from src.utils.cl_client import CLClient
from src.variables import (
    ACCOUNT,
    CL_RPC_ENDPOINTS,
    LOG_LEVEL,
    LOOKBACK_DAYS,
    PROMETHEUS_PORT,
    PROMETHEUS_PREFIX,
    SERVER_PORT,
    SLEEP_INTERVAL_SECONDS,
    WEB3_RPC_ENDPOINTS,
)

# Configure structlog for JSON logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, LOG_LEVEL)),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger(__name__)


def create_web3(endpoints: list[str]) -> Web3:
    w3 = Web3(FallbackProvider(endpoints, cache_allowed_requests=True))
    logger.info({"msg": "Current chain_id", "chain_id": w3.eth.chain_id})
    w3.attach_modules(
        {
            "lido": LidoContracts,
            "transaction": TransactionUtils,
        }
    )
    return w3


def create_cl_client(endpoints: list[str]) -> CLClient:
    return CLClient(endpoints[0])


def main():
    """Main bot logic."""
    # Start health server in background thread
    start_health_server(SERVER_PORT)
    start_http_server(PROMETHEUS_PORT)

    logger.info(
        {
            "msg": "Initializing metrics for web3 requests.",
            "namespace": PROMETHEUS_PREFIX,
        }
    )
    web3_multi_provider.init_metrics(MetricsConfig(namespace=PROMETHEUS_PREFIX))

    w3 = create_web3(WEB3_RPC_ENDPOINTS)
    cl_client = create_cl_client(CL_RPC_ENDPOINTS)

    # Initialize TriggerExitBot
    bot = TriggerExitBot(w3, cl_client)
    logger.info({"msg": "TriggerExitBot initialized"})

    # Track last processed block
    last_processed_block = None

    try:
        while True:
            pulse()
            if ACCOUNT:
                balance = w3.eth.get_balance(ACCOUNT.address)
                metrics.ACCOUNT_BALANCE.labels(ACCOUNT.address, w3.eth.chain_id).set(
                    balance
                )
            logger.info({"msg": "Running bot cycle"})
            # Always use 'finalized' as to_block
            finalized_block = w3.eth.get_block("finalized").get("number")
            if finalized_block is None:
                raise RuntimeError("Finalized block must have a number")

            # Determine from_block
            if last_processed_block is None:
                # Approximate blocks in lookback period (12 seconds per block average)
                blocks_per_day = 24 * 60 * 60 // SLOT_TIME
                lookback_blocks = LOOKBACK_DAYS * blocks_per_day
                from_block = max(0, finalized_block - lookback_blocks)

                logger.info(
                    {
                        "msg": "First run - scanning historical events",
                        "lookback_days": LOOKBACK_DAYS,
                        "from_block": from_block,
                        "current_block": finalized_block,
                        "blocks_to_scan": lookback_blocks,
                    }
                )
            else:
                # Subsequent runs: continue from last processed block
                from_block = last_processed_block + 1
                logger.info(
                    {
                        "msg": "Continuing from last processed block",
                        "from_block": from_block,
                    }
                )
            # Fetch and process ExitDataProcessing events
            cycle_start_time = time.time()
            try:
                events = bot.trigger_exits(
                    from_block=from_block, to_block=finalized_block
                )
                last_processed_block = finalized_block

                cycle_duration = time.time() - cycle_start_time
                BOT_CYCLE_DURATION.labels(status="success").observe(cycle_duration)
                LAST_PROCESSED_BLOCK.labels(chain_id=w3.eth.chain_id).set(
                    last_processed_block
                )

                logger.info(
                    {
                        "msg": "Bot cycle completed",
                        "events_processed": len(events),
                        "from_block": from_block,
                        "to_block": finalized_block,
                        "last_processed_block": last_processed_block,
                        "cycle_duration_seconds": cycle_duration,
                        "sleeping_for_seconds": SLEEP_INTERVAL_SECONDS,
                    }
                )
            except Exception as e:
                cycle_duration = time.time() - cycle_start_time
                BOT_CYCLE_DURATION.labels(status="error").observe(cycle_duration)

                error_type = type(e).__name__
                UNEXPECTED_EXCEPTIONS.labels(type=error_type).inc()
                logger.error(
                    {
                        "msg": "Error triggering exits",
                        "error": str(e),
                        "error_type": error_type,
                        "from_block": from_block,
                        "to_block": finalized_block,
                        "cycle_duration_seconds": cycle_duration,
                    },
                    exc_info=True,
                )
            time.sleep(SLEEP_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info({"msg": "Shutting down bot..."})


if __name__ == "__main__":
    main()
