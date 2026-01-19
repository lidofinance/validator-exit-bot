from typing import cast

import structlog
from web3 import Web3
from web3.module import Module

from src import variables
from src.blockchain.contracts.lido_locator import LidoLocatorContract
from src.blockchain.contracts.node_operator_registry import NodeOperatorRegistryContract
from src.blockchain.contracts.staking_router import StakingRouterContract
from src.blockchain.contracts.validator_exit_bus_oracle import (
    ValidatorExitBusOracleContract,
)
from src.blockchain.contracts.withdrawal_vault import WithdrawalVaultContract

logger = structlog.get_logger(__name__)


class LidoContracts(Module):
    def __init__(self, w3: Web3):
        super().__init__(w3)
        self.node_operator_registry_map: dict[int, NodeOperatorRegistryContract] = {}
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

        for module_id in variables.MODULES_WHITELIST:
            self.node_operator_registry_map[module_id] = cast(
                NodeOperatorRegistryContract,
                self.w3.eth.contract(
                    address=self.staking_router.get_staking_module(module_id),
                    ContractFactoryClass=NodeOperatorRegistryContract,
                ),
            )
