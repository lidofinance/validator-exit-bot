import logging
import time
import structlog
import web3_multi_provider
from blockchain.typings import Web3
from blockchain.web3_extentions.lido_contracts import LidoContracts
from blockchain.web3_extentions.transaction import TransactionUtils
from health_server import start_health_server
from prometheus_client import start_http_server
from trigger_exit_bot import TriggerExitBot
from utils.cl_client import CLClient
from variables import SERVER_PORT, LOG_LEVEL, PROMETHEUS_PORT, WEB3_RPC_ENDPOINTS, CL_RPC_ENDPOINTS, SLEEP_INTERVAL_SECONDS, LOOKBACK_DAYS
from blockchain.constants import SLOT_TIME
from web3_multi_provider import FallbackProvider

# Configure structlog for JSON logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, LOG_LEVEL)),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger(__name__)

def create_web3(endpoints: list[str]) -> Web3:
    w3 = Web3(FallbackProvider(endpoints, cache_allowed_requests=True))
    logger.info({'msg': 'Current chain_id', 'chain_id': w3.eth.chain_id})
    w3.attach_modules(
        {
            'lido': LidoContracts,
            'transaction': TransactionUtils,
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
    w3 = create_web3(WEB3_RPC_ENDPOINTS)
    cl_client = create_cl_client(CL_RPC_ENDPOINTS)
    logger.info({'msg': 'Add metrics to web3 requests.'})
    web3_multi_provider.init_metrics()
    
    # Initialize TriggerExitBot
    bot = TriggerExitBot(w3, cl_client)
    logger.info({'msg': 'TriggerExitBot initialized'})
    
    # Track last processed block
    last_processed_block = None
    
    try:
        while True:
            logger.info({'msg': 'Running bot cycle'})
            # Always use 'finalized' as to_block
            finalized_block = w3.eth.get_block('finalized')['number']
            
            # Determine from_block
            if last_processed_block is None:
                # Approximate blocks in lookback period (12 seconds per block average)
                blocks_per_day = 24 * 60 * 60 // SLOT_TIME
                lookback_blocks = LOOKBACK_DAYS * blocks_per_day
                from_block = max(0, finalized_block - lookback_blocks)
                
                logger.info({
                    'msg': 'First run - scanning historical events',
                    'lookback_days': LOOKBACK_DAYS,
                    'from_block': from_block,
                    'current_block': finalized_block,
                    'blocks_to_scan': lookback_blocks
                })
            else:
                # Subsequent runs: continue from last processed block
                from_block = last_processed_block + 1
                logger.info({
                    'msg': 'Continuing from last processed block',
                    'from_block': from_block
                })
            # Fetch and process ExitDataProcessing events
            events = bot.trigger_exits(from_block=from_block, to_block=finalized_block)
            last_processed_block = finalized_block
            
            logger.info({
                'msg': 'Bot cycle completed', 
                'events_processed': len(events),
                'from_block': from_block,
                'to_block': finalized_block,
                'last_processed_block': last_processed_block,
                'sleeping_for_seconds': SLEEP_INTERVAL_SECONDS
            })
            time.sleep(SLEEP_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info({'msg': 'Shutting down bot...'})


if __name__ == '__main__':
    main()
