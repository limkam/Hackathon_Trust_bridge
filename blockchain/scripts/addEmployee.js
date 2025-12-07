const {
  Connection,
  Keypair,
  PublicKey,
  SystemProgram,
  Transaction,
  TransactionInstruction,
} = require("@solana/web3.js");
const fs = require("fs");
const path = require("path");

/**
 * Adds an employee with verified certificate to a startup using raw Solana transactions
 * Verifies certificate exists on-chain before adding
 * @param {Object} params - Employee parameters
 * @param {string} params.startupId - Startup ID
 * @param {string} params.certificateId - Certificate ID of the employee
 * @param {string} params.employeeAddress - Solana address of the employee (signer)
 * @returns {Promise<Object>} Employee addition result with transaction signature
 */
async function addEmployee({ startupId, certificateId, employeeAddress }) {
  try {
    // Connect to Solana Devnet
    const connection = new Connection(
      "https://api.devnet.solana.com",
      "confirmed"
    );

    // Load wallet (employee must sign)
    const homeDir = process.env.HOME || process.env.USERPROFILE;
    const walletPath =
      process.env.WALLET_PATH || path.join(homeDir, ".config/solana/id.json");
    const walletKeypair = Keypair.fromSecretKey(
      new Uint8Array(JSON.parse(fs.readFileSync(walletPath, "utf-8")))
    );

    // Program IDs
    const startupProgramId = new PublicKey(
      "DqwhC5DDZZmL4E1f4YYQJ9R121NurZV8ttk2dfGoYnTj"
    );
    const certificateProgramId = new PublicKey(
      "D7SYneSxju3iTtJW9HPQMVjQRXgTCZi2vR2UWRk8nTRa"
    );

    // Find PDAs
    const [startupPDA] = await PublicKey.findProgramAddress(
      [Buffer.from("startup"), Buffer.from(startupId)],
      startupProgramId
    );

    const [certificatePDA] = await PublicKey.findProgramAddress(
      [Buffer.from("certificate"), Buffer.from(certificateId)],
      certificateProgramId
    );

    // Parse employee address
    const employeePubkey = new PublicKey(employeeAddress);

    // Instruction discriminator for add_employee: [14, 82, 239, 156, 50, 90, 189, 61]
    const instructionDiscriminator = Buffer.from([
      14, 82, 239, 156, 50, 90, 189, 61,
    ]);

    // Serialize string (Anchor format: 4 bytes length + UTF-8)
    const serializeString = (str) => {
      const utf8 = Buffer.from(str, "utf-8");
      const len = Buffer.alloc(4);
      len.writeUInt32LE(utf8.length, 0);
      return Buffer.concat([len, utf8]);
    };

    const args = Buffer.concat([serializeString(certificateId)]);
    const instructionData = Buffer.concat([instructionDiscriminator, args]);

    // Create instruction
    const instruction = new TransactionInstruction({
      keys: [
        {
          pubkey: startupPDA,
          isSigner: false,
          isWritable: true,
        },
        {
          pubkey: employeePubkey,
          isSigner: true,
          isWritable: false,
        },
        {
          pubkey: certificatePDA,
          isSigner: false,
          isWritable: false,
        },
        {
          pubkey: certificateProgramId,
          isSigner: false,
          isWritable: false,
        },
      ],
      programId: startupProgramId,
      data: instructionData,
    });

    // Create transaction
    const transaction = new Transaction().add(instruction);

    // Get recent blockhash
    const { blockhash } = await connection.getLatestBlockhash("confirmed");
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = walletKeypair.publicKey;

    // Sign and send transaction
    transaction.sign(walletKeypair);
    const signature = await connection.sendRawTransaction(
      transaction.serialize(),
      {
        skipPreflight: false,
        maxRetries: 3,
      }
    );

    // Confirm transaction
    await connection.confirmTransaction(signature, "confirmed");

    // Return result
    return {
      startupId,
      certificateId,
      transactionSignature: signature,
      blockchainProof: {
        network: "Solana Devnet",
        startupProgramId: startupProgramId.toString(),
        certificateProgramId: certificateProgramId.toString(),
        startupAccount: startupPDA.toString(),
        certificateAccount: certificatePDA.toString(),
        transactionSignature: signature,
        verificationUrl: `https://explorer.solana.com/tx/${signature}?cluster=devnet`,
      },
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    console.error("Error adding employee:", error);
    throw new Error(`Failed to add employee: ${error.message}`);
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 3) {
    console.error(
      "Usage: node addEmployee.js <startupId> <certificateId> <employeeAddress>"
    );
    process.exit(1);
  }

  addEmployee({
    startupId: args[0],
    certificateId: args[1],
    employeeAddress: args[2],
  })
    .then((result) => {
      console.log(JSON.stringify(result, null, 2));
    })
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

module.exports = { addEmployee };
