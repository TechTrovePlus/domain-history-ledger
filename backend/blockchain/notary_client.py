# backend/blockchain/notary_client.py

from web3 import Web3
from eth_utils import to_checksum_address

from backend.blockchain.integrity_hash import compute_integrity_hash
from backend.blockchain.anchoring_policy import should_anchor_event


RPC_URL = "http://127.0.0.1:8545"

# Hardhat deployed contract address
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

# Solidity enum mapping (MUST match contract order)
EVENT_TYPE_MAP = {
    "ABUSE_FLAG": 2,           # EventType.ABUSE_FLAGGED
    "OWNERSHIP_CHANGED": 1,    # EventType.OWNERSHIP_CHANGED
}

# ABI matching the EXACT Solidity contract
CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "domainHash",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "internalType": "uint8",
                "name": "eventType",
                "type": "uint8"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "DomainEventRecorded",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "domainHash",
                "type": "bytes32"
            },
            {
                "internalType": "uint8",
                "name": "eventType",
                "type": "uint8"
            }
        ],
        "name": "recordDomainEvent",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


class BlockchainNotary:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))

        if not self.w3.is_connected():
            raise RuntimeError("Cannot connect to local blockchain (Hardhat not running)")

        self.contract = self.w3.eth.contract(
            address=to_checksum_address(CONTRACT_ADDRESS),
            abi=CONTRACT_ABI
        )

        # First Hardhat account
        self.account = self.w3.eth.accounts[0]

    def anchor_event(self, domain: str, event_type: str, event_date: str):
        """
        Anchor an event on-chain if policy allows.
        Returns (integrity_hash, tx_hash) or (None, None).
        """

        if not should_anchor_event(domain, event_type):
            return None, None

        if event_type not in EVENT_TYPE_MAP:
            raise ValueError(f"Unsupported event type for anchoring: {event_type}")

        integrity_hash = compute_integrity_hash(domain, event_type, event_date)

        tx = self.contract.functions.recordDomainEvent(
            self.w3.to_bytes(hexstr=integrity_hash),
            EVENT_TYPE_MAP[event_type]
        ).transact({
            "from": self.account
        })

        receipt = self.w3.eth.wait_for_transaction_receipt(tx)

        return integrity_hash, receipt.transactionHash.hex()
