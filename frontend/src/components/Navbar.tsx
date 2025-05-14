import React from "react";
import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { usePythonChat } from '@/contexts/PythonChatContext';
import { pythonBackendService } from "@/services/pythonBackendService";

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const { userProfile } = usePythonChat();

  const redirectLogin = () => {
    navigate("/login");
  };

  const redirectRegister = () => {
    navigate("/register");
  };

  const logout = () => {
    pythonBackendService.auth.logout();
    navigate("/login");
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="lloyds-container flex justify-between items-center py-4">
        <div className="flex items-center">
          <Link to="/" className="flex items-center">
            <div className="w-10 h-10 bg-lloyds-darkGreen rounded-full flex items-center justify-center mr-2">
              <span className="text-white font-bold text-lg">L</span>
            </div>
            <span className="text-lloyds-darkGreen font-bold text-xl">
              RetireIQ
            </span>
          </Link>

          <div className="hidden md:flex ml-10 space-x-6">
            <Link
              to="/"
              className="text-lloyds-darkGray hover:text-lloyds-green font-medium"
            >
              Home
            </Link>
            <Link
              to="/chat"
              className="text-lloyds-darkGray hover:text-lloyds-green font-medium"
            >
              Chat Assistant
            </Link>
            <Link
              to="/settings"
              className="text-lloyds-darkGray hover:text-lloyds-green font-medium"
            >
              Settings
            </Link>
          </div>
        </div>
        {!pythonBackendService.auth.isAuthenticated() && (
          <div className="flex items-center space-x-4">
            <Button
              onClick={redirectLogin}
              variant="outline"
              className="lloyds-button-secondary"
            >
              Log in
            </Button>
            <Button
              onClick={redirectRegister}
              className="lloyds-button-primary"
            >
              Sign up
            </Button>
          </div>
        )}
        {pythonBackendService.auth.isAuthenticated() && userProfile && (
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              className="lloyds-button-secondary"
            >
            {userProfile.name}
            </Button>
            <Button
              onClick={logout}
              className="lloyds-button-primary"
            >
              Logout
            </Button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
