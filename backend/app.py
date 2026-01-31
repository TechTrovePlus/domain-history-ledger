from flask import Flask, jsonify
from web3 import Web3
import sqlite3
from eth_utils import keccak, to_hex

app = Flask(__name__)

# --- CONFIG ---
DB_PATH = "backend/dns_guard.db"
RPC_URL = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "domainHash", "type": "bytes32"},
            {"indexed": False, "internalType": "uint8", "name": "eventType", "type": "uint8"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "DomainEventRecorded",
        "type": "event"
    }
]

# --- Web3 setup ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)


def get_domain_from_db(domain):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, domain_name, current_status FROM domains WHERE domain_name = ?",
        (domain,)
    )
    row = cursor.fetchone()
    conn.close()

    return row


def is_domain_on_blockchain(domain):
    domain_hash = keccak(text=domain)
    logs = contract.events.DomainEventRecorded().get_logs(
    from_block=0,
    argument_filters={"domainHash": domain_hash}
)

    return len(logs) > 0


@app.route("/search/<domain>")
def search(domain):
    record = get_domain_from_db(domain)

    if not record:
        return jsonify({
            "domain": domain,
            "status": "UNKNOWN",
            "blockchain_verified": False
        })

    _, name, status = record
    verified = is_domain_on_blockchain(name)

    return jsonify({
        "domain": name,
        "status": status,
        "blockchain_verified": verified
    })


if __name__ == "__main__":
    app.run(debug=True)
