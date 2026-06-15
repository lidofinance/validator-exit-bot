# Add support for new staking module types and remove manual whitelist

## Overview

This PR extends the validator exit bot to support new staking module types
(CSModule, CuratedModule v2) that use a different on-chain interface for
determining when a validator exit should be triggered. At the same time it
removes the manual `MODULES_WHITELIST` configuration — the bot now
auto-discovers all registered staking modules from the Staking Router at
startup with no operator configuration required.

---

## 1. Removed: `MODULES_WHITELIST`

Previously operators had to enumerate every staking module ID they wanted the
bot to process:

```
MODULES_WHITELIST=1,2,3
```

This was error-prone (missed modules meant missed exits) and required manual
updates whenever a new module was registered on-chain.

**What changed:**

- `MODULES_WHITELIST` env var removed from `variables.py`, `env.example`, and
  `docker-compose.yml`
- `StakingRouterContract` gained `get_staking_module_ids()` which calls
  `getStakingModuleIds()` on-chain
- `LidoContracts._load_contracts()` now fetches all registered module IDs from
  the Staking Router at startup and initialises a contract handle for each

---

## 2. Added: auto-detection of module type

Not all staking modules implement the same interface. At startup, for each
discovered module the bot probes which interface it supports:

```
_probe_exit_penalties(module_address)
  └─ calls EXIT_PENALTIES() on the module
       ├─ returns non-zero address → new-style module (CSM, CMv2)
       └─ reverts / returns zero  → legacy NOR module
```

The result is stored in two maps:

| Map | Module types |
|-----|-------------|
| `node_operator_registry_map` | Curated (NOR), SimpleDVT, Sandbox |
| `exit_penalties_map` | CSModule, CuratedModule v2 |

---

## 3. How exit triggering works per module type

### Legacy NOR modules (modules 1, 2, 3 on Hoodi)

These modules expose `isValidatorExitingKeyReported(pubkey)` directly on the
module contract (NodeOperatorRegistry). The bot calls this method to determine
whether an exit can be triggered.

```
ValidatorExitBusOracle
  └─ ExitDataProcessing event
       └─ for each validator
            └─ NodeOperatorRegistry.isValidatorExitingKeyReported(pubkey)
                 ├─ true  → trigger exit transaction
                 └─ false → wait (keep in state)
```

### New-style modules (modules 4, 5 on Hoodi — CSM, CMv2)

These modules do not have `isValidatorExitingKeyReported`. Instead the module
contract exposes an immutable `EXIT_PENALTIES()` address pointing to a
dedicated `ExitPenalties` contract. The relevant check is
`getExitPenaltyInfo(nodeOpId, pubkey).delayFee.isValue`:

```
ValidatorExitBusOracle
  └─ ExitDataProcessing event
       └─ for each validator
            └─ Module.EXIT_PENALTIES() → ExitPenalties address
                 └─ ExitPenalties.getExitPenaltyInfo(nodeOpId, pubkey)
                      └─ delayFee: MarkedUint248 { value: uint248, isValue: bool }
                           ├─ isValue = true  → trigger exit transaction
                           └─ isValue = false → wait (keep in state)
```

`delayFee.isValue` is set to `true` by the `ExitPenalties` contract once
`processExitDelayReport` has been called for that validator, meaning the
on-chain accounting has recorded that the validator is overdue and a penalty
fee has been determined.

---

## 4. Full flow diagram

```
Bot startup
│
├─ StakingRouter.getStakingModuleIds() ──────────────────────── [1, 2, 3, 4, 5]
│
└─ for each module_id:
     ├─ StakingRouter.getStakingModule(id) → module_address
     │
     └─ probe: Module.EXIT_PENALTIES()
          │
          ├─ non-zero address
          │    └─ ExitPenalties contract initialised
          │         → exit_penalties_map[module_id]          (new-style)
          │
          └─ reverts / zero
               └─ NodeOperatorRegistry contract initialised
                    → node_operator_registry_map[module_id]  (NOR-style)


Bot cycle
│
├─ fetch ExitDataProcessing events (VEBO)
│
└─ for each validator in state:
     │
     ├─ CLClient.is_validator_exited(pubkey)
     │    ├─ true  → remove from state
     │    └─ false → continue
     │
     ├─ exit_penalties_map.get(module_id)  [new-style path]
     │    ├─ found:
     │    │    ExitPenalties.getExitPenaltyInfo(nodeOpId, pubkey)
     │    │      ├─ delayFee.isValue = true  → add to trigger list
     │    │      └─ delayFee.isValue = false → keep in state (waiting)
     │    │    continue  (NOR path never reached for new-style modules)
     │    └─ not found → fall through to NOR path
     │
     └─ node_operator_registry_map.get(module_id)  [NOR path]
          ├─ found:
          │    NodeOperatorRegistry.isValidatorExitingKeyReported(pubkey)
          │      ├─ true  → add to trigger list
          │      └─ false → keep in state (waiting)
          └─ not found (module registered after bot start)
               └─ remove from state (prevents unbounded accumulation)
```

---

## 5. State management: no hanging entries

| Situation | State action |
|---|---|
| Validator already exited on CL | Removed |
| New-style: `delayFee.isValue = true` | Triggered → stays until exited on CL |
| New-style: `delayFee.isValue = false` | Kept (waiting for penalty to be set) |
| NOR: key reported | Triggered → stays until exited on CL |
| NOR: key not reported | Kept (waiting for oracle report) |
| Module unknown (registered after bot start) | Removed (prevents accumulation) |

---

## 6. New files

| File | Purpose |
|---|---|
| `interfaces/BaseModule.json` | Minimal ABI — `EXIT_PENALTIES()` function |
| `interfaces/ExitPenalties.json` | ABI — `getExitPenaltyInfo` with `MarkedUint248`/`ExitPenaltyInfo` structs |
| `src/blockchain/contracts/base_module.py` | Contract wrapper used to probe module type at startup |
| `src/blockchain/contracts/exit_penalties.py` | Contract wrapper — `is_exit_delay_applicable(node_op_id, pubkey)` |
| `tests/test_new_module_support.py` | Unit tests for all three layers: contract, detection, bot loop |
