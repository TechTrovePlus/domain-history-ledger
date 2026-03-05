// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DomainHistory {

    // Mapping to ensure event_hash cannot be anchored twice
    mapping(bytes32 => bool) public anchored;

    // Event emitted when a ledger hash is anchored
    event EventAnchored(
        bytes32 indexed eventHash,
        uint256 timestamp
    );

    /**
     * @notice Anchors a ledger event hash on-chain
     * @param eventHash SHA256 hash generated from backend ledger
     */
    function anchorEvent(bytes32 eventHash) external {
        require(!anchored[eventHash], "Event already anchored");

        anchored[eventHash] = true;

        emit EventAnchored(
            eventHash,
            block.timestamp
        );
    }
}