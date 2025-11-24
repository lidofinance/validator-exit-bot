# Unit Tests for Validator Exit Bot

This directory contains comprehensive unit tests for the core bot logic in `TriggerExitBot`.

## Running Tests

### Prerequisites

Install test dependencies:
```bash
poetry install --with dev
```

### Run All Tests

```bash
# Using make
make test

# Using poetry directly
poetry run pytest

# Using pytest directly (if in poetry shell)
pytest
```

### Run with Coverage

```bash
# Using make
make test-cov

# Using poetry
poetry run pytest --cov=src --cov-report=term-missing --cov-report=html
```

This will generate:
- Terminal coverage report
- HTML coverage report in `htmlcov/` directory

### Run Specific Tests

```bash
# Run specific test file
poetry run pytest tests/test_trigger_exit_bot.py

# Run specific test class
poetry run pytest tests/test_trigger_exit_bot.py::TestTriggerExitBotInit

# Run specific test method
poetry run pytest tests/test_trigger_exit_bot.py::TestTriggerExitBotInit::test_init_creates_empty_state

# Run tests matching a pattern
poetry run pytest -k "transaction"
```

### Verbose Output

```bash
# More verbose output
poetry run pytest -vv

# Show print statements
poetry run pytest -s

# Both
poetry run pytest -vv -s
```

## Test Structure

### Test Classes

The tests are organized into the following classes:

#### `TestTriggerExitBotInit`
- Tests for bot initialization
- Verifies empty state creation

#### `TestGetTransactionData`
- Tests for `_get_transaction_data()` method
- Success and failure scenarios
- Error handling

#### `TestDecodeTransactionInput`
- Tests for `_decode_transaction_input()` method
- Tests both `submitReportData` and `submitExitRequestsData` decoding
- Handles decode failures

#### `TestProcessSubmitReportData`
- Tests for `_process_submit_report_data()` method
- Validator storage
- Zero requests handling

#### `TestProcessSubmitExitRequestsData`
- Tests for `_process_submit_exit_requests_data()` method
- Processing state retrieval
- Validator storage

#### `TestGetValidatorsForData`
- Tests for `get_validators_for_data()` method
- Tests with bytes and hex string keys
- Not found scenarios

#### `TestCheckAndTriggerExits`
- Tests for `_check_and_trigger_exits()` method
- Validator reporting checks
- CL client integration (exited validators)
- Module whitelist filtering
- State management (removal of exited validators)

#### `TestTriggerExitsTransaction`
- Tests for `_trigger_exits_transaction()` method
- Transaction building and sending
- Withdrawal fee calculation
- Account configuration (with/without account)
- Error handling (fee fetch failures, check failures)

#### `TestTriggerExitsMainMethod`
- Tests for the main `trigger_exits()` entry point
- Event processing
- Failed transaction handling
- State checking for all entries

## Test Coverage

The test suite covers:

✅ **Initialization & Setup**
- Bot initialization with empty state
- Mock creation and fixtures

✅ **Transaction Data Handling**
- Fetching transaction data from blockchain
- Error handling for network failures

✅ **Transaction Decoding**
- Decoding `submitReportData` transactions
- Decoding `submitExitRequestsData` transactions
- Handling decode failures

✅ **Validator Processing**
- Storing validators in state
- Retrieving validators by data key
- Zero request handling

✅ **Exit Triggering Logic**
- Checking validator exit status via CL
- Checking validator reporting status via node operator registry
- Module whitelist filtering
- Removing exited validators from state
- Building and sending trigger transactions

✅ **Withdrawal Fees**
- Fetching withdrawal request fee
- Calculating total fee for multiple validators
- Error handling for fee fetch failures

✅ **Transaction Building**
- Using correct refund recipient (bot account)
- Zero address fallback for dry run mode
- Including correct value in transaction
- Transaction checking before sending

✅ **Error Handling**
- Network failures
- Contract call failures
- Transaction check failures
- Missing configuration

## Mocking Strategy

The tests use comprehensive mocking to isolate the bot logic:

### `mock_w3` Fixture
Mocks the Web3 instance including:
- `w3.eth` for blockchain operations
- `w3.lido` for Lido contract interactions
- `w3.transaction` for transaction utilities

### `mock_cl_client` Fixture
Mocks the Consensus Layer client:
- `is_validator_exited()` method

### `sample_validator` / `sample_validators` Fixtures
Provide realistic test data for validators

## Best Practices

1. **Isolation**: Each test is isolated with proper fixtures and mocks
2. **Coverage**: Tests cover success paths, error paths, and edge cases
3. **Clarity**: Test names clearly describe what is being tested
4. **Maintainability**: Uses pytest fixtures for reusable test components
5. **Documentation**: Tests serve as documentation for expected behavior

## Adding New Tests

When adding new functionality to `TriggerExitBot`:

1. Create a new test class if testing a new method
2. Add test methods covering:
   - Success scenario
   - Error scenarios
   - Edge cases
3. Use descriptive test names: `test_<method>_<scenario>`
4. Add appropriate mocks and fixtures
5. Run tests to ensure they pass: `make test`
6. Check coverage: `make test-cov`

## CI/CD Integration

Tests are automatically run via GitHub Actions in `.github/workflows/tests-and-checks.yml`:

- ✅ Runs on every push and pull request
- ✅ Includes linting (Ruff), type checking (Pyright), and unit tests
- ✅ Generates coverage reports
- ✅ Uploads coverage to Codecov
- ✅ Uses dependency caching for faster runs

The workflow runs:
```bash
poetry run pytest tests/ -v --cov=src --cov-report=xml --cov-report=term-missing
```

