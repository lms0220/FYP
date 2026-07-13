import { Link, useNavigate, useLocation } from "react-router-dom";
import { Shield, Home, Send, History, LogOut, Menu, X } from "lucide-react";
import { useState } from "react";
import { logout } from "../api";

export default function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error(error);
    }

    sessionStorage.clear();

    navigate("/", { replace: true });
  };

  const navItems = [
    { path: "/app", icon: Home, label: "Dashboard" },
    { path: "/app/submit", icon: Send, label: "Submit" },
    { path: "/app/history", icon: History, label: "History" },
  ];

  const isActive = (path: string) => {
    if (path === "/app") {
      return location.pathname === "/app";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <div className="flex items-center">
              <div className="bg-indigo-600 p-2 rounded-lg">
                <Shield className="size-6 text-white" />
              </div>
              <span className="ml-3 text-xl font-bold text-gray-900">
                Scam Shield AI
              </span>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex ml-10 space-x-4">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition ${
                    isActive(item.path)
                      ? "bg-indigo-100 text-indigo-700"
                      : "text-gray-700 hover:bg-gray-100"
                  }`}
                >
                  <item.icon className="size-4 mr-2" />
                  {item.label}
                </Link>
              ))}
            </div>
          </div>

          {/* Desktop Logout */}
          <div className="hidden md:block">
            <button
              onClick={handleLogout}
              className="flex items-center px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-red-50 hover:text-red-600 transition"
            >
              <LogOut className="size-4 mr-2" />
              Logout
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-md text-gray-700 hover:bg-gray-100"
            >
              {isMobileMenuOpen ? (
                <X className="size-6" />
              ) : (
                <Menu className="size-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`flex items-center px-3 py-2 rounded-md text-base font-medium transition ${
                  isActive(item.path)
                    ? "bg-indigo-100 text-indigo-700"
                    : "text-gray-700 hover:bg-gray-100"
                }`}
              >
                <item.icon className="size-5 mr-3" />
                {item.label}
              </Link>
            ))}
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-red-50 hover:text-red-600 transition"
            >
              <LogOut className="size-5 mr-3" />
              Logout
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
