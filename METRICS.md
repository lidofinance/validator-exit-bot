# Prometheus Metrics

This document describes all Prometheus metrics exposed by the Validator Exit Bot.

## Metrics Endpoint

- **URL**: `http://localhost:9000/metrics` (configurable via `PROMETHEUS_PORT`)
- **Namespace**: `validator_exit_bot` (configurable via `PROMETHEUS_PREFIX`)

All metrics are prefixed with the namespace, e.g., `validator_exit_bot_last_processed_block`.

## Critical Metrics

### `validator_exit_bot_exit_events_processed`
**Type**: Counter  
**Labels**: `status` (success, failed, skipped)  
**Description**: Number of ExitDataProcessing events processed from the ValidatorExitBusOracle contract.

**Usage**: Monitor if the bot is processing events. Alert if no events are processed for an extended period.

### `validator_exit_bot_validators_checked`
**Type**: Counter  
**Labels**: `module_id`, `status` (already_exited, needs_exit, not_reported, skipped_module)  
**Description**: Number of validators checked for exit status.

**Usage**: Track validator processing flow. High `not_reported` count may indicate validators not yet reported by oracle.

### `validator_exit_bot_validators_triggered`
**Type**: Counter  
**Labels**: `module_id`, `node_operator_id`  
**Description**: Number of validators for which exit was successfully triggered.

**Usage**: Core business metric. Track actual validator exits per module and node operator.

### `validator_exit_bot_last_processed_block`
**Type**: Gauge  
**Labels**: `chain_id`  
**Description**: Last block number processed by the bot.

**Usage**: Monitor if bot is keeping up with chain. Compare with current finalized block to detect lag.

**Alert Example**:
```yaml
- alert: ValidatorExitBotLagging
  expr: eth_block_number{job="ethereum"} - validator_exit_bot_last_processed_block > 100
  for: 5m
  annotations:
    summary: "Validator Exit Bot is lagging behind"
```

## High Priority Metrics

### `validator_exit_bot_bot_cycle_duration_seconds`
**Type**: Histogram  
**Labels**: `status` (success, error)  
**Buckets**: 0.5, 1, 2, 5, 10, 30, 60, 120, 300 seconds  
**Description**: Duration of bot cycle execution.

**Usage**: Performance monitoring. Alert on slow cycles or increasing p95/p99 latencies.

**Queries**:
```promql
# Average cycle duration
rate(validator_exit_bot_bot_cycle_duration_seconds_sum[5m]) / rate(validator_exit_bot_bot_cycle_duration_seconds_count[5m])

# P95 cycle duration
histogram_quantile(0.95, rate(validator_exit_bot_bot_cycle_duration_seconds_bucket[5m]))
```

### `validator_exit_bot_pending_validators`
**Type**: Gauge  
**Labels**: `module_id`  
**Description**: Number of validators pending exit trigger (reported but not yet exited).

**Usage**: Monitor backlog per module. Alert if growing continuously.

**Alert Example**:
```yaml
- alert: ValidatorExitBacklogGrowing
  expr: delta(validator_exit_bot_pending_validators[1h]) > 10
  for: 30m
  annotations:
    summary: "Validator exit backlog is growing"
```

## Existing Metrics

### `validator_exit_bot_transactions_send`
**Type**: Counter  
**Labels**: `status` (success, failure)  
**Description**: Number of transactions sent by the bot.

### `validator_exit_bot_unexpected_exceptions`
**Type**: Counter  
**Labels**: `type` (exception class name)  
**Description**: Total count of unexpected exceptions.

**Usage**: Alert on any unexpected exceptions.

### `validator_exit_bot_account_balance`
**Type**: Gauge  
**Labels**: `address`, `chain_id`  
**Description**: Account balance in wei.

**Usage**: Alert if balance is too low to pay for transactions.

**Alert Example**:
```yaml
- alert: ValidatorExitBotLowBalance
  expr: validator_exit_bot_account_balance < 100000000000000000  # 0.1 ETH
  for: 5m
  annotations:
    summary: "Validator Exit Bot account balance is low"
```

### `validator_exit_bot_build_info`
**Type**: Info  
**Description**: Build and configuration information.

## Web3 Provider Metrics

These metrics are provided by the `web3-multi-provider` library and track RPC performance:

### `validator_exit_bot_http_rpc_requests`
**Type**: Counter  
**Labels**: `network`, `layer`, `chain_id`, `provider`, `batched`, `response_code`, `result`  
**Description**: Total HTTP requests to RPC providers.

### `validator_exit_bot_rpc_request`
**Type**: Counter  
**Labels**: `network`, `layer`, `chain_id`, `provider`, `method`, `result`, `rpc_error_code`  
**Description**: Total number of RPC requests by method.

### `validator_exit_bot_http_rpc_response_seconds`
**Type**: Histogram  
**Labels**: `network`, `layer`, `chain_id`, `provider`  
**Description**: Distribution of RPC response times.

### `validator_exit_bot_http_rpc_batch_size`
**Type**: Histogram  
**Labels**: `network`, `layer`, `chain_id`, `provider`  
**Description**: Distribution of batch request sizes.

## Grafana Dashboard Examples

### Key Panels

1. **Validators Triggered (Rate)**
```promql
rate(validator_exit_bot_validators_triggered[5m])
```

2. **Bot Cycle Duration (P95)**
```promql
histogram_quantile(0.95, rate(validator_exit_bot_bot_cycle_duration_seconds_bucket[5m]))
```

3. **Pending Validators by Module**
```promql
validator_exit_bot_pending_validators
```

4. **Block Processing Lag**
```promql
eth_block_number{job="ethereum"} - validator_exit_bot_last_processed_block
```

5. **Events Processed Rate**
```promql
rate(validator_exit_bot_exit_events_processed[5m])
```

6. **Validators Status Breakdown**
```promql
rate(validator_exit_bot_validators_checked[5m])
```

7. **RPC Performance**
```promql
histogram_quantile(0.95, rate(validator_exit_bot_http_rpc_response_seconds_bucket[5m]))
```

## Configuration

Set the metrics namespace in your `.env` file:

```bash
PROMETHEUS_PREFIX=validator_exit_bot
PROMETHEUS_PORT=9000
```

