import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../lib/api';
import { useRouter } from 'next/router';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Helper to safely get Privy auth
const usePrivyAuthSafe = () => {
  try {
    const { usePrivyAuth } = require('./PrivyAuthContext');
    return usePrivyAuth();
  } catch (e) {
    return null;
  }
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Get Privy auth state (safely)
  const privyAuth = usePrivyAuthSafe();

  // Sync Privy user with backend
  useEffect(() => {
    const syncPrivyUser = async () => {
      if (privyAuth && privyAuth.authenticated && privyAuth.user && !user) {
        try {
          // Get Privy user data
          const privyUser = privyAuth.user;
          const email = privyUser.email?.address || privyUser.linkedAccounts?.find(acc => acc.type === 'email')?.address;
          
          if (!email) {
            setLoading(false);
            return;
          }

          // Get Solana wallet from Privy
          const solanaWallet = privyAuth.solanaAddress || 
            privyUser.linkedAccounts?.find(acc => acc.type === 'wallet' && acc.walletClientType === 'solana');

          // Sync with backend
          const syncData = {
            privy_id: privyUser.id,
            email: email,
            full_name: privyUser.name || email.split('@')[0],
            wallet_address: solanaWallet?.address || solanaWallet || null,
            role: privyAuth.userRole || 'investor', // Default to investor
          };

          const response = await authAPI.syncPrivy(syncData);
          const backendUser = response.data;

          // Store token and user
          if (backendUser.access_token) {
    if (typeof window !== 'undefined') {
              localStorage.setItem('token', backendUser.access_token);
              localStorage.setItem('user', JSON.stringify(backendUser));
            }
            setToken(backendUser.access_token);
            setUser(backendUser);
          }
        } catch (error) {
          console.error('Failed to sync Privy user:', error);
        }
      }
      setLoading(false);
    };

    syncPrivyUser();
  }, [privyAuth?.authenticated, privyAuth?.user, privyAuth?.solanaAddress]);

  useEffect(() => {
    // Check for stored token on mount (for non-Privy users)
    if (typeof window !== 'undefined' && !privyAuth?.authenticated) {
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      }
    }
    if (!privyAuth?.authenticated) {
    setLoading(false);
    }
  }, [privyAuth?.authenticated]);

  // Helper function to extract error message from API response
  const extractErrorMessage = (error) => {
    const detail = error.response?.data?.detail;
    if (!detail) return error.message || 'An error occurred';
    
    // Handle Pydantic validation errors (array of objects)
    if (Array.isArray(detail)) {
      return detail.map(err => err.msg || JSON.stringify(err)).join(', ');
    }
    
    // Handle object with message property
    if (typeof detail === 'object' && detail !== null) {
      return detail.msg || detail.message || JSON.stringify(detail);
    }
    
    // Handle string
    return String(detail);
  };

  const login = async (email, password) => {
    try {
      const response = await authAPI.login({ email, password });
      const { access_token, user_id, role } = response.data;
      
      // Store token and user info
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify({ id: user_id, role }));
      }
      
      setToken(access_token);
      setUser({ id: user_id, role });
      
      // Fetch full user data
      const userData = await authAPI.getUser(user_id);
      const fullUser = userData.data;
      setUser(fullUser);
      
      return { success: true, user: fullUser };
    } catch (error) {
      return { 
        success: false, 
        error: extractErrorMessage(error)
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      // Auto-login after registration
      return await login(userData.email, userData.password);
    } catch (error) {
      return { 
        success: false, 
        error: extractErrorMessage(error)
      };
    }
  };

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
    setToken(null);
    setUser(null);
    
    // Also logout from Privy if available
    if (privyAuth && privyAuth.logout) {
      privyAuth.logout();
    }
    
    router.push('/');
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

