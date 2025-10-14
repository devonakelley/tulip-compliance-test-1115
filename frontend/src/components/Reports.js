import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FileText, Calendar, TrendingUp, Activity, Download, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [reportStats, setReportStats] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditStats, setAuditStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchReports();
    fetchReportStats();
    fetchAuditLogs();
    fetchAuditStats();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await axios.get(`${API}/reports`);
      setReports(response.data.reports || []);
    } catch (error) {
      console.error('Error fetching reports:', error);
      toast.error('Failed to load reports');
    }
  };

  const fetchReportStats = async () => {
    try {
      const response = await axios.get(`${API}/reports/stats`);
      setReportStats(response.data.stats);
    } catch (error) {
      console.error('Error fetching report stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const response = await axios.get(`${API}/reports/audit-logs?limit=20`);
      setAuditLogs(response.data.logs || []);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    }
  };

  const fetchAuditStats = async () => {
    try {
      const response = await axios.get(`${API}/reports/audit-stats`);
      setAuditStats(response.data.stats);
    } catch (error) {
      console.error('Error fetching audit stats:', error);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAnalysisTypeBadge = (type) => {
    const colors = {
      'clause_mapping': 'bg-blue-100 text-blue-800',
      'compliance_gap_analysis': 'bg-purple-100 text-purple-800',
      'gap_analysis': 'bg-orange-100 text-orange-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Reports & Audit Logs</h1>
        <p className="text-gray-600 mt-2">View compliance analysis history and system activity</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
            <FileText className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{reportStats?.total_reports || 0}</div>
            <p className="text-xs text-gray-500 mt-1">Compliance analyses</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Alignment Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getScoreColor(reportStats?.average_alignment_score || 0)}`}>
              {(reportStats?.average_alignment_score || 0).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-500 mt-1">Overall compliance</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Activities</CardTitle>
            <Activity className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{auditStats?.total_actions || 0}</div>
            <p className="text-xs text-gray-500 mt-1">Logged actions</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs for Reports and Audit Logs */}
      <Tabs defaultValue="reports" className="w-full">
        <TabsList>
          <TabsTrigger value="reports">Analysis Reports</TabsTrigger>
          <TabsTrigger value="audit">Audit Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="reports" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Compliance Analysis Reports</CardTitle>
              <CardDescription>
                Historical compliance analyses for your organization
              </CardDescription>
            </CardHeader>
            <CardContent>
              {reports.length === 0 ? (
                <Alert>
                  <AlertDescription>
                    No reports available yet. Run a compliance analysis to generate reports.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-4">
                  {reports.map((report, index) => (
                    <div key={index} className="border rounded-lg p-4 hover:bg-gray-50 transition">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge className={getAnalysisTypeBadge(report.analysis_type)}>
                              {report.analysis_type.replace('_', ' ').toUpperCase()}
                            </Badge>
                            <span className={`text-lg font-semibold ${getScoreColor(report.alignment_score)}`}>
                              {report.alignment_score.toFixed(1)}%
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{report.summary}</p>
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {formatDate(report.created_at)}
                            </span>
                            <span className="flex items-center gap-1">
                              <FileText className="h-3 w-3" />
                              {report.total_documents} documents
                            </span>
                            {report.gaps_found > 0 && (
                              <span className="flex items-center gap-1 text-orange-600">
                                <Activity className="h-3 w-3" />
                                {report.gaps_found} gaps
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Audit Activity Log</CardTitle>
              <CardDescription>
                All system activities and user actions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {auditLogs.length === 0 ? (
                <Alert>
                  <AlertDescription>
                    No audit logs available.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-2">
                  {auditLogs.map((log, index) => (
                    <div key={index} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded hover:bg-gray-100 transition">
                      <div className="flex items-center gap-3">
                        <Clock className="h-4 w-4 text-gray-400" />
                        <div>
                          <span className="font-medium text-sm capitalize">{log.action.replace('_', ' ')}</span>
                          <span className="text-gray-600 text-sm ml-2">→ {log.target}</span>
                        </div>
                      </div>
                      <span className="text-xs text-gray-500">
                        {formatDate(log.timestamp)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Reports;
