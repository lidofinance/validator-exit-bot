import structlog
from typing import cast

from blockchain.contracts.node_operator_registry import NodeOperatorRegistryContract
from blockchain.contracts.staking_router import StakingRouterContract
from blockchain.contracts.validator_exit_bus_oracle import ValidatorExitBusOracleContract
import variables
from blockchain.contracts.lido_locator import LidoLocatorContract
from web3 import Web3
from web3.contract.contract import Contract
from web3.module import Module

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

        for module_id in variables.MODULES_WHITELIST:
            self.node_operator_registry_map[module_id] = cast(
                NodeOperatorRegistryContract,
                self.w3.eth.contract(
                    address=self.staking_router.get_staking_module(module_id),
                    ContractFactoryClass=NodeOperatorRegistryContract,
                ),
            )
            
