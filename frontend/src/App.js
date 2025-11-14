import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import '@/App.css';

// Icons
import { 
  Home, Upload, BarChart3, AlertTriangle, FileText, Settings, 
  Shield, Database, TrendingUp, User, LogOut, AlertCircle, GitCompare
} from 'lucide-react';

// UI Components
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Toaster } from '@/components/ui/sonner';

// Auth Context & Components
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login';
import ProtectedRoute from './components/ProtectedRoute';
import MainWorkflow from './components/MainWorkflow';
import LandingPage from './pages/LandingPage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Dashboard Component
const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/dashboard/metrics`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.data && response.data.success) {
        setDashboardData(response.data);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin h-12 w-12 border-4 border-blue-600 border-t-transparent rounded-full"></div>
        <p className="ml-4 text-lg text-gray-600">Loading compliance dashboard...</p>
      </div>
    );
  }

  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="space-y-8">
      <style>{`
        .metric-card { background: white; border-radius: 16px; border: 1px solid #e2e8f0; padding: 1.5rem; transition: all 0.3s ease; position: relative; overflow: hidden; }
        .metric-card::before { content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: linear-gradient(135deg, #0066ff 0%, #00d4aa 100%); transform: scaleX(0); transition: transform 0.3s ease; }
        .metric-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08); }
        .metric-card:hover::before { transform: scaleX(1); }
        .metric-icon { width: 48px; height: 48px; background: linear-gradient(135deg, #0066ff 0%, #00d4aa 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; margin-bottom: 1rem; }
        .metric-value { font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; }
        .metric-label { font-size: 0.875rem; color: #64748b; font-weight: 500; }
        .dashboard-title { font-size: 3rem; font-weight: 800; background: linear-gradient(135deg, #0a0e27 0%, #0066ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 1rem; }
        .dashboard-subtitle { font-size: 1.25rem; color: #64748b; }
        .status-card { background: linear-gradient(135deg, #f0f4ff 0%, #e8f5ff 100%); border-radius: 16px; padding: 2rem; margin-top: 2rem; }
        .status-indicator { width: 16px; height: 16px; background: #10b981; border-radius: 50%; animation: pulse-status 2s infinite; }
        @keyframes pulse-status { 0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); } 70% { box-shadow: 0 0 0 12px rgba(16, 185, 129, 0); } 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }
        .compliance-progress { height: 8px; background: #e2e8f0; border-radius: 10px; overflow: hidden; margin-top: 1rem; }
        .compliance-progress-bar { height: 100%; background: linear-gradient(135deg, #0066ff 0%, #00d4aa 100%); border-radius: 10px; transition: width 0.6s ease; }
      `}</style>

      {/* Header */}
      <div className="text-center space-y-4 py-8">
        <h1 className="dashboard-title">
          Certaro Compliance Dashboard
        </h1>
        <p className="dashboard-subtitle max-w-2xl mx-auto">
          Monitor your Quality System Procedures compliance with ISO 13485:2024 standards
        </p>
      </div>

      {/* Status Alert */}
      {!dashboardData?.iso_summary_loaded && (
        <div className="bg-gradient-to-r from-orange-50 to-yellow-50 border-l-4 border-orange-500 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-orange-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-gray-900">Upload Regulatory Document</p>
            <p className="text-sm text-gray-600">Go to Workflow tab to upload regulatory standards and analyze compliance.</p>
          </div>
        </div>
      )}

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="metric-card">
          <div className="metric-icon">
            <Shield className="h-6 w-6" />
          </div>
          <div style={{ color: getScoreColor(dashboardData?.compliance_score || 0) }} className="metric-value">
            {dashboardData?.compliance_score || 0}%
          </div>
          <div className="metric-label">Compliance Score</div>
          <div className="compliance-progress">
            <div 
              className="compliance-progress-bar" 
              style={{ width: `${dashboardData?.compliance_score || 0}%` }}
            ></div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">
            <FileText className="h-6 w-6" />
          </div>
          <div className="metric-value" style={{ color: '#0066ff' }}>
            {dashboardData?.total_documents || 0}
          </div>
          <div className="metric-label">QSP Documents Uploaded</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">
            <AlertTriangle className="h-6 w-6" />
          </div>
          <div className="metric-value" style={{ color: '#ef4444' }}>
            {dashboardData?.gaps_count || 0}
          </div>
          <div className="metric-label">Compliance Gaps Identified</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">
            <Database className="h-6 w-6" />
          </div>
          <div className="metric-value" style={{ color: '#00d4aa' }}>
            {dashboardData?.total_mappings || 0}
          </div>
          <div className="metric-label">AI-Generated Mappings</div>
        </div>
      </div>

      {/* Regulatory Analysis Status */}
      {dashboardData?.iso_summary_loaded && (
        <div className="status-card">
          <div className="flex items-center gap-3 mb-6">
            <div className="status-indicator"></div>
            <h3 className="text-xl font-bold" style={{ color: '#0a0e27' }}>
              Regulatory Standards Monitoring Active
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold" style={{ color: '#0066ff' }}>
                {dashboardData.new_clauses_count || 0}
              </div>
              <p className="text-sm text-gray-600 mt-2">New Requirements</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold" style={{ color: '#f59e0b' }}>
                {dashboardData.modified_clauses_count || 0}
              </div>
              <p className="text-sm text-gray-600 mt-2">Modified Clauses</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold" style={{ color: '#00d4aa' }}>
                {dashboardData.total_mappings || 0}
              </div>
              <p className="text-sm text-gray-600 mt-2">Active Mappings</p>
            </div>
          </div>
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-500">
              Last Analysis: {dashboardData.last_analysis_date ? 
                new Date(dashboardData.last_analysis_date).toLocaleDateString() : 'Never'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

// Navigation Component
const Navigation = () => {
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();
  
  // Don't show navigation on landing or login page
  if (location.pathname === '/login' || location.pathname === '/') {
    return null;
  }

  if (!isAuthenticated) {
    return null;
  }
  
  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/workflow', label: 'Workflow', icon: GitCompare }
  ];

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <div className="flex items-center gap-2">
              <div style={{ 
                width: '35px', 
                height: '35px', 
                background: 'linear-gradient(135deg, #0066ff 0%, #00d4aa 100%)',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '1.2rem',
                fontWeight: '800'
              }}>
                ✓
              </div>
              <span className="text-xl font-bold" style={{
                background: 'linear-gradient(135deg, #0066ff 0%, #00d4aa 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>Certaro</span>
            </div>
            
            <div className="hidden md:flex space-x-4">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive 
                        ? 'bg-blue-100 text-blue-700' 
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
          
          {/* User Menu */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <User className="h-4 w-4" />
              <span>{user?.email}</span>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={logout}
              className="flex items-center gap-2"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Main App Component
function App() {
  return (
    <div className="App min-h-screen bg-gray-50">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            
            {/* Protected Routes with Navigation */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Navigation />
                  <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                    <Dashboard />
                  </main>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/workflow" 
              element={
                <ProtectedRoute>
                  <Navigation />
                  <MainWorkflow />
                </ProtectedRoute>
              } 
            />
          </Routes>
          <Toaster />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
