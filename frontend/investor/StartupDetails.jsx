/**
 * Startup Details Component
 * Shows detailed startup information with verification proof
 */
import { useState, useEffect } from "react";
import { Shield, TrendingUp, Users, Globe, Mail, Phone } from "lucide-react";
import { useRouter } from "next/router";
import toast from "react-hot-toast";

export default function StartupDetails({ startupId }) {
  const router = useRouter();
  const [startup, setStartup] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (startupId) {
      console.log("Fetching startup with ID:", startupId);
      fetchStartupDetails();
    }
  }, [startupId]);

  const fetchStartupDetails = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8001/api/startups/${startupId}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to fetch startup: ${response.status}`);
      }
      
      const data = await response.json();
      setStartup(data);
    } catch (error) {
      console.error("Error fetching startup:", error);
      toast.error(error.message || "Failed to fetch startup details");
      setStartup(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <p>Loading startup details...</p>;
  }

  if (!startup) {
    return (
      <div className="card p-6 text-center">
        <p className="text-red-600 font-semibold mb-2">Startup not found</p>
        <p className="text-gray-600 text-sm mb-4">
          Startup ID: {startupId}
        </p>
        <p className="text-gray-500 text-xs">
          Please check that the startup ID is correct and try again.
        </p>
      </div>
    );
  }

  return (
    <div className="startup-details">
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">{startup.name}</h1>
            <p className="text-gray-600">{startup.sector}</p>
          </div>
          <div className="flex items-center gap-2 text-green-600">
            <Shield className="w-5 h-5" />
            <span className="font-semibold">Verified</span>
          </div>
        </div>

        {/* Verification Proof */}
        {startup.transaction_signature && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-green-800">
              <strong>Blockchain Verified:</strong>{" "}
              <a
                href={`https://explorer.solana.com/tx/${startup.transaction_signature}?cluster=devnet`}
                target="_blank"
                rel="noopener noreferrer"
                className="underline"
              >
                View on Solana Explorer
              </a>
            </p>
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <TrendingUp className="w-6 h-6 mx-auto mb-2 text-blue-600" />
            <p className="text-2xl font-bold">{startup.credibility_score}%</p>
            <p className="text-sm text-gray-600">Credibility Score</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <Users className="w-6 h-6 mx-auto mb-2 text-green-600" />
            <p className="text-2xl font-bold">{startup.employees_verified}</p>
            <p className="text-sm text-gray-600">Verified Employees</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <span className="text-2xl font-bold">${startup.funding_goal?.toLocaleString()}</span>
            <p className="text-sm text-gray-600">Funding Goal</p>
          </div>
        </div>

        {/* Description */}
        <div className="mb-6">
          <h3 className="font-semibold mb-2">About</h3>
          <p className="text-gray-700">{startup.description}</p>
        </div>

        {/* Contact Information */}
        <div className="grid grid-cols-2 gap-4">
          {startup.website && (
            <div className="flex items-center gap-2">
              <Globe className="w-5 h-5 text-gray-400" />
              <a href={startup.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                {startup.website}
              </a>
            </div>
          )}
          {startup.contact_email && (
            <div className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-gray-400" />
              <a href={`mailto:${startup.contact_email}`} className="text-blue-600 hover:underline">
                {startup.contact_email}
              </a>
            </div>
          )}
          {startup.phone && (
            <div className="flex items-center gap-2">
              <Phone className="w-5 h-5 text-gray-400" />
              <span>{startup.phone}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

