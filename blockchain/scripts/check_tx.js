async function main() {
    const tx = await ethers.provider.getTransactionReceipt('0x8c7bb554db22c15981ab28fd5751996ab427f7a7da984a132ba2fba96fa2c5a1');
    console.log(tx);
    const contract = await ethers.getContractAt('DomainHistory', '0x2279B7A0a67DB372996a5FaB50D91eAA73d2eBe6');
    const logs = await contract.queryFilter('EventAnchored');
    console.log("All anchored events:");
    logs.forEach(l => console.log(l.args.eventHash));
}
main().catch(console.error);
