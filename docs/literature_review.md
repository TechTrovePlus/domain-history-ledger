# Literature Review

## Blockchain-Based Reputation Systems

Battah et al. (2021) discuss the challenges of implementing reputation systems using blockchain technology. 
The paper highlights that while blockchain provides immutability, transparency, and integrity, it is not 
suitable for heavy computation or large-scale data storage. Performing reputation scoring directly on-chain 
introduces scalability, cost, and determinism issues.

The authors recommend a hybrid architecture where blockchain is used strictly as an immutable audit layer, 
while all reputation computation, analytics, and data aggregation are handled off-chain. This separation 
ensures system scalability, flexibility, and practical deployability.

This project directly follows these recommendations by using the blockchain only to store immutable domain 
lifecycle events (domain registration, ownership change, and abuse flags). All reputation logic is computed 
off-chain using a Python backend, ensuring simplicity and efficiency while preserving trust through 
cryptographic immutability.

## Domain Name Reputation Systems

Rotună et al. (2023) propose a generic architecture for building domain name reputation systems based on 
historical data, domain behavior, ownership patterns, and external intelligence sources. Their work 
demonstrates that domain reputation is strongly influenced by domain history and lifecycle behavior rather 
than isolated real-time observations.

Traditional domain reputation systems described in the literature rely on centralized databases, machine 
learning models, and registry-controlled infrastructure. While effective, these systems suffer from a lack 
of transparency and public verifiability, allowing historical context to be lost during domain transfers or 
re-registration.

This project complements existing domain reputation architectures by introducing a permanent, decentralized 
domain history layer. Instead of replacing existing reputation systems, the proposed Domain History & 
Reputation Ledger provides a publicly verifiable memory layer that preserves domain history across ownership 
changes, preventing reputation laundering and historical erasure.

## Identified Research Gap

Existing domain reputation systems focus on detecting malicious behavior but do not ensure permanent 
historical memory. Blockchain-based reputation systems often attempt to perform excessive logic on-chain, 
leading to scalability and complexity issues.

The identified gap is the absence of a lightweight, neutral, and immutable domain history mechanism that 
preserves trust signals over time without enforcing decisions or performing heavy computation.

## Project Contribution

This project addresses the identified gap by:
- Treating domain trust as a historical problem rather than a real-time scoring problem
- Using blockchain strictly as an immutable audit log
- Preserving domain lifecycle events permanently
- Enabling reputation signals to be derived transparently off-chain

By combining principles from blockchain-based reputation research and domain reputation architectures, the 
project provides a novel and practical solution for preventing domain reputation laundering.
