import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import axios from 'axios';
import '@/App.css';

// Auth Context & Components
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login';
import ProtectedRoute from './components/ProtectedRoute';
import Reports from './components/Reports';

// Shadcn UI Components
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { Toaster } from '@/components/ui/sonner';

// Icons from Lucide React
import { 
  Upload, 
  FileText, 
  BarChart3, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Settings,
  Home,
  Database,
  TrendingUp,
  Shield,
  FileCheck,
  AlertCircle,
  LogOut,
  User
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Dashboard Component
const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardData(response.data);
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
        <div className="text-center space-y-4">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadgeVariant = (score) => {
    if (score >= 80) return 'default';
    if (score >= 60) return 'secondary';
    return 'destructive';
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">
          QSP Compliance Dashboard
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Monitor your Quality System Procedures compliance with ISO 13485:2024 standards
        </p>
      </div>

      {/* Status Alert */}
      {!dashboardData?.iso_summary_loaded && (
        <Alert data-testid="iso-summary-alert">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Upload an ISO 13485:2024 Summary of Changes document to enable compliance analysis.
          </AlertDescription>
        </Alert>
      )}

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card data-testid="compliance-score-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Score</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getScoreColor(dashboardData?.compliance_score || 0)}`}>
              {dashboardData?.compliance_score || 0}%
            </div>
            <div className="mt-2">
              <Progress value={dashboardData?.compliance_score || 0} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card data-testid="documents-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">QSP Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData?.total_documents || 0}</div>
            <p className="text-xs text-muted-foreground">
              Documents uploaded
            </p>
          </CardContent>
        </Card>

        <Card data-testid="gaps-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Gaps</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {dashboardData?.gaps_count || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Issues identified
            </p>
          </CardContent>
        </Card>

        <Card data-testid="mappings-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Clause Mappings</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData?.total_mappings || 0}</div>
            <p className="text-xs text-muted-foreground">
              AI-generated mappings
            </p>
          </CardContent>
        </Card>
      </div>

      {/* ISO Summary Status */}
      {dashboardData?.iso_summary_loaded && (
        <Card data-testid="iso-status-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              ISO 13485:2024 Analysis Ready
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {dashboardData.new_clauses_count}
                </div>
                <p className="text-sm text-muted-foreground">New Clauses</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {dashboardData.modified_clauses_count}
                </div>
                <p className="text-sm text-muted-foreground">Modified Clauses</p>
              </div>
              <div className="text-center">
                <div className="text-sm text-muted-foreground">
                  Last Analysis: {dashboardData.last_analysis_date ? 
                    new Date(dashboardData.last_analysis_date).toLocaleDateString() : 'Never'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Document Upload Component
const DocumentUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/documents`);
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
      toast.error('Failed to load documents');
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (event, type) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setUploading(true);
    const endpoint = type === 'qsp' ? '/documents/upload' : '/iso-summary/upload';
    
    let successCount = 0;
    let failCount = 0;

    // Upload files sequentially to avoid overwhelming the server
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await axios.post(`${API}${endpoint}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        successCount++;
        
        // Show progress for multiple files
        if (files.length > 1) {
          toast.success(`Uploaded ${file.name} (${i + 1}/${files.length})`);
        } else {
          toast.success(response.data.message);
        }
      } catch (error) {
        console.error(`Upload error for ${file.name}:`, error);
        failCount++;
        toast.error(`Failed to upload ${file.name}: ${error.response?.data?.detail || 'Upload failed'}`);
      }
    }

    // Show final summary for batch uploads
    if (files.length > 1) {
      if (successCount > 0 && failCount === 0) {
        toast.success(`✅ All ${successCount} files uploaded successfully!`);
      } else if (successCount > 0 && failCount > 0) {
        toast.info(`Uploaded ${successCount} files, ${failCount} failed`);
      }
    }

    setUploading(false);
    event.target.value = '';
    
    // Refresh document list after uploads
    if (type === 'qsp' && successCount > 0) {
      fetchDocuments();
    }
  };

  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">Document Management</h1>
        <p className="text-xl text-muted-foreground">
          Upload QSP documents and ISO summary for compliance analysis
        </p>
      </div>

      {/* Upload Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* QSP Document Upload */}
        <Card data-testid="qsp-upload-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              QSP Documents
            </CardTitle>
            <CardDescription>
              Upload Quality System Procedure documents (.docx, .txt)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <input
                  id="qsp-file"
                  type="file"
                  accept=".docx,.txt"
                  multiple
                  className="hidden"
                  onChange={(e) => handleFileUpload(e, 'qsp')}
                />
                <label 
                  htmlFor="qsp-file" 
                  className={`inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                    uploading 
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                      : 'bg-primary text-primary-foreground hover:bg-primary/90 cursor-pointer'
                  } h-10 px-4 py-2`}
                  data-testid="qsp-upload-btn"
                >
                  {uploading ? 'Uploading...' : 'Select QSP Files'}
                </label>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                Supports .docx and .txt files • Select multiple files at once
              </p>
            </div>
          </CardContent>
        </Card>

        {/* ISO Summary Upload */}
        <Card data-testid="iso-upload-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              ISO 13485:2024 Summary
            </CardTitle>
            <CardDescription>
              Upload the Summary of Changes document
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <input
                  id="iso-file"
                  type="file"
                  accept=".docx,.txt,.pdf"
                  className="hidden"
                  onChange={(e) => handleFileUpload(e, 'iso')}
                />
                <label 
                  htmlFor="iso-file" 
                  className={`inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                    uploading 
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80 cursor-pointer'
                  } h-10 px-4 py-2`}
                  data-testid="iso-upload-btn"
                >
                  {uploading ? 'Uploading...' : 'Select ISO Summary'}
                </label>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                ISO 13485:2024 Summary of Changes
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Documents List */}
      <Card>
        <CardHeader>
          <CardTitle>Uploaded Documents</CardTitle>
          <CardDescription>
            {documents.length} QSP documents uploaded
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingDocs ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            </div>
          ) : documents.length > 0 ? (
            <div className="space-y-3">
              {documents.map((doc, index) => (
                <div key={doc.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileCheck className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="font-medium">{doc.filename}</p>
                      <p className="text-sm text-muted-foreground">
                        {doc.sections ? Object.keys(doc.sections).length : 0} sections • 
                        Uploaded {new Date(doc.upload_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <Badge variant="secondary">
                    {doc.processed ? 'Processed' : 'Processing'}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No documents uploaded yet. Upload QSP documents to get started.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Analysis Component
const Analysis = () => {
  const [running, setRunning] = useState(false);
  const [step, setStep] = useState('');

  const runMapping = async () => {
    setRunning(true);
    setStep('Analyzing clause mappings with AI...');
    
    try {
      const response = await axios.post(`${API}/analysis/run-mapping`);
      toast.success(response.data.message);
      setStep('Mapping completed successfully!');
    } catch (error) {
      console.error('Mapping error:', error);
      toast.error(error.response?.data?.detail || 'Mapping failed');
      setStep('Mapping failed');
    } finally {
      setTimeout(() => {
        setRunning(false);
        setStep('');
      }, 2000);
    }
  };

  const runCompliance = async () => {
    setRunning(true);
    setStep('Running compliance gap analysis...');
    
    try {
      const response = await axios.post(`${API}/analysis/run-compliance`);
      toast.success(response.data.message);
      setStep('Analysis completed successfully!');
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error(error.response?.data?.detail || 'Analysis failed');
      setStep('Analysis failed');
    } finally {
      setTimeout(() => {
        setRunning(false);
        setStep('');
      }, 2000);
    }
  };

  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">Compliance Analysis</h1>
        <p className="text-xl text-muted-foreground">
          Run AI-powered analysis to map clauses and identify compliance gaps
        </p>
      </div>

      {/* Analysis Steps */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card data-testid="mapping-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Step 1: Clause Mapping
            </CardTitle>
            <CardDescription>
              AI analyzes QSP documents and maps them to ISO 13485 clauses
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• Parses document sections</li>
              <li>• Maps content to ISO clauses using AI</li>
              <li>• Generates confidence scores</li>
              <li>• Extracts evidence quotes</li>
            </ul>
            <Button 
              onClick={runMapping} 
              disabled={running} 
              className="w-full"
              data-testid="run-mapping-btn"
            >
              {running && step.includes('mapping') ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                  Analyzing...
                </>
              ) : (
                'Run Clause Mapping'
              )}
            </Button>
          </CardContent>
        </Card>

        <Card data-testid="analysis-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Step 2: Gap Analysis
            </CardTitle>
            <CardDescription>
              Compare mappings against ISO changes to identify gaps
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• Compares against ISO 13485:2024 changes</li>
              <li>• Identifies missing coverage</li>
              <li>• Calculates compliance scores</li>
              <li>• Generates recommendations</li>
            </ul>
            <Button 
              onClick={runCompliance} 
              disabled={running} 
              className="w-full"
              data-testid="run-analysis-btn"
            >
              {running && step.includes('compliance') ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                  Analyzing...
                </>
              ) : (
                'Run Gap Analysis'
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Progress Indicator */}
      {running && (
        <Card data-testid="progress-card">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <div className="animate-pulse">
                <TrendingUp className="h-12 w-12 mx-auto text-blue-500" />
              </div>
              <div>
                <h3 className="text-lg font-medium">Processing Analysis</h3>
                <p className="text-muted-foreground">{step}</p>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Gaps Component
const Gaps = () => {
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchGaps = async () => {
    try {
      const response = await axios.get(`${API}/gaps`);
      setGaps(response.data.gaps || []);
    } catch (error) {
      console.error('Error fetching gaps:', error);
      toast.error('Failed to load compliance gaps');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGaps();
  }, []);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'secondary';
    }
  };

  const getGapTypeIcon = (type) => {
    switch (type) {
      case 'missing': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'partial': return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'outdated': return <Clock className="h-4 w-4 text-orange-500" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
          <p className="text-muted-foreground">Loading compliance gaps...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">Compliance Gaps</h1>
        <p className="text-xl text-muted-foreground">
          Detailed analysis of compliance gaps and recommendations
        </p>
      </div>

      {gaps.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
            <h3 className="text-lg font-medium mb-2">No Compliance Gaps Found</h3>
            <p className="text-muted-foreground">
              Great! Your QSP documents appear to be compliant with ISO 13485:2024 changes.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {/* Summary */}
          <Card data-testid="gaps-summary">
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-red-600">
                    {gaps.filter(g => g.severity === 'high').length}
                  </div>
                  <p className="text-sm text-muted-foreground">High Priority</p>
                </div>
                <div>
                  <div className="text-2xl font-bold text-yellow-600">
                    {gaps.filter(g => g.severity === 'medium').length}
                  </div>
                  <p className="text-sm text-muted-foreground">Medium Priority</p>
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {gaps.filter(g => g.severity === 'low').length}
                  </div>
                  <p className="text-sm text-muted-foreground">Low Priority</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Gaps List */}
          {gaps.map((gap, index) => (
            <Card key={gap.id || index} data-testid={`gap-${index}`}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    {getGapTypeIcon(gap.gap_type)}
                    <div>
                      <CardTitle className="text-lg">{gap.iso_clause}</CardTitle>
                      <CardDescription>{gap.qsp_filename}</CardDescription>
                    </div>
                  </div>
                  <Badge variant={getSeverityColor(gap.severity)}>
                    {gap.severity?.toUpperCase() || 'UNKNOWN'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Description</h4>
                  <p className="text-muted-foreground">{gap.description}</p>
                </div>
                
                {gap.recommendations && gap.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Recommendations</h4>
                    <ul className="space-y-1">
                      {gap.recommendations.map((rec, idx) => (
                        <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                          <span className="text-blue-500 mt-1">•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Navigation Component
const Navigation = () => {
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();
  
  // Don't show navigation on login page
  if (location.pathname === '/login') {
    return null;
  }

  if (!isAuthenticated) {
    return null;
  }
  
  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/upload', label: 'Documents', icon: Upload },
    { path: '/analysis', label: 'Analysis', icon: BarChart3 },
    { path: '/gaps', label: 'Gaps', icon: AlertTriangle },
    { path: '/reports', label: 'Reports', icon: FileText }
  ];

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <div className="flex items-center gap-2">
              <Shield className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">QSP Compliance</span>
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
                    data-testid={`nav-${item.label.toLowerCase()}`}
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
          <Navigation />
          <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/upload" 
                element={
                  <ProtectedRoute>
                    <DocumentUpload />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/analysis" 
                element={
                  <ProtectedRoute>
                    <Analysis />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/gaps" 
                element={
                  <ProtectedRoute>
                    <Gaps />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/reports" 
                element={
                  <ProtectedRoute>
                    <Reports />
                  </ProtectedRoute>
                } 
              />
            </Routes>
          </main>
          <Toaster />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;