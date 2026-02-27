# 🛡️ DNS Guard

## Domain History & Reputation Ledger

DNS Guard is a mini-project that provides a **permanent, tamper-resistant history of internet domains** by combining traditional databases with blockchain as an **immutable audit log**.

The system is designed to prevent **domain reputation laundering**, where malicious actors reuse expired or transferred domains by erasing their past abuse history.

---

## ⚠️ Problem Statement — Reputation Laundering

Current domain reputation systems suffer from a critical flaw:

* When a domain **expires** or **changes ownership**, its historical reputation is often lost.
* Attackers exploit this gap by re-registering or buying old domains and reusing them for phishing and scams.
* Users and security tools see the domain as “clean” again.

This creates a **trust reset problem**.

---

## 💡 Solution — DNS Guard

DNS Guard solves this by introducing a **Domain History Ledger**:

* Every significant domain event (abuse, ownership change) is recorded.
* **Critical events are cryptographically anchored on the blockchain** using Keccak-256 hashes.
* Once anchored, history **cannot be erased or rewritten** — even if the domain changes hands.

The blockchain acts as a **neutral notary**, while all computation remains off-chain.

---

## 🏗️ System Architecture (Modules)

### 1️⃣ Blockchain Layer — *The Notary*

**Technology:** Solidity, Hardhat, Ethereum (Local Test Network)

* Stores **immutable hashes** of domain events.
* Records:

  * Abuse flags
  * Ownership changes
* Does **not** calculate reputation or store domain names.
* Used selectively for **proof**, not bulk storage.

---

### 2️⃣ Ingestion Module — *The Watchman*

**Technology:** Python

* Detects malicious or suspicious domains.
* In this prototype:

  * Uses **mock and curated demo data** to simulate real-world detection.
* Designed to integrate live OSINT feeds (URLhaus, PhishTank) as **future work**.

---

### 3️⃣ Backend & Storage Layer — *The Brain*

**Technology:** Python, Flask, SQLite

* Maintains **rich domain records** in SQLite.
* Maps database records to blockchain transaction proofs.
* Applies trust logic:

  * **GREEN** – Clean history
  * **YELLOW** – New domain or recent ownership change
  * **RED** – Verified abuse history

---

### 4️⃣ Presentation Layer — *The Interface*

**Technology:** HTML, CSS (Bootstrap), JavaScript

* Simple, non-technical UI.
* Allows users to:

  * Search a domain
  * Instantly see its trust status
  * Verify whether history is anchored on blockchain

---

## 🛠️ Technical Implementation Details

### 🔐 Integrity Standard — Keccak-256 Anchoring

DNS Guard uses **Ethereum-native Keccak-256 hashing**:

1. A domain event is detected (e.g., abuse).
2. A hash is generated off-chain.
3. The hash is anchored on the blockchain.
4. Later verification recomputes the hash and checks its existence on-chain.

This ensures:

* Immutability
* Verifiability
* Gas efficiency

---

### 🗄️ Database Schema (SQLite)

**domains**

* `domain_name`
* `first_seen`
* `current_status` (GREEN / YELLOW / RED)

**domain_events**

* `event_type` (REGISTERED, OWNERSHIP_CHANGED, ABUSE_FLAG)
* `event_time`
* `blockchain_tx`
* `integrity_hash`

---

## 🚀 Demo Workflow

1. User searches a domain in the UI.
2. Backend retrieves domain data from SQLite.
3. If applicable, backend verifies the event hash on the blockchain.
4. UI displays:

   * Traffic-light trust status
   * Blockchain verification indicator

### Demo Scenarios

* **Clean Domain** → GREEN
* **Typosquatter / New Domain** → YELLOW
* **Zombie Domain (Historic Abuse)** → RED (Verified on Blockchain)

---

## 🔬 Research Foundation

The project is informed by academic research on:

* Blockchain-based reputation systems
* Domain lifecycle and reputation persistence

The architecture follows best practices by:

* Using blockchain **only as a trust anchor**
* Performing analytics and reputation logic **off-chain**

---

## 🔮 Future Work

* Integration with live OSINT feeds (URLhaus, PhishTank)
* Automated ownership change detection
* Public testnet deployment
* Evidence hashing (screenshots, reports)
* Production-grade configuration management

---

## 📌 Project Scope Note

This project is a **proof-of-concept prototype** focused on demonstrating:

* Architecture correctness
* Trust guarantees
* Immutability of domain history

It prioritizes **reliability and clarity over real-time automation**, making it suitable for academic evaluation and live demonstrations.


