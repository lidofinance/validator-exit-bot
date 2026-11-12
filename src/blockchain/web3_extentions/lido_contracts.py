from typing import cast

import structlog
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.exceptions import BadFunctionCallOutput, ContractLogicError
from web3.module import Module

from src import variables
from src.blockchain.contracts.base_module import BaseModuleContract
from src.blockchain.contracts.exit_penalties import ExitPenaltiesContract
from src.blockchain.contracts.lido_locator import LidoLocatorContract
from src.blockchain.contracts.node_operator_registry import NodeOperatorRegistryContract
from src.blockchain.contracts.staking_router import StakingRouterContract
from src.blockchain.contracts.validator_exit_bus_oracle import (
    ValidatorExitBusOracleContract,
)
from src.blockchain.contracts.withdrawal_vault import WithdrawalVaultContract

logger = structlog.get_logger(__name__)

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class LidoContracts(Module):
    def __init__(self, w3: Web3):
        super().__init__(w3)
        self.node_operator_registry_map: dict[int, NodeOperatorRegistryContract] = {}
        self.exit_penalties_map: dict[int, ExitPenaltiesContract] = {}
        self._load_contracts()

    def _load_contracts(self):
        self.lido_locator: LidoLocatorContract = cast(
            LidoLocatorContract,
            self.w3.eth.contract(
                address=variables.LIDO_LOCATOR,
                ContractFactoryClass=LidoLocatorContract,
            ),
        )

        self.validator_exit_bus_oracle: ValidatorExitBusOracleContract = cast(
            ValidatorExitBusOracleContract,
            self.w3.eth.contract(
                address=self.lido_locator.validator_exit_bus_oracle(),
                ContractFactoryClass=ValidatorExitBusOracleContract,
            ),
        )
        self.staking_router: StakingRouterContract = cast(
            StakingRouterContract,
            self.w3.eth.contract(
                address=self.lido_locator.staking_router(),
                ContractFactoryClass=StakingRouterContract,
            ),
        )

        self.withdrawal_vault: WithdrawalVaultContract = cast(
            WithdrawalVaultContract,
            self.w3.eth.contract(
                address=self.lido_locator.withdrawal_vault(),
                ContractFactoryClass=WithdrawalVaultContract,
            ),
        )

        self.refresh_modules()

    def refresh_modules(self) -> None:
        """
        Rebuild the per-module contract maps from StakingRouter.

        Staking modules are added and replaced while the bot runs, and a module
        the bot has never seen makes `_check_and_trigger_exits` drop that
        module's validators, so the maps are rebuilt every cycle instead of only
        at startup.

        The new maps are published only once every module has been resolved: a
        failing RPC call leaves the previous maps in place rather than a partial
        view in which known modules look unknown.
        """
        exit_penalties_map: dict[int, ExitPenaltiesContract] = {}
        node_operator_registry_map: dict[int, NodeOperatorRegistryContract] = {}

        for module_id in self.staking_router.get_staking_module_ids():
            module_address = self.staking_router.get_staking_module(module_id)
            exit_penalties_address = self._probe_exit_penalties(module_address)
            if exit_penalties_address:
                exit_penalties_map[module_id] = cast(
                    ExitPenaltiesContract,
                    self.w3.eth.contract(
                        address=exit_penalties_address,
                        ContractFactoryClass=ExitPenaltiesContract,
                    ),
                )
                logger.debug(
                    {
                        "msg": "Module detected as new-style (ExitPenalties)",
                        "module_id": module_id,
                        "exit_penalties_address": exit_penalties_address,
                    }
                )
            else:
                node_operator_registry_map[module_id] = cast(
                    NodeOperatorRegistryContract,
                    self.w3.eth.contract(
                        address=module_address,
                        ContractFactoryClass=NodeOperatorRegistryContract,
                    ),
                )
                logger.debug(
                    {
                        "msg": "Module detected as NOR-style (NodeOperatorRegistry)",
                        "module_id": module_id,
                    }
                )

        previous = self._modules_snapshot()
        self.exit_penalties_map = exit_penalties_map
        self.node_operator_registry_map = node_operator_registry_map
        current = self._modules_snapshot()

        # Every cycle calls this; only report when the module set actually moved.
        if current != previous:
            logger.info(
                {
                    "msg": "Staking modules loaded",
                    "exit_penalties_modules": sorted(exit_penalties_map),
                    "node_operator_registry_modules": sorted(
                        node_operator_registry_map
                    ),
                    "added": sorted(current.keys() - previous.keys()),
                    "removed": sorted(previous.keys() - current.keys()),
                }
            )

    def _modules_snapshot(self) -> dict[int, ChecksumAddress]:
        """Module id -> address of the contract the bot calls for that module."""
        return {
            module_id: contract.address
            for source in (self.exit_penalties_map, self.node_operator_registry_map)
            for module_id, contract in source.items()
        }

    def _probe_exit_penalties(
        self, module_address: ChecksumAddress
    ) -> ChecksumAddress | None:
        try:
            base_module: BaseModuleContract = cast(
                BaseModuleContract,
                self.w3.eth.contract(
                    address=module_address,
                    ContractFactoryClass=BaseModuleContract,
                ),
            )
            exit_penalties_address = base_module.exit_penalties()
            if exit_penalties_address and exit_penalties_address != ZERO_ADDRESS:
                return exit_penalties_address
        except (ContractLogicError, BadFunctionCallOutput) as exc:
            logger.debug(
                {
                    "msg": "Module probe failed, treating as NOR-style",
                    "module_address": module_address,
                    "exc": str(exc),
                }
            )
        return None
