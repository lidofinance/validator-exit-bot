from prometheus_client.metrics import Counter, Gauge, Info
from variables import PUBLIC_ENV_VARS

GAS_FEE = Gauge(
    'gas_fee',
    'Gas fee',
    ['type', 'module_id'],
)

TX_SEND = Counter('transactions_send', 'Amount of send transaction from bot.', ['status'])

# Initialize metrics
TX_SEND.labels('success').inc(0)
TX_SEND.labels('failure').inc(0)

MODULE_TX_SEND = Counter(
    'transactions',
    'Amount of send transactions from depositor bot.',
    ['status', 'module_id'],
)

UNEXPECTED_EXCEPTIONS = Counter(
    'unexpected_exceptions',
    'Total count of unexpected exceptions',
    ['type'],
)

ACCOUNT_BALANCE = Gauge(
    'account_balance',
    'Account balance',
    ['address', 'chain_id'],
)

MODULES = Gauge('modules', 'Modules gauge', ['module_id'])

INFO = Info(name='build', documentation='Info metric')
CONVERTED_PUBLIC_ENV = {k: str(v) for k, v in PUBLIC_ENV_VARS.items()}
INFO.info(CONVERTED_PUBLIC_ENV)
