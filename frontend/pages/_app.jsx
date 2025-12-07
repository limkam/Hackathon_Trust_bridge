import '../styles/globals.css';
import { AuthProvider } from '../contexts/AuthContext';
import { PrivyAuthProvider } from '../contexts/PrivyAuthContext';
import PrivyWrapper from '../components/PrivyWrapper';
import { Toaster } from 'react-hot-toast';
import Layout from '../components/Layout';
import Head from 'next/head';
import { useEffect } from 'react';

// Check if Privy App ID is configured
const PRIVY_APP_ID = process.env.NEXT_PUBLIC_PRIVY_APP_ID;
const PRIVY_ENABLED = PRIVY_APP_ID && PRIVY_APP_ID !== 'your-privy-app-id' && PRIVY_APP_ID.trim() !== '';

function MyApp({ Component, pageProps }) {
  // Register Service Worker for PWA
  useEffect(() => {
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      // Register service worker
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          console.log('✅ Service Worker registered:', registration.scope);
          
          // Check for updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  console.log('🔄 New service worker available');
                  // Optionally show update notification to user
                }
              });
            }
          });
        })
        .catch((error) => {
          console.log('❌ Service Worker registration failed:', error);
        });

      // Handle service worker updates
      let refreshing = false;
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
          refreshing = true;
          window.location.reload();
        }
      });
    }

    // Debug: Log Privy configuration on mount
    if (typeof window !== 'undefined') {
      console.log('🔍 Privy Configuration Check:');
      console.log('  PRIVY_ENABLED:', PRIVY_ENABLED);
      console.log('  PRIVY_APP_ID:', PRIVY_APP_ID ? `${PRIVY_APP_ID.substring(0, 10)}...` : 'NOT SET');
      console.log('  Environment:', process.env.NODE_ENV);
      console.log('  Using PrivyWrapper component');
      
      // Check if Privy scripts are being loaded
      const checkPrivyScripts = setInterval(() => {
        const scripts = Array.from(document.querySelectorAll('script[src*="privy"], script[src*="auth.privy.io"]'));
        if (scripts.length > 0) {
          console.log('✅ Found Privy scripts in DOM:', scripts.length);
          clearInterval(checkPrivyScripts);
        }
      }, 1000);
      
      setTimeout(() => clearInterval(checkPrivyScripts), 10000);
    }
  }, []);

  const coreApp = (
    <AuthProvider>
      <Layout>
        <Component {...pageProps} />
      </Layout>
      <Toaster position="top-right" />
    </AuthProvider>
  );

  return (
    <>
      <Head>
        <title>TrustBridge - Professional Career & Investment Platform</title>
        <meta name="description" content="AI-Powered CV Builder, Global Job Matching & Diaspora Investment Platform" />
        <link rel="manifest" href="/manifest.json" />
        
        {/* LinkedIn-style Theme Colors */}
        <meta name="theme-color" content="#0A66C2" />
        <meta name="msapplication-TileColor" content="#0A66C2" />
        <meta name="msapplication-navbutton-color" content="#0A66C2" />
        
        {/* PWA Meta Tags */}
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="TrustBridge" />
        
        {/* iOS Safari */}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-touch-fullscreen" content="yes" />
        
        {/* Viewport */}
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
        
        {/* Open Graph / Social Media */}
        <meta property="og:type" content="website" />
        <meta property="og:title" content="TrustBridge - Professional Career & Investment Platform" />
        <meta property="og:description" content="AI-Powered CV Builder, Global Job Matching & Diaspora Investment Platform" />
        <meta property="og:site_name" content="TrustBridge" />
        
        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="TrustBridge" />
        <meta name="twitter:description" content="AI-Powered CV Builder, Global Job Matching & Diaspora Investment Platform" />
        
        {/* Favicon */}
        <link rel="icon" type="image/png" href="/trust.png" />
        <link rel="apple-touch-icon" href="/trust.png" />
      </Head>
      <PrivyWrapper>
        <PrivyAuthProvider>
          {coreApp}
        </PrivyAuthProvider>
      </PrivyWrapper>
    </>
  );
}

export default MyApp;

