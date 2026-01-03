/**
 * Startup Dashboard
 * Shows verification status, funding progress, and startup management
 */
import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { useAuth } from "../contexts/AuthContext";
import { 
  Shield, 
  TrendingUp, 
  DollarSign, 
  Users, 
  CheckCircle, 
  Clock, 
  XCircle,
  FileText,
  Edit
} from "lucide-react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";

export default function StartupDashboard() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();
  const solanaAddress = user?.wallet_address || null;
  const [startup, setStartup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fundingProgress, setFundingProgress] = useState(0);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    fetchStartupData();
  }, [isAuthenticated, router]);

  const fetchStartupData = async () => {
    try {
      setLoading(true);
      // Fetch startup by founder/user ID
      const response = await fetch(`http://localhost:8001/api/startups/by-founder/${user?.id}`);
      if (response.ok) {
        const data = await response.json();
        setStartup(data);
        
        // Calculate funding progress
        if (data.funding_goal && data.total_investments) {
          const progress = (data.total_investments / data.funding_goal) * 100;
          setFundingProgress(Math.min(100, progress));
        }
      } else if (response.status === 404) {
        // No startup found - redirect to onboarding
        router.push("/startup-onboarding");
      }
    } catch (error) {
      toast.error("Failed to load startup data");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getVerificationStatus = () => {
    if (!startup) return { status: "pending", label: "Pending", icon: Clock, color: "yellow" };
    
    if (startup.transaction_signature) {
      return { status: "verified", label: "Verified", icon: CheckCircle, color: "green" };
    }
    return { status: "pending", label: "Pending Verification", icon: Clock, color: "yellow" };
  };

  if (!isAuthenticated || loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!startup) {
    return null; // Will redirect to onboarding
  }

  const verification = getVerificationStatus();
  const StatusIcon = verification.icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-8 mb-8 shadow-xl"
          >
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-4xl font-bold text-white mb-2">{startup.name}</h1>
                <p className="text-white/80">{startup.sector} • {startup.country}</p>
              </div>
              <button
                onClick={() => router.push("/startup-onboarding")}
                className="px-4 py-2 backdrop-blur-xl bg-white/10 border border-white/20 rounded-lg text-white hover:bg-white/20 transition-all flex items-center gap-2"
              >
                <Edit className="w-4 h-4" />
                Edit Profile
              </button>
            </div>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Verification Status */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-xl"
              >
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-white">Verification Status</h2>
                  <StatusIcon className={`w-6 h-6 text-${verification.color}-400`} />
                </div>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-white/80">On-Chain Verification</span>
                    <span className={`text-${verification.color}-400 font-semibold`}>
                      {verification.label}
                    </span>
                  </div>
                  {startup.transaction_signature && (
                    <div className="mt-4 p-4 backdrop-blur-xl bg-white/5 border border-white/10 rounded-lg">
                      <p className="text-white/60 text-sm mb-1">Transaction Signature</p>
                      <p className="text-white font-mono text-xs break-all">
                        {startup.transaction_signature}
                      </p>
                    </div>
                  )}
                  {verification.status === "pending" && (
                    <p className="text-white/60 text-sm mt-4">
                      Your startup is being verified on the blockchain. This usually takes a few minutes.
                    </p>
                  )}
                </div>
              </motion.div>

              {/* Funding Progress */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-xl"
              >
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-white">Funding Progress</h2>
                  <DollarSign className="w-6 h-6 text-green-400" />
                </div>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-white/80 mb-2">
                      <span>Raised</span>
                      <span className="font-semibold text-white">
                        ${(startup.total_investments || 0).toLocaleString()} USDC
                      </span>
                    </div>
                    <div className="w-full h-4 backdrop-blur-xl bg-white/10 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${fundingProgress}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className="h-full bg-gradient-to-r from-green-400 to-emerald-500"
                      />
                    </div>
                    <div className="flex justify-between text-white/60 text-sm mt-2">
                      <span>{fundingProgress.toFixed(1)}% Complete</span>
                      <span>Goal: ${(startup.funding_goal || 0).toLocaleString()} USDC</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 mt-6">
                    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-lg p-4">
                      <p className="text-white/60 text-sm">Total Investments</p>
                      <p className="text-2xl font-bold text-white mt-1">
                        {startup.investment_count || 0}
                      </p>
                    </div>
                    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-lg p-4">
                      <p className="text-white/60 text-sm">Investors</p>
                      <p className="text-2xl font-bold text-white mt-1">
                        {startup.investor_count || 0}
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Startup Details */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-xl"
              >
                <h2 className="text-2xl font-bold text-white mb-4">About</h2>
                <div className="space-y-4 text-white/80">
                  <div>
                    <h3 className="text-white font-semibold mb-2">Description</h3>
                    <p>{startup.description}</p>
                  </div>
                  {startup.mission && (
                    <div>
                      <h3 className="text-white font-semibold mb-2">Mission</h3>
                      <p>{startup.mission}</p>
                    </div>
                  )}
                  {startup.vision && (
                    <div>
                      <h3 className="text-white font-semibold mb-2">Vision</h3>
                      <p>{startup.vision}</p>
                    </div>
                  )}
                </div>
              </motion.div>
            </div>

            {/* Sidebar */}
            <div className="space-y-8">
              {/* Quick Stats */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-xl"
              >
                <h2 className="text-xl font-bold text-white mb-4">Quick Stats</h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-white/80">
                      <Users className="w-5 h-5" />
                      <span>Team Size</span>
                    </div>
                    <span className="text-white font-semibold">{startup.team_size || 0}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-white/80">
                      <TrendingUp className="w-5 h-5" />
                      <span>Credibility Score</span>
                    </div>
                    <span className="text-white font-semibold">
                      {startup.credibility_score?.toFixed(1) || "N/A"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-white/80">
                      <Shield className="w-5 h-5" />
                      <span>Verified Employees</span>
                    </div>
                    <span className="text-white font-semibold">
                      {startup.employees_verified || 0}
                    </span>
                  </div>
                </div>
              </motion.div>

              {/* Contact Info */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-xl"
              >
                <h2 className="text-xl font-bold text-white mb-4">Contact</h2>
                <div className="space-y-3 text-white/80">
                  {startup.contact_email && (
                    <div>
                      <p className="text-sm text-white/60">Email</p>
                      <p className="text-white">{startup.contact_email}</p>
                    </div>
                  )}
                  {startup.phone && (
                    <div>
                      <p className="text-sm text-white/60">Phone</p>
                      <p className="text-white">{startup.phone}</p>
                    </div>
                  )}
                  {startup.website && (
                    <div>
                      <p className="text-sm text-white/60">Website</p>
                      <a
                        href={startup.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline"
                      >
                        {startup.website}
                      </a>
                    </div>
                  )}
                  {startup.pitch_deck_url && (
                    <div>
                      <p className="text-sm text-white/60">Pitch Deck</p>
                      <a
                        href={startup.pitch_deck_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline flex items-center gap-2"
                      >
                        <FileText className="w-4 h-4" />
                        View Pitch Deck
                      </a>
                    </div>
                  )}
                </div>
              </motion.div>

              {/* Wallet Info */}
              {solanaAddress && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-xl"
                >
                  <h2 className="text-xl font-bold text-white mb-4">Wallet</h2>
                  <p className="text-white/60 text-sm mb-2">Solana Address</p>
                  <p className="text-white font-mono text-xs break-all">{solanaAddress}</p>
                </motion.div>
              )}
            </div>
          </div>
        </div>
      </div>
  );
}

