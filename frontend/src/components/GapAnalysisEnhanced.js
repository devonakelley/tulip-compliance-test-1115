import React, { useState, useRef } from 'react';
import axios from 'axios';
import { TrendingUp, Download, AlertCircle, ChevronDown, ChevronUp, Grid3x3, List, Edit2, Save, X, FileText } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const GapAnalysisEnhanced = () => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [runId, setRunId] = useState(null);
  const [exportingCSV, setExportingCSV] = useState(false);
  const [exportingPDF, setExportingPDF] = useState(false);
  const [expandedRows, setExpandedRows] = useState({});
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'grid'
  const [editingImpact, setEditingImpact] = useState(null);
  const [suggestedChanges, setSuggestedChanges] = useState({});
  const printRef = useRef();

  const handleRunAnalysis = async () => {
    try {
      setAnalyzing(true);
      toast.loading('Running gap analysis...', { id: 'analysis' });

      const diffResults = localStorage.getItem('regulatory_diff');
      if (!diffResults) {
        toast.error('No regulatory diff found. Please complete Tab 1 first.', { id: 'analysis' });
        setAnalyzing(false);
        return;
      }

      const clauseMap = localStorage.getItem('clause_map');
      if (!clauseMap) {
        toast.error('No clause map found. Please complete Tab 2 first.', { id: 'analysis' });
        setAnalyzing(false);
        return;
      }

      const deltas = JSON.parse(diffResults);

      const response = await axios.post(`${API}/api/impact/analyze`, {
        deltas: deltas.deltas || [],
        top_k: 10
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.data.success) {
        setAnalysisResults(response.data);
        setRunId(response.data.run_id);
        
        // Initialize suggested changes
        const initialSuggestions = {};
        response.data.impacts?.forEach((impact, idx) => {
          initialSuggestions[idx] = impact.suggested_change || '';
        });
        setSuggestedChanges(initialSuggestions);
        
        toast.success(
          `✅ Analysis complete: ${response.data.total_impacts_found} impacts found`,
          { id: 'analysis' }
        );
      } else if (response.data.error) {
        toast.error(response.data.error, { id: 'analysis' });
      }
    } catch (error) {
      console.error('Error running analysis:', error);
      toast.error(error.response?.data?.detail || 'Failed to run analysis', { id: 'analysis' });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleExportCSV = async () => {
    if (!runId) {
      toast.error('No analysis results to export');
      return;
    }

    try {
      setExportingCSV(true);
      toast.loading('Generating CSV...', { id: 'csv-export' });
      
      const response = await axios.get(
        `${API}/api/impact/report/${runId}?format=csv`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().toISOString().slice(0, 10);
      link.setAttribute('download', `gap_analysis_${timestamp}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('CSV exported successfully', { id: 'csv-export' });
    } catch (error) {
      console.error('Error exporting CSV:', error);
      toast.error('Failed to export CSV. Please try again.', { id: 'csv-export' });
    } finally {
      setExportingCSV(false);
    }
  };

  const handleExportPDF = () => {
    if (!analysisResults?.impacts) {
      toast.error('No analysis results to export');
      return;
    }

    try {
      setExportingPDF(true);
      toast.loading('Generating PDF...', { id: 'pdf-export' });

      // Use browser's print to PDF functionality
      window.print();

      toast.success('PDF export dialog opened', { id: 'pdf-export' });
    } catch (error) {
      console.error('Error exporting PDF:', error);
      toast.error('Failed to export PDF', { id: 'pdf-export' });
    } finally {
      setExportingPDF(false);
    }
  };

  const toggleRowExpansion = (idx) => {
    setExpandedRows(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const getSeverityLevel = (changeType) => {
    // Determine severity based on change type
    switch (changeType) {
      case 'added':
        return 'high'; // New requirements are high priority
      case 'modified':
        return 'medium'; // Modified requirements need review
      case 'deleted':
        return 'low'; // Deleted requirements may be low risk
      default:
        return 'medium';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 border-red-500 text-red-900';
      case 'medium':
        return 'bg-yellow-100 border-yellow-500 text-yellow-900';
      case 'low':
        return 'bg-green-100 border-green-500 text-green-900';
      default:
        return 'bg-gray-100 border-gray-500 text-gray-900';
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'high':
        return <Badge className="bg-red-500">High Priority</Badge>;
      case 'medium':
        return <Badge className="bg-yellow-500">Medium Priority</Badge>;
      case 'low':
        return <Badge className="bg-green-500">Low Priority</Badge>;
      default:
        return <Badge>Unknown</Badge>;
    }
  };

  const getChangeTypeBadge = (type) => {
    switch (type) {
      case 'added':
        return <Badge className="bg-green-500">Added</Badge>;
      case 'modified':
        return <Badge className="bg-yellow-500">Modified</Badge>;
      case 'deleted':
        return <Badge className="bg-red-500">Deleted</Badge>;
      default:
        return <Badge>{type}</Badge>;
    }
  };

  const getTextPreview = (text) => {
    if (!text) return 'No text available';
    return text.length > 200 ? text.substring(0, 200) + '...' : text;
  };

  const handleEditSuggestion = (idx) => {
    setEditingImpact(idx);
  };

  const handleSaveSuggestion = (idx) => {
    // Save to local state (in production, you'd save to backend)
    setEditingImpact(null);
    toast.success('Suggested change saved');
  };

  const handleCancelEdit = (idx) => {
    // Restore original value
    const impact = analysisResults?.impacts?.[idx];
    setSuggestedChanges(prev => ({
      ...prev,
      [idx]: impact?.suggested_change || ''
    }));
    setEditingImpact(null);
  };

  const getSummaryStats = () => {
    if (!analysisResults?.impacts) return null;

    const stats = {
      total: analysisResults.impacts.length,
      high: 0,
      medium: 0,
      low: 0,
      byDocument: {}
    };

    analysisResults.impacts.forEach(impact => {
      const severity = getSeverityLevel(impact.change_type);
      stats[severity]++;

      const docNo = impact.qsp_doc || 'Unknown';
      stats.byDocument[docNo] = (stats.byDocument[docNo] || 0) + 1;
    });

    return stats;
  };

  const stats = getSummaryStats();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Gap Analysis</h2>
        <p className="text-gray-600 mt-1">
          Review-ready compliance analysis with document and clause references
        </p>
      </div>

      {/* Run Analysis Button */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <Button
            onClick={handleRunAnalysis}
            disabled={analyzing}
            size="lg"
            className="w-full h-14 text-lg"
          >
            {analyzing ? (
              <>
                <div className="animate-spin h-6 w-6 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                Running Gap Analysis...
              </>
            ) : (
              <>
                <TrendingUp className="h-6 w-6 mr-2" />
                Run Gap Analysis
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Summary Counters */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">{stats.total}</div>
                <div className="text-sm text-gray-600 mt-1">Total Impacts</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-red-600">{stats.high}</div>
                <div className="text-sm text-gray-600 mt-1">High Priority</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-600">{stats.medium}</div>
                <div className="text-sm text-gray-600 mt-1">Medium Priority</div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">{stats.low}</div>
                <div className="text-sm text-gray-600 mt-1">Low Priority</div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Results with View Toggle */}
      {analysisResults && analysisResults.impacts && analysisResults.impacts.length > 0 ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Gap Analysis Results</CardTitle>
                <CardDescription>
                  {analysisResults.total_impacts_found} QSP sections require review
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => setViewMode(viewMode === 'table' ? 'grid' : 'table')}
                  variant="outline"
                  size="sm"
                >
                  {viewMode === 'table' ? (
                    <>
                      <Grid3x3 className="h-4 w-4 mr-1" />
                      Grid View
                    </>
                  ) : (
                    <>
                      <List className="h-4 w-4 mr-1" />
                      Table View
                    </>
                  )}
                </Button>
                <Button
                  onClick={handleExportPDF}
                  disabled={exportingPDF}
                  variant="outline"
                  size="sm"
                >
                  {exportingPDF ? (
                    <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  ) : (
                    <>
                      <FileText className="h-4 w-4 mr-1" />
                      Export PDF
                    </>
                  )}
                </Button>
                <Button
                  onClick={handleExportCSV}
                  disabled={exportingCSV}
                  variant="outline"
                  size="sm"
                >
                  {exportingCSV ? (
                    <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-1" />
                      Export CSV
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {viewMode === 'table' ? (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b-2 bg-gray-50">
                      <th className="px-4 py-3 text-left font-semibold">Priority</th>
                      <th className="px-4 py-3 text-left font-semibold">Regulatory Clause</th>
                      <th className="px-4 py-3 text-left font-semibold">Change Type</th>
                      <th className="px-4 py-3 text-left font-semibold">QSP Doc No.</th>
                      <th className="px-4 py-3 text-left font-semibold">QSP Clause No.</th>
                      <th className="px-4 py-3 text-left font-semibold">QSP Clause Text (Preview)</th>
                      <th className="px-4 py-3 text-left font-semibold">Rationale</th>
                      <th className="px-4 py-3 text-left font-semibold"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysisResults.impacts.map((impact, idx) => {
                      const severity = getSeverityLevel(impact.change_type);
                      return (
                        <React.Fragment key={idx}>
                          <tr className={`border-b hover:bg-gray-50 ${getSeverityColor(severity)} border-l-4`}>
                            <td className="px-4 py-3">
                              {getSeverityBadge(severity)}
                            </td>
                            <td className="px-4 py-3">
                              <span className="font-mono font-bold text-blue-700">
                                {impact.clause_id}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              {getChangeTypeBadge(impact.change_type)}
                            </td>
                            <td className="px-4 py-3">
                              <span className="font-mono text-sm font-semibold">
                                {impact.qsp_doc || 'N/A'}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <span className="font-mono font-bold text-blue-700">
                                {impact.section_path || 'N/A'}
                              </span>
                            </td>
                            <td className="px-4 py-3 max-w-md">
                              <span className="text-gray-700">
                                {getTextPreview(impact.qsp_text || impact.heading)}
                              </span>
                            </td>
                            <td className="px-4 py-3 max-w-xs">
                              <span className="text-gray-600 text-xs">
                                {impact.rationale ? 
                                  impact.rationale.replace(/confidence[:\s]*[\d.]+/gi, '').replace(/\(confidence[^)]*\)/gi, '').trim() 
                                  : 'Review for compliance'}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <button
                                onClick={() => toggleRowExpansion(idx)}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                {expandedRows[idx] ? (
                                  <ChevronUp className="h-5 w-5" />
                                ) : (
                                  <ChevronDown className="h-5 w-5" />
                                )}
                              </button>
                            </td>
                          </tr>
                          {expandedRows[idx] && (
                            <tr className="bg-blue-50 border-b">
                              <td colSpan={8} className="px-4 py-4">
                                <div className="space-y-3">
                                  <div>
                                    <div className="text-xs font-semibold text-gray-700 mb-1">OLD REGULATORY TEXT:</div>
                                    <div className="text-sm text-red-700 bg-red-50 p-2 rounded border-l-4 border-red-500">
                                      {impact.old_text || 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-xs font-semibold text-gray-700 mb-1">NEW REGULATORY TEXT:</div>
                                    <div className="text-sm text-green-700 bg-green-50 p-2 rounded border-l-4 border-green-500">
                                      {impact.new_text || 'N/A'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-xs font-semibold text-gray-700 mb-1">MAPPED QSP CLAUSE TEXT:</div>
                                    <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded border-l-4 border-gray-400">
                                      {impact.qsp_text || impact.heading || 'No text available'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-xs font-semibold text-gray-700 mb-1">RATIONALE:</div>
                                    <div className="text-sm text-blue-900 bg-blue-50 p-2 rounded">
                                      {impact.rationale?.replace(/confidence[:\s]*[\d.]+/gi, '').replace(/\(confidence[^)]*\)/gi, '').trim() || 'Model flagged this section for review based on semantic similarity to regulatory change.'}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="flex items-center justify-between mb-1">
                                      <div className="text-xs font-semibold text-gray-700">SUGGESTED CHANGES:</div>
                                      {editingImpact === idx ? (
                                        <div className="flex gap-2">
                                          <button
                                            onClick={() => handleSaveSuggestion(idx)}
                                            className="text-green-600 hover:text-green-800"
                                          >
                                            <Save className="h-4 w-4" />
                                          </button>
                                          <button
                                            onClick={() => handleCancelEdit(idx)}
                                            className="text-red-600 hover:text-red-800"
                                          >
                                            <X className="h-4 w-4" />
                                          </button>
                                        </div>
                                      ) : (
                                        <button
                                          onClick={() => handleEditSuggestion(idx)}
                                          className="text-blue-600 hover:text-blue-800"
                                        >
                                          <Edit2 className="h-4 w-4" />
                                        </button>
                                      )}
                                    </div>
                                    {editingImpact === idx ? (
                                      <textarea
                                        value={suggestedChanges[idx] || ''}
                                        onChange={(e) => setSuggestedChanges(prev => ({
                                          ...prev,
                                          [idx]: e.target.value
                                        }))}
                                        className="w-full text-sm p-2 border rounded min-h-[100px]"
                                        placeholder="Enter suggested changes to QSP document..."
                                      />
                                    ) : (
                                      <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded border">
                                        {suggestedChanges[idx] || 'No suggested changes yet. Click edit to add.'}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              /* Grid View */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {analysisResults.impacts.map((impact, idx) => {
                  const severity = getSeverityLevel(impact.change_type);
                  return (
                    <Card key={idx} className={`${getSeverityColor(severity)} border-l-4`}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              {getSeverityBadge(severity)}
                              {getChangeTypeBadge(impact.change_type)}
                            </div>
                            <CardTitle className="text-lg">
                              <span className="font-mono">{impact.clause_id}</span>
                            </CardTitle>
                            <CardDescription>
                              QSP: {impact.qsp_doc} • Clause: {impact.section_path}
                            </CardDescription>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 text-sm">
                          <div>
                            <div className="font-semibold text-gray-700">QSP Text:</div>
                            <div className="text-gray-600">
                              {getTextPreview(impact.qsp_text || impact.heading)}
                            </div>
                          </div>
                          <div>
                            <div className="font-semibold text-gray-700">Rationale:</div>
                            <div className="text-gray-600 text-xs">
                              {impact.rationale?.replace(/confidence[:\s]*[\d.]+/gi, '').replace(/\(confidence[^)]*\)/gi, '').trim() || 'Review for compliance'}
                            </div>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            className="w-full mt-2"
                            onClick={() => toggleRowExpansion(idx)}
                          >
                            {expandedRows[idx] ? 'Hide Details' : 'View Details'}
                          </Button>
                          {expandedRows[idx] && (
                            <div className="mt-3 pt-3 border-t space-y-2">
                              <div>
                                <div className="text-xs font-semibold mb-1">Old Text:</div>
                                <div className="text-xs text-red-700 bg-red-50 p-2 rounded">
                                  {impact.old_text || 'N/A'}
                                </div>
                              </div>
                              <div>
                                <div className="text-xs font-semibold mb-1">New Text:</div>
                                <div className="text-xs text-green-700 bg-green-50 p-2 rounded">
                                  {impact.new_text || 'N/A'}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      ) : analysisResults ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-600 font-medium">No impacts found</p>
              <p className="text-sm text-gray-500 mt-1">
                The regulatory changes may not affect your current QSP sections.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <AlertCircle className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 font-medium text-lg">No results yet.</p>
              <p className="text-sm text-gray-500 mt-2">
                Please complete Tabs 1 and 2, then click "Run Gap Analysis."
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Print styles for PDF export */}
      <style>{`
        @media print {
          body * {
            visibility: hidden;
          }
          .print-area, .print-area * {
            visibility: visible;
          }
          .print-area {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
};

export default GapAnalysisEnhanced;
