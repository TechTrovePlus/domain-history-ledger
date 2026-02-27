const { ethers } = require("hardhat");

async function main() {
  const CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3";

  const DomainHistory = await ethers.getContractAt(
    "DomainHistory",
    CONTRACT_ADDRESS
  );

  // Keccak-256 hash of a demo domain
  const domain = "old-scam-domain.com";
  const domainHash = ethers.utils.keccak256(
    ethers.utils.toUtf8Bytes(domain)
  );

  const tx = await DomainHistory.recordDomainEvent(
    domainHash,
    2 // ABUSE_FLAGGED
  );

  await tx.wait();

  console.log("Anchored ABUSE_FLAG for:", domain);
  console.log("Domain hash:", domainHash);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
