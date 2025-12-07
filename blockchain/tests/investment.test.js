const { investUSDC } = require("../scripts/investUSDC");
const { registerStartup } = require("../scripts/registerStartup");

describe("Investment Ledger Tests", () => {
  let startupId;
  const mockInvestorAddress = "FB7xNwme7h5VZxTMa26jmGQqfz4dJGrsaGDx1ZRbfX5t"; // Valid Solana address format

  beforeAll(async () => {
    // Register a test startup first
    const startupResult = await registerStartup({
      startupName: "Test Startup for Investment",
      sector: "Technology",
      founderAddress: "FB7xNwme7h5VZxTMa26jmGQqfz4dJGrsaGDx1ZRbfX5t",
    });
    startupId = startupResult.startupId;
  }, 30000);

  test("should record an investment successfully", async () => {
    const result = await investUSDC({
      investorAddress: mockInvestorAddress,
      startupId: startupId,
      amountUSDC: 1000,
    });

    expect(result).toHaveProperty("investmentId");
    expect(result).toHaveProperty("transactionSignature");
    expect(result).toHaveProperty("confirmationUrl");
    expect(result).toHaveProperty("blockchainProof");

    expect(result.investmentId).toContain("INV-");
    expect(result.blockchainProof.amountUSDC).toBe(1000);
    expect(result.blockchainProof.status).toBe("confirmed");
  }, 30000);

  test("should record multiple investments", async () => {
    const investments = [
      { amountUSDC: 500 },
      { amountUSDC: 1500 },
      { amountUSDC: 2500 },
    ];

    const results = await Promise.all(
      investments.map((inv) =>
        investUSDC({
          investorAddress: mockInvestorAddress,
          startupId: startupId,
          amountUSDC: inv.amountUSDC,
        })
      )
    );

    expect(results).toHaveLength(3);
    results.forEach((result, index) => {
      expect(result).toHaveProperty("investmentId");
      expect(result.blockchainProof.amountUSDC).toBe(
        investments[index].amountUSDC
      );
    });
  }, 60000);
});
