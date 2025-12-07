#!/bin/bash
# Airdrop SOL to founder wallets for startup registration

echo "Airdropping SOL to founder wallets..."

# Founder wallets (from seed data)
FOUNDER_1="BhLh32RvnYxF3qesVxkjgKjPpg9gUF24oFUPDM3VkwW6"  # David
FOUNDER_2="AcYnQ3GHDHF5e8NojkCZVGo294RpJNSqqSgNkWnCQDzH"  # Hawa

echo "Airdropping to David (Founder 1)..."
solana airdrop 2 "$FOUNDER_1" || echo "Rate limited, will retry later"

sleep 5

echo "Airdropping to Hawa (Founder 2)..."
solana airdrop 2 "$FOUNDER_2" || echo "Rate limited, will retry later"

echo "Done! Check balances:"
solana balance "$FOUNDER_1"
solana balance "$FOUNDER_2"

