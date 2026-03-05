# backend/blockchain/notary_client.py

from web3 import Web3
from eth_utils import to_checksum_address
import logging

logger = logging.getLogger(__name__)

from backend.config import settings

RPC_URL = settings.RPC_URL
CONTRACT_ADDRESS = settings.CONTRACT_ADDRESS

CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "eventHash",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "EventAnchored",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "eventHash",
                "type": "bytes32"
            }
        ],
        "name": "anchorEvent",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "",
                "type": "bytes32"
            }
        ],
        "name": "anchored",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]


class BlockchainNotary:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.contract = None
        self.account = None

    def is_ready(self) -> bool:
        if not self.w3.is_connected():
            return False
            
        if self.contract is None:
            self.contract = self.w3.eth.contract(
                address=to_checksum_address(CONTRACT_ADDRESS),
                abi=CONTRACT_ABI
            )
            
        if self.account is None:
            try:
                self.account = self.w3.eth.accounts[0]
            except Exception as e:
                logger.warning(f"Could not load accounts from local node: {e}")
                
        return self.account is not None

    def anchor_event(self, event_hash: str, event_type: str):
        """
        Anchor an event hash on-chain.
        Takes our SHA256 event_hash and records it on the ledger.
        Returns (on_chain_tx_hash, block_number) or (None, None).
        """
        if not self.is_ready():
            raise RuntimeError("Blockchain not connected.")

        # event_hash is a 64 char hex string without 0x prefix. We add the prefix.
        hex_hash = "0x" + event_hash

        tx = self.contract.functions.anchorEvent(
            self.w3.to_bytes(hexstr=hex_hash)
        ).transact({
            "from": self.account
        })

        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        return receipt.transactionHash.hex(), receipt.blockNumber
