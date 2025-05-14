// src/components/ProtectedRoute.js
import { Navigate } from "react-router-dom";
import { pythonBackendService } from "@/services/pythonBackendService";

const ProtectedRoute = ({ children }) => {
  const isAuthenticated = pythonBackendService.auth.isAuthenticated();

  return isAuthenticated ? children : <Navigate to="/login" />;
};

export default ProtectedRoute;
