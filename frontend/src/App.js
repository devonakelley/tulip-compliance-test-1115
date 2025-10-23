import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import '@/App.css';

// Auth Context & Components
import { AuthProvider } from './context/AuthContext';
import Login from './components/Login';
import ProtectedRoute from './components/ProtectedRoute';
import MainWorkflow from './components/MainWorkflow';

// Toaster for notifications
import { Toaster } from '@/components/ui/sonner';

function App() {
  return (
    <div className="App min-h-screen bg-gray-50">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public Route - Login */}
            <Route path="/login" element={<Login />} />
            
            {/* Protected Route - Main Workflow (3 Tabs) */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <MainWorkflow />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/workflow" 
              element={
                <ProtectedRoute>
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
