/**
 * Privy Authentication Context
 * Provides Privy authentication with automatic Solana wallet creation
 * Falls back to mock implementation if Privy is not configured
 */
import { createContext, useContext, useEffect, useState, useRef } from 'react';
import { Connection, PublicKey } from '@solana/web3.js';

const PRIVY_ENABLED = typeof window !== 'undefined' && 
  process.env.NEXT_PUBLIC_PRIVY_APP_ID && 
  process.env.NEXT_PUBLIC_PRIVY_APP_ID !== 'your-privy-app-id' &&
  process.env.NEXT_PUBLIC_PRIVY_APP_ID.trim() !== '';

// Import usePrivy hook - must be imported at module level for React hooks to work
let usePrivy = null;
if (PRIVY_ENABLED) {
  try {
    const privyModule = require('@privy-io/react-auth');
    usePrivy = privyModule.usePrivy;
  } catch (e) {
    console.warn('Privy not available, using fallback authentication:', e);
  }
}

const PrivyAuthContext = createContext();

export const usePrivyAuth = () => {
  const context = useContext(PrivyAuthContext);
  if (!context) {
    throw new Error('usePrivyAuth must be used within PrivyAuthProvider');
  }
  return context;
};

export const PrivyAuthProvider = ({ children }) => {
  // Fallback implementation when Privy is not configured
  const fallbackAuth = {
    ready: true,
    authenticated: false,
    user: null,
    login: async () => {
      console.warn('Privy not configured. Please set NEXT_PUBLIC_PRIVY_APP_ID in .env.local');
      return Promise.resolve();
    },
    logout: () => {
      console.warn('Privy not configured');
    },
    linkEmail: () => Promise.resolve(),
    linkWallet: () => Promise.resolve(),
    getAccessToken: () => Promise.resolve(null),
  };

  // Try to use Privy hook if available, otherwise use fallback
  // IMPORTANT: usePrivy() must be called inside a component that's wrapped by PrivyProvider
  // We check if we're inside PrivyProvider by trying to use the hook
  let privyHook;
  let hookError = null;
  
  // Always try to use Privy hook if it's available (even if PRIVY_ENABLED check fails)
  // This allows the hook to work when PrivyProvider is present
  if (usePrivy) {
    try {
      privyHook = usePrivy();
      // Debug logging
      if (typeof window !== 'undefined') {
        console.log('✅ Privy hook initialized successfully, ready:', privyHook?.ready);
        console.log('Privy hook has login function:', typeof privyHook?.login === 'function');
      }
    } catch (error) {
      hookError = error;
      // If error is about missing PrivyProvider, use fallback
      if (error.message?.includes('PrivyProvider') || error.message?.includes('wrap your application')) {
        console.error('❌ PrivyProvider not found when calling usePrivy():', error.message);
        console.error('This means PrivyAuthProvider is not inside PrivyProvider. Check _app.jsx structure.');
        privyHook = fallbackAuth;
      } else {
        console.error('❌ Error initializing Privy hook:', error);
        privyHook = fallbackAuth;
      }
    }
  } else {
    // usePrivy hook not available at all
    if (PRIVY_ENABLED) {
      console.warn('⚠️ Privy enabled but usePrivy hook not available - is @privy-io/react-auth installed?');
    }
    privyHook = fallbackAuth;
  }
  
  // Use ref to maintain privyHook reference and preserve context
  const privyHookRef = useRef(privyHook);
  useEffect(() => {
    privyHookRef.current = privyHook;
  }, [privyHook]);
  
  // Don't destructure login - we need to call it directly from privyHook to preserve context
  const ready = privyHook?.ready ?? false;
  const authenticated = privyHook?.authenticated ?? false;
  const user = privyHook?.user ?? null;
  const logout = privyHook?.logout ?? fallbackAuth.logout;
  const linkEmail = privyHook?.linkEmail ?? fallbackAuth.linkEmail;
  const linkWallet = privyHook?.linkWallet ?? fallbackAuth.linkWallet;
  const getAccessToken = privyHook?.getAccessToken ?? fallbackAuth.getAccessToken;

  // Debug: Log ready state changes and check Privy initialization
  useEffect(() => {
    if (typeof window !== 'undefined' && PRIVY_ENABLED && privyHook && privyHook !== fallbackAuth) {
      console.log('Privy ready state:', ready, 'PRIVY_ENABLED:', PRIVY_ENABLED, 'usePrivy available:', !!usePrivy);
      
      // Check if Privy scripts are loaded
      if (!ready) {
        console.log('Waiting for Privy to become ready...');
        const checkPrivy = setInterval(() => {
          // Re-check ready state from the hook
          if (privyHook?.ready) {
            console.log('✅ Privy is now ready!');
            clearInterval(checkPrivy);
          } else {
            console.log('⏳ Still waiting for Privy...');
          }
        }, 2000);
        
        // Clear after 30 seconds
        setTimeout(() => {
          clearInterval(checkPrivy);
          if (!privyHook?.ready) {
            console.warn('⚠️ Privy did not become ready after 30 seconds. This might indicate a configuration issue.');
          }
        }, 30000);
        
        return () => clearInterval(checkPrivy);
      } else {
        console.log('✅ Privy is ready!');
      }
    }
  }, [ready, PRIVY_ENABLED, privyHook]);

  const [solanaWallet, setSolanaWallet] = useState(null);
  const [solanaAddress, setSolanaAddress] = useState(null);
  const [userRole, setUserRole] = useState(null);

  // Get Solana wallet address from Privy
  useEffect(() => {
    if (authenticated && user) {
      // Privy automatically creates wallets for users
      // Get Solana wallet from Privy user
      const wallets = user?.linkedAccounts?.filter(
        (account) => account.type === 'wallet' && account.walletClientType === 'solana'
      );
      
      if (wallets && wallets.length > 0) {
        const solanaWallet = wallets[0];
        setSolanaWallet(solanaWallet);
        setSolanaAddress(solanaWallet.address);
      } else {
        // If no Solana wallet exists, create one via Privy
        // Privy will handle wallet creation on first use
        setSolanaAddress(null);
      }

      // Get user role from Privy metadata or backend
      // For now, default to investor if not set
      const role = user?.metadata?.role || 'investor';
      setUserRole(role);
    } else {
      setSolanaWallet(null);
      setSolanaAddress(null);
      setUserRole(null);
    }
  }, [authenticated, user]);

  // Ensure Solana wallet is linked
  const ensureSolanaWallet = async () => {
    if (!authenticated) {
      await wrappedLogin();
      return;
    }

    if (!solanaAddress) {
      // Link Solana wallet via Privy
      try {
        await linkWallet('solana');
      } catch (error) {
        console.error('Failed to link Solana wallet:', error);
      }
    }
  };

  // Wrap login to provide better error handling
  // IMPORTANT: Call login directly from privyHookRef to preserve React context binding
  const wrappedLogin = async (...args) => {
    const currentHook = privyHookRef.current;
    
    console.log('🔐 wrappedLogin called');
    console.log('🔐 currentHook === fallbackAuth:', currentHook === fallbackAuth);
    console.log('🔐 ready state:', ready);
    console.log('🔐 currentHook exists:', !!currentHook);
    console.log('🔐 currentHook.login type:', typeof currentHook?.login);
    console.log('🔐 currentHook.ready:', currentHook?.ready);
    
    if (currentHook === fallbackAuth || !currentHook) {
      console.error('❌ Cannot login: Using fallback Privy (PrivyProvider not found)');
      const error = new Error('Privy is not properly configured. PrivyProvider may not be wrapping the app correctly. Check _app.jsx to ensure PrivyProvider wraps PrivyAuthProvider.');
      error.name = 'PrivyNotConfigured';
      throw error;
    }
    
    // Check if we have the real login function from privyHook
    const loginFn = currentHook.login;
    if (!loginFn || typeof loginFn !== 'function') {
      console.error('❌ Cannot login: Login function not available from privyHook');
      console.error('currentHook contents:', Object.keys(currentHook || {}));
      const error = new Error('Privy login function is not available. Privy may still be initializing. Try waiting a few seconds.');
      error.name = 'PrivyNotReady';
      throw error;
    }
    
    // CRITICAL: Wait for ready state - Privy's login() will fail if not ready
    const currentReady = currentHook.ready ?? ready;
    if (!currentReady) {
      console.warn('⚠️ Privy not ready yet. Waiting for initialization...');
      console.warn('  Current ready state:', currentReady);
      console.warn('  currentHook.ready:', currentHook?.ready);
      
      // Wait up to 10 seconds for Privy to become ready
      let attempts = 0;
      const maxAttempts = 20; // 20 * 500ms = 10 seconds
      
      while (!currentHook.ready && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 500));
        attempts++;
        
        // Re-check ready from the hook
        if (currentHook.ready) {
          console.log('✅ Privy became ready after', attempts * 500, 'ms!');
          break;
        }
        
        // Log progress every 2 seconds
        if (attempts % 4 === 0) {
          console.log(`⏳ Still waiting for Privy... (${attempts * 500}ms elapsed)`);
        }
      }
      
      // Final check - if still not ready, throw helpful error
      if (!currentHook.ready) {
        console.error('❌ Privy did not become ready after 10 seconds');
        console.error('This usually means:');
        console.error('  1. Privy scripts are not loading (check Network tab for auth.privy.io)');
        console.error('  2. PrivyProvider is not properly configured');
        console.error('  3. App ID might be invalid or domain not whitelisted');
        console.error('  4. Browser extensions might be blocking Privy scripts');
        
        const error = new Error('Privy is not ready. Please wait a few seconds and try again. If the problem persists, check the browser console for Privy initialization errors.');
        error.name = 'PrivyNotReady';
        error.ready = false;
        error.waited = attempts * 500;
        throw error;
      }
    }
    
    // Verify login function is still available after waiting
    if (!currentHook.login || typeof currentHook.login !== 'function') {
      console.error('❌ Login function disappeared after waiting');
      const error = new Error('Privy login function is not available. This might indicate a context issue.');
      error.name = 'PrivyLoginUnavailable';
      throw error;
    }
    
    try {
      console.log('✅ Privy is ready! Calling login function...');
      console.log('  Ready state:', currentHook.ready);
      console.log('  Login function type:', typeof currentHook.login);
      
      // Call login directly from currentHook to preserve React context
      // Use .apply() to ensure proper context binding
      return await loginFn.apply(currentHook, args);
    } catch (error) {
      console.error('❌ Privy login error:', error);
      console.error('Error details:', {
        message: error.message,
        name: error.name,
        ready: currentHook?.ready,
        hasLogin: typeof currentHook?.login === 'function',
        currentHookType: currentHook === fallbackAuth ? 'fallback' : 'real',
      });
      
      // If error is about PrivyProvider, provide more context
      if (error.message?.includes('PrivyProvider') || error.message?.includes('wrap your application')) {
        console.error('🔍 Debugging PrivyProvider context:');
        console.error('  - Check that PrivyProvider wraps PrivyAuthProvider in _app.jsx');
        console.error('  - Verify NEXT_PUBLIC_PRIVY_APP_ID is set correctly');
        console.error('  - Check browser console for Privy initialization errors');
        console.error('  - Check Network tab for requests to auth.privy.io');
      }
      
      // If error is about PrivyProvider, provide helpful message
      if (error.message?.includes('PrivyProvider') || error.message?.includes('wrap your application')) {
        const helpfulError = new Error('Privy login failed: PrivyProvider context not found. This usually means Privy is not fully initialized. The ready state is: ' + currentReady + '. Try waiting a few seconds and refreshing the page.');
        helpfulError.name = 'PrivyProviderNotFound';
        helpfulError.originalError = error;
        throw helpfulError;
      }
      
      throw error;
    }
  };

  const value = {
    ready,
    authenticated,
    user,
    login: wrappedLogin,
    logout,
    linkEmail,
    solanaWallet,
    solanaAddress,
    userRole,
    ensureSolanaWallet,
    getAccessToken,
    isInvestor: userRole === 'investor',
    isStartup: userRole === 'startup' || userRole === 'founder',
    // Debug info
    _isFallback: privyHook === fallbackAuth,
    _hookError: hookError?.message,
  };

  return (
    <PrivyAuthContext.Provider value={value}>
      {children}
    </PrivyAuthContext.Provider>
  );
};

