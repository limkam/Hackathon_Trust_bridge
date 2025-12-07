/**
 * PrivyWrapper - Ensures PrivyProvider is always present when PrivyAuthProvider renders
 * This prevents timing issues where usePrivy() is called before PrivyProvider mounts
 */
import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

const PRIVY_APP_ID = process.env.NEXT_PUBLIC_PRIVY_APP_ID;
const PRIVY_ENABLED = PRIVY_APP_ID && PRIVY_APP_ID !== 'your-privy-app-id' && PRIVY_APP_ID.trim() !== '';

// Dynamically import PrivyProvider
const PrivyProvider = PRIVY_ENABLED
  ? dynamic(
      () => import('@privy-io/react-auth').then((mod) => mod.PrivyProvider),
      { ssr: false }
    )
  : null;

export default function PrivyWrapper({ children }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // On server or before mount, render children without PrivyProvider
  // PrivyAuthProvider will use fallback mode
  if (!PRIVY_ENABLED || !PrivyProvider || !mounted) {
    return <>{children}</>;
  }

  // Once mounted on client, render with PrivyProvider
  return (
    <PrivyProvider
      appId={PRIVY_APP_ID}
      config={{
        loginMethods: ['email', 'google', 'twitter', 'github'],
        appearance: {
          theme: 'dark',
          accentColor: '#3b82f6',
        },
        embeddedWallets: {
          createOnLogin: 'users-without-wallets',
          requireUserPasswordOnCreate: false,
          noPromptOnSignature: false,
        },
        // Don't configure externalWallets - we're using embedded wallets only
        // If Solana external wallet login is enabled in Privy dashboard, disable it there
      }}
      onSuccess={(user) => {
        console.log('✅ PrivyProvider onSuccess - User authenticated:', user?.id);
      }}
    >
      {children}
    </PrivyProvider>
  );
}

