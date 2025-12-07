#!/usr/bin/env node

/**
 * Post-build script to add 'size' property to IDL account definitions
 * Anchor doesn't include size in generated IDL files, but it's required for Program initialization
 */

const fs = require("fs");
const path = require("path");

const idlDir = path.join(__dirname, "../target/idl");

const accountSizes = {
  Certificate: 470,
  Startup: 1156,
  Investment: 256,
};

function fixIdlFile(filePath) {
  try {
    const idl = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    let modified = false;

    if (idl.accounts && Array.isArray(idl.accounts)) {
      for (const acc of idl.accounts) {
        if (acc && acc.name && !acc.size) {
          acc.size = accountSizes[acc.name] || 1000;
          modified = true;
        }
      }
    }

    if (modified) {
      fs.writeFileSync(filePath, JSON.stringify(idl, null, 2));
      console.log(`✓ Fixed ${path.basename(filePath)}`);
      return true;
    }
    return false;
  } catch (error) {
    console.error(`Error fixing ${filePath}:`, error.message);
    return false;
  }
}

// Fix all IDL files
const idlFiles = [
  "certificate_registry.json",
  "startup_registry.json",
  "investment_ledger.json",
];

let fixed = 0;
for (const file of idlFiles) {
  const filePath = path.join(idlDir, file);
  if (fs.existsSync(filePath)) {
    if (fixIdlFile(filePath)) {
      fixed++;
    }
  }
}

if (fixed > 0) {
  console.log(`\n✓ Fixed ${fixed} IDL file(s)`);
} else {
  console.log("\n✓ All IDL files already have size properties");
}
