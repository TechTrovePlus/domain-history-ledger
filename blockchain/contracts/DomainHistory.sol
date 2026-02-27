// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DomainHistory {

    // Enum representing domain lifecycle events
    enum EventType {
        DOMAIN_REGISTERED,
        OWNERSHIP_CHANGED,
        ABUSE_FLAGGED
    }

    // Event emitted for every domain history action
    event DomainEventRecorded(
        bytes32 indexed domainHash,
        EventType eventType,
        uint256 timestamp
    );

    /**
     * @notice Records a domain lifecycle event on the blockchain
     * @param domainHash Keccak256 hash of the domain name
     * @param eventType Type of domain event
     */
    function recordDomainEvent(
        bytes32 domainHash,
        EventType eventType
    ) external {
        emit DomainEventRecorded(
            domainHash,
            eventType,
            block.timestamp
        );
    }
}
