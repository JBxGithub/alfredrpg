import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Link2,
  Shield,
  Percent,
  TrendingUp,
  Menu,
  X,
  ChevronDown,
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/chains', label: 'Chains', icon: Link2 },
  { path: '/protocols', label: 'Protocols', icon: Shield },
  { path: '/yields', label: 'Yields', icon: Percent },
  { path: '/tvl', label: 'TVL History', icon: TrendingUp },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="min-h-screen bg-dark-900 text-white">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-dark-800/95 backdrop-blur-sm border-b border-dark-600">
        <div className="px-4 lg:px-6">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 text-gray-400 hover:text-white transition-colors"
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
              <Link to="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-accent-gold to-amber-600 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-dark-900" />
                </div>
                <span className="font-bold text-lg hidden sm:block">DeFi Intel</span>
              </Link>
            </div>
            <div className="hidden lg:flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-dark-700 text-accent-gold'
                        : 'text-gray-400 hover:text-white hover:bg-dark-700/50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-dark-700 rounded-full">
                <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse" />
                <span className="text-xs text-gray-400">Live</span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-dark-800 border-r border-dark-600 transform transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full pt-20 pb-4">
          <nav className="flex-1 px-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-dark-700 text-accent-gold'
                      : 'text-gray-400 hover:text-white hover:bg-dark-700/50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="px-4 py-3 border-t border-dark-600">
            <div className="text-xs text-gray-500">
              Data from DeFiLlama
            </div>
          </div>
        </div>
      </div>

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <main className="pt-16 lg:pl-64">
        <div className="p-4 lg:p-6">{children}</div>
      </main>
    </div>
  );
}
