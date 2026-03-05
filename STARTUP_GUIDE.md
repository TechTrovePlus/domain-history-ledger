# DNS Guard Startup Guide

Welcome to the **DNS Guard Analytics Engine**. This system consists of multiple moving parts designed to build an append-only cryptographic event ledger of domain intelligence.

This guide provides the full procedure for cleanly starting, stopping, and troubleshooting the system.

---

## 🏗️ SECTION 1 — System Overview

DNS Guard is a multi-tiered architecture that runs on several independent processes:

*   **Frontend UI:** A glassmorphism HTML/JS dashboard providing the visual interface.
*   **Backend Flask API:** The core orchestration layer that handles business logic and routes.
*   **PostgreSQL Database:** The persistent storage for domain states and historical ledgers.
*   **Diff Monitoring Worker:** A continuous background process monitoring domains for lifecycle changes (RDAP variations).
*   **Blockchain Anchoring Worker:** A background daemon that cryptographic proofs event hashes locally or to Mainnet.
*   **Optional Hardhat Blockchain Node:** A local Ethereum execution environment for validating smart contract anchors.

These components run independently but communicate securely through the underlying API and database layer.

---

## 🚀 SECTION 2 — Full Startup Procedure

The system relies on the database being available before the APIs and workers boot. Follow this exact startup order.

### 1️⃣ Start PostgreSQL

The entire analytical ledger is built on PostgreSQL. Start the database first:

```powershell
docker-compose up -d db
```
*(This gracefully boots the PostgreSQL container in the background. The ledger strictly depends on this service.)*

### 2️⃣ Start Backend API

The Python backend handles the Oracles (RDAP, URLhaus) and the active PostgreSQL connection pool.

Open a new terminal and activate your virtual environment:

**PowerShell (Windows Default):**
```powershell
.\venv\Scripts\Activate
```

**Git Bash / MINGW64:**
```bash
source venv/Scripts/activate
```

Run the backend:

**PowerShell:**
```powershell
$env:PYTHONPATH="."; python backend\app.py
```

**Git Bash / MINGW64:**
```bash
PYTHONPATH="." python backend/app.py
```
*Confirm the server runs at: `http://127.0.0.1:5000`*

### 3️⃣ Start Frontend Server

The frontend requires a separate local server to avoid CORS issues.

Open a second terminal and activate the environment (if not already active):

**PowerShell:**
```powershell
.\venv\Scripts\Activate
```

**Git Bash / MINGW64:**
```bash
source venv/Scripts/activate
```

Run the UI server:

**PowerShell:**
```powershell
$env:PYTHONPATH="."; python serve_frontend.py
```

**Git Bash / MINGW64:**
```bash
PYTHONPATH="." python serve_frontend.py
```
*Confirm the UI runs at: `http://localhost:8000`*

### 4️⃣ Start Blockchain Node (Optional)

If you intend to test real on-chain transaction hashes, boot the local Hardhat Node. 

Open a third terminal and run:
```bash
cd blockchain
npx hardhat node
```
*This enables real blockchain anchoring locally on port `8545`.*

### 5️⃣ Worker Containers

**Note:** `docker-compose` automatically manages the persistent daemon components. When you run `docker-compose up -d` (or starting them via Docker Desktop), it automatically spins up:
*   `anchoring_worker`
*   `diff_monitor_worker`

These run silently in the background and process intelligence events and anchors automatically.

---

## 🛑 SECTION 3 — System Shutdown Procedure

To prevent data corruption or orphaned ports, shut the system down in this order:

**Step 1** – Stop the Frontend server (Press `CTRL + C` in its terminal)  
**Step 2** – Stop the Backend server (Press `CTRL + C` in its terminal)  
**Step 3** – Stop the Hardhat node if running (Press `CTRL + C` in its terminal)  
**Step 4** – Stop all Docker containers:  

```powershell
docker-compose down
```
*(This cleanly stops the PostgreSQL database and safely terminates both the diff and anchoring worker containers without dropping volumes).*

---

## 🔄 SECTION 4 — Restarting the System

Unless you fully tore down the Docker containers, restarting usually only requires:

```powershell
docker-compose up -d db
```

Then restarting the backend (`app.py`) and frontend (`serve_frontend.py`). Note that because we use persistent Docker volumes, **database data remains entirely intact** between restarts.

---

## 🛠️ SECTION 5 — Troubleshooting

### PORT ALREADY IN USE
**Symptom:** `OSError: [WinError 10048] Only one usage of each socket address is normally permitted`  
**Solution:** Stop existing Python processes that may have lost their terminal connection, or fully restart your terminal.

```powershell
Get-WmiObject Win32_Process | Where-Object {$_.CommandLine -like '*serve_frontend.py*'} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Get-WmiObject Win32_Process | Where-Object {$_.CommandLine -like '*backend\app.py*'} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

### DATABASE CONNECTION ERROR
**Symptom:** `psycopg2.OperationalError: connection to server at "localhost" failed`  
**Solution:** Ensure the Docker PostgreSQL container is actually running. Verify by running `docker ps` and re-running `docker-compose up -d db`.

### BLOCKCHAIN NOT ANCHORING
**Symptom:** Events remain marked as 'Queued' indefinitely in the timeline.  
**Solution:** Ensure the Hardhat node is actively running on port `8545` and that the `anchoring_worker` container hasn't crashed.

---

## 💻 SECTION 6 — Recommended Development Workflow

1. Start DB (`docker-compose up -d db`)
2. Start backend (`python backend\app.py`)
3. Start frontend (`python serve_frontend.py`)
4. Optionally start Hardhat node (`cd blockchain && npx hardhat node`)

Then open your browser to: **http://localhost:8000** and search a domain.

---

## ⚠️ SECTION 7 — Safety Note

DNS Guard is a heavy orchestration engine. The system utilizes:
*   Continuous background workers
*   Asynchronous Cold Start ingestion paths
*   Cryptographic event ledger hashing

Because of this intensive intelligence gathering pipeline, **the first time a domain is searched it may take several seconds** to compile the initial baseline. Subsequent visits check the persistent database cache resulting in near-instant load times.
