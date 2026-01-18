from prometheus_client.metrics import Counter, Gauge, Histogram, Info

from src.variables import PROMETHEUS_PREFIX, PUBLIC_ENV_VARS

TX_SEND = Counter(
    "transactions_send",
    "Amount of send transaction from bot.",
    ["status"],
    namespace=PROMETHEUS_PREFIX,
)

# Initialize metrics
TX_SEND.labels("success").inc(0)
TX_SEND.labels("failure").inc(0)

UNEXPECTED_EXCEPTIONS = Counter(
    "unexpected_exceptions",
    "Total count of unexpected exceptions",
    ["type"],
    namespace=PROMETHEUS_PREFIX,
)

ACCOUNT_BALANCE = Gauge(
    "account_balance",
    "Account balance in wei",
    ["address", "chain_id"],
    namespace=PROMETHEUS_PREFIX,
)


EVENTS_PROCESSED = Counter(
    "exit_events_processed",
    "Number of ExitDataProcessing events processed",
    ["status"],  # success, failed, skipped
    namespace=PROMETHEUS_PREFIX,
)

VALIDATORS_CHECKED = Gauge(
    "validators_checked",
    "Current number of validators in each check status",
    ["module_id", "status"],  # already_exited, needs_exit, not_reported, skipped_module
    namespace=PROMETHEUS_PREFIX,
)

VALIDATORS_TRIGGERED = Counter(
    "validators_triggered",
    "Number of validators for which exit was triggered",
    ["module_id", "node_operator_id"],
    namespace=PROMETHEUS_PREFIX,
)

LAST_PROCESSED_BLOCK = Gauge(
    "last_processed_block",
    "Last block number processed by the bot",
    ["chain_id"],
    namespace=PROMETHEUS_PREFIX,
)

BOT_CYCLE_DURATION = Histogram(
    "bot_cycle_duration_seconds",
    "Duration of bot cycle execution in seconds",
    ["status"],  # success, error
    namespace=PROMETHEUS_PREFIX,
    buckets=(0.5, 1, 2, 5, 10, 30, 60, 120, 300),
)

PENDING_VALIDATORS = Gauge(
    "pending_validators",
    "Number of validators pending exit trigger (reported but not exited)",
    ["module_id"],
    namespace=PROMETHEUS_PREFIX,
)

INFO = Info(name="build", documentation="Info metric", namespace=PROMETHEUS_PREFIX)
CONVERTED_PUBLIC_ENV = {k: str(v) for k, v in PUBLIC_ENV_VARS.items()}
INFO.info(CONVERTED_PUBLIC_ENV)
