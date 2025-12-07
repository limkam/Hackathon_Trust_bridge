import { useEffect, useState } from 'react';
import { usePrivyAuth } from '../contexts/PrivyAuthContext';

export default function PrivyTest() {
  const privyAuth = usePrivyAuth();
  const [status, setStatus] = useState('Checking...');

  useEffect(() => {
    const checkPrivy = () => {
      const checks = {
        'Privy Context Available': !!privyAuth,
        'Is Fallback': privyAuth?._isFallback || false,
        'Ready State': privyAuth?.ready || false,
        'Has Login Function': typeof privyAuth?.login === 'function',
        'Hook Error': privyAuth?._hookError || 'None',
        'App ID in Env': process.env.NEXT_PUBLIC_PRIVY_APP_ID || 'Not found',
      };

      console.log('🔍 Privy Diagnostic:', checks);
      setStatus(JSON.stringify(checks, null, 2));
    };

    checkPrivy();
    const interval = setInterval(checkPrivy, 2000);
    return () => clearInterval(interval);
  }, [privyAuth]);

  const testLogin = async () => {
    try {
      console.log('Testing Privy login...');
      console.log('Privy auth object:', privyAuth);
      console.log('Ready state:', privyAuth?.ready);
      console.log('Is fallback:', privyAuth?._isFallback);
      
      // Use the context's login function (which handles ready state waiting)
      if (!privyAuth) {
        throw new Error('Privy auth context is not available');
      }
      
      if (privyAuth._isFallback) {
        throw new Error('Privy is using fallback mode. PrivyProvider may not be properly configured.');
      }
      
      console.log('Calling privyAuth.login()...');
      await privyAuth.login();
      
      console.log('Login test successful!');
    } catch (error) {
      console.error('Login test failed:', error);
      console.error('Full error:', error);
      alert('Login test failed: ' + error.message + '\n\nCheck console for details.');
    }
  };

  return (
    <div className="min-h-screen p-8 bg-gray-100">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold mb-4">Privy Diagnostic Page</h1>
        
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Status:</h2>
          <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm">
            {status}
          </pre>
        </div>

        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Actions:</h2>
          <button
            onClick={testLogin}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Test Privy Login
          </button>
        </div>

        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">What to Check:</h2>
          <ul className="list-disc list-inside space-y-2">
            <li>Open browser console (F12) to see detailed logs</li>
            <li>Check Network tab for requests to <code>auth.privy.io</code></li>
            <li>Verify "Is Fallback" is <strong>false</strong></li>
            <li>Verify "Ready State" becomes <strong>true</strong> after a few seconds</li>
            <li>If "Is Fallback" is true, PrivyProvider is not wrapping correctly</li>
          </ul>
        </div>

        <div className="text-sm text-gray-600">
          <p><strong>App ID:</strong> {process.env.NEXT_PUBLIC_PRIVY_APP_ID || 'Not configured'}</p>
          <p><strong>Environment:</strong> {process.env.NODE_ENV}</p>
        </div>
      </div>
    </div>
  );
}

