from backend.db import get_db_cursor
from web3 import Web3
from backend.config import settings
from eth_utils import to_checksum_address

w3 = Web3(Web3.HTTPProvider(settings.RPC_URL))
contract = w3.eth.contract(
    address=to_checksum_address(settings.CONTRACT_ADDRESS),
    abi=[{'inputs': [{'internalType': 'bytes32', 'name': 'eventHash', 'type': 'bytes32'}], 'name': 'anchored', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'}]
)

with get_db_cursor() as cursor:
    cursor.execute("SELECT event_hash FROM domain_events ORDER BY id DESC LIMIT 1")
    evt = cursor.fetchone()
    if evt:
        hex_hash = "0x" + evt['event_hash']
        is_anchored = contract.functions.anchored(w3.to_bytes(hexstr=hex_hash)).call()
        is_anchored = contract.functions.anchored(w3.to_bytes(hexstr=hex_hash)).call()
        print(f"Event Hash: {evt['event_hash']}")
        print(f"Anchored on Smart Contract: {is_anchored}")
    else:
        print("No events found in DB.")
