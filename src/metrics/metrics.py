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

DEPOSIT_MESSAGES = Gauge(
    'deposit_messages',
    'Guardians deposit messages',
    ['address', 'module_id', 'version', 'transport', 'chain_id'],
)
PAUSE_MESSAGES = Gauge(
    'pause_messages',
    'Guardians pause messages',
    ['address', 'module_id', 'version', 'transport', 'chain_id'],
)
PING_MESSAGES = Gauge(
    'ping_messages',
    'Guardians ping messages',
    ['address', 'version', 'transport', 'chain_id'],
)
UNVET_MESSAGES = Gauge(
    'unvet_messages',
    'Guardian unvet messages',
    ['address', 'module_id', 'version', 'transport', 'chain_id'],
)

CURRENT_QUORUM_SIZE = Gauge(
    'quorum_size',
    'Current quorum size',
    ['type'],
)

DEPOSITABLE_ETHER = Gauge(
    'depositable_ether',
    'Depositable Ether',
)

POSSIBLE_DEPOSITS_AMOUNT = Gauge(
    'possible_deposits_amount',
    'Possible deposits amount.',
    ['module_id'],
)

IS_DEPOSITABLE = Gauge(
    'is_depositable',
    'Represents is_depositable check.',
    ['module_id'],
)

QUORUM = Gauge(
    'quorum',
    'Represents if quorum could be collected.',
    ['module_id'],
)

CAN_DEPOSIT = Gauge(
    'can_deposit',
    'Represents can_deposit check.',
    ['module_id'],
)

GAS_OK = Gauge(
    'is_gas_ok',
    'Represents is_gas_ok check.',
    ['module_id'],
)

DEPOSIT_AMOUNT_OK = Gauge(
    'is_deposit_amount_ok',
    'Represents is_deposit_amount_ok check.',
    ['module_id'],
)

UNEXPECTED_EXCEPTIONS = Counter(
    'unexpected_exceptions',
    'Total count of unexpected exceptions',
    ['type'],
)

# TODO unify ACCOUNT_BALANCE and GUARDIAN_BALANCE
ACCOUNT_BALANCE = Gauge(
    'account_balance',
    'Account balance',
    ['address', 'chain_id'],
)

GUARDIAN_BALANCE = Gauge(
    'guardian_balance',
    'Balance of the guardian',
    ['address', 'chain_id'],
)

MODULES = Gauge('modules', 'Modules gauge', ['module_id'])

INFO = Info(name='build', documentation='Info metric')
CONVERTED_PUBLIC_ENV = {k: str(v) for k, v in PUBLIC_ENV_VARS.items()}
INFO.info(CONVERTED_PUBLIC_ENV)
