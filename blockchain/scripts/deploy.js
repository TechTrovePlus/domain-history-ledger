const { ethers } = require("hardhat");

async function main() {
  const DomainHistory = await ethers.getContractFactory("DomainHistory");
  const contract = await DomainHistory.deploy();
  await contract.deployed();

  console.log("DomainHistory deployed to:", contract.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
