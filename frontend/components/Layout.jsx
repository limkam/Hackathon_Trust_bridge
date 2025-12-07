import Link from "next/link";
import { useRouter } from "next/router";
import { useAuth } from "../contexts/AuthContext";
import {
  LogOut,
  Building2,
  GraduationCap,
} from "lucide-react";
import Logo from "./Logo";

export default function Layout({ children }) {
  const { user, logout, isAuthenticated } = useAuth();
  const router = useRouter();

  const getNavLinks = () => {
    if (!user) return [];

    const links = [];
    
    // Job seekers and students see CV Builder
    if (user.role === 'job_seeker' || user.role === 'student' || !user.role) {
      links.push({ href: "/cv-builder", label: "CV Builder", icon: GraduationCap });
    }
    
    // Investors see Investments
    if (user.role === 'investor') {
      links.push({ href: "/investor-platform", label: "Investments", icon: Building2 });
    }
    
    // Startups see their dashboard (but NOT Investments)
    if (user.role === 'startup' || user.role === 'founder') {
      links.push({ href: "/startup-dashboard", label: "My Startup", icon: Building2 });
    }

    return links;
  };

  const navLinks = getNavLinks();

  // Don't show nav on landing page
  const isLandingPage = router.pathname === '/';

  return (
    <div className="min-h-screen">
      {isAuthenticated && !isLandingPage && (
        <nav className="glass-premium border-b border-blue-200/50 sticky top-0 z-50 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <Logo size="default" />

              <div className="flex items-center gap-4">
                {navLinks.map((link) => {
                  const Icon = link.icon;
                  const isActive = router.pathname === link.href;
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold transition-all duration-300 ${
                        isActive
                          ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/30"
                          : "text-blue-700 hover:bg-blue-50 hover:text-blue-800"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="hidden md:inline">{link.label}</span>
                    </Link>
                  );
                })}

                <div className="flex items-center gap-4 pl-4 border-l border-blue-200">
                  <span className="text-sm text-blue-700 font-medium hidden md:inline">
                    {user?.full_name || user?.email}
                  </span>
                  <button
                    onClick={logout}
                    className="flex items-center gap-2 text-blue-700 hover:text-red-600 transition-colors font-medium px-3 py-2 rounded-lg hover:bg-red-50"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="hidden md:inline">Logout</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </nav>
      )}

      <main>{children}</main>
    </div>
  );
}
