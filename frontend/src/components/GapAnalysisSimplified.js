import React, { useState } from 'react';
import axios from 'axios';
import { TrendingUp, Download, AlertCircle, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const GapAnalysisSimplified = () => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [runId, setRunId] = useState(null);
  const [exportingCSV, setExportingCSV] = useState(false);
  const [expandedRows, setExpandedRows] = useState({});
  const [reviewedItems, setReviewedItems] = useState({});
  const [customRationales, setCustomRationales] = useState({});

  const handleRationaleChange = (idx, value) => {
    setCustomRationales(prev => ({
      ...prev,
      [idx]: value
    }));
  };

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

  const toggleRowExpansion = (idx) => {
    setExpandedRows(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const toggleReviewed = (idx) => {
    setReviewedItems(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const getImpactBadge = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return <Badge className="bg-red-100 text-red-800 border-red-300">🔴 High</Badge>;
      case 'medium':
        return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-300">🟡 Medium</Badge>;
      case 'low':
        return <Badge className="bg-green-100 text-green-800 border-green-300">🟢 Low</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>;
    }
  };

  const getChangeTypeBadge = (type) => {
    switch (type?.toLowerCase()) {
      case 'added':
      case 'new':
        return <Badge className="bg-green-600 text-white">Added</Badge>;
      case 'modified':
        return <Badge className="bg-yellow-600 text-white">Modified</Badge>;
      case 'deleted':
        return <Badge className="bg-red-600 text-white">Deleted</Badge>;
      default:
        return <Badge className="bg-gray-600 text-white">{type || 'Unknown'}</Badge>;
    }
  };

  const getTextPreview = (text) => {
    if (!text) return 'No text available';
    return text.length > 150 ? text.substring(0, 150) + '...' : text;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Gap Analysis</h2>
        <p className="text-gray-600 mt-1">
          Compare regulatory changes against internal QSP documents
        </p>
      </div>

      {/* AI Disclaimer Banner */}
      <Card className="bg-amber-50 border-amber-300">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-amber-900">
              <p className="font-semibold mb-1">Important Notice</p>
              <p>
                This system identifies potential compliance gaps between regulatory and internal documents.
                Results require human review and do not guarantee audit compliance.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

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

      {/* Results Table */}
      {analysisResults && analysisResults.impacts && analysisResults.impacts.length > 0 ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Gap Analysis Results</CardTitle>
                <CardDescription>
                  {analysisResults.total_impacts_found} potential compliance gap(s) identified
                </CardDescription>
              </div>
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
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b-2 bg-gray-50">
                    <th className="px-4 py-3 text-left font-semibold w-12">
                      <input
                        type="checkbox"
                        className="rounded"
                        title="Mark All Reviewed"
                        onChange={(e) => {
                          const newState = {};
                          analysisResults.impacts.forEach((_, idx) => {
                            newState[idx] = e.target.checked;
                          });
                          setReviewedItems(newState);
                        }}
                      />
                    </th>
                    <th className="px-4 py-3 text-left font-semibold">Regulatory Clause</th>
                    <th className="px-4 py-3 text-left font-semibold">Change Type</th>
                    <th className="px-4 py-3 text-left font-semibold">QSP Doc</th>
                    <th className="px-4 py-3 text-left font-semibold">QSP Clause</th>
                    <th className="px-4 py-3 text-left font-semibold">QSP Text (Preview)</th>
                    <th className="px-4 py-3 text-left font-semibold">Rationale</th>
                    <th className="px-4 py-3 text-left font-semibold"></th>
                  </tr>
                </thead>
                <tbody>
                  {analysisResults.impacts.map((impact, idx) => (
                    <React.Fragment key={idx}>
                      <tr className={`border-b hover:bg-gray-50 ${reviewedItems[idx] ? 'bg-green-50' : ''}`}>
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            className="rounded"
                            checked={reviewedItems[idx] || false}
                            onChange={() => toggleReviewed(idx)}
                            title="Mark as Reviewed"
                          />
                        </td>
                        <td className="px-4 py-3">
                          <span className="font-mono font-bold text-blue-700">
                            {impact.reg_clause || impact.clause_id || 'N/A'}
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
                            {impact.qsp_clause || impact.section_path || 'N/A'}
                          </span>
                        </td>
                        <td className="px-4 py-3 max-w-md">
                          <span className="text-gray-700 text-xs">
                            {getTextPreview(impact.qsp_text || impact.heading)}
                          </span>
                        </td>
                        <td className="px-4 py-3 max-w-xs">
                          <span className="text-gray-600 text-xs">
                            {impact.rationale || 'Review for compliance'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => toggleRowExpansion(idx)}
                            className="text-blue-600 hover:text-blue-800"
                            title="View Details"
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
                                <div className="text-sm text-red-700 bg-red-50 p-3 rounded border-l-4 border-red-500">
                                  {impact.old_text || 'N/A'}
                                </div>
                              </div>
                              <div>
                                <div className="text-xs font-semibold text-gray-700 mb-1">NEW REGULATORY TEXT:</div>
                                <div className="text-sm text-green-700 bg-green-50 p-3 rounded border-l-4 border-green-500">
                                  {impact.new_text || 'N/A'}
                                </div>
                              </div>
                              <div>
                                <div className="text-xs font-semibold text-gray-700 mb-1">FULL QSP CLAUSE TEXT:</div>
                                <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded border-l-4 border-gray-400">
                                  {impact.qsp_text_full || impact.qsp_text || impact.heading || 'No text available'}
                                </div>
                              </div>
                              <div>
                                <div className="text-xs font-semibold text-gray-700 mb-1">RATIONALE:</div>
                                <div className="text-sm text-blue-900 bg-blue-50 p-3 rounded">
                                  {impact.rationale || 'Model flagged this section for review based on semantic similarity to regulatory change.'}
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
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
              <p className="text-gray-600 font-medium text-lg">No results yet</p>
              <p className="text-sm text-gray-500 mt-2">
                Complete Tab 1 (Regulatory Diff) and Tab 2 (QSP Upload & Mapping), then run analysis.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default GapAnalysisSimplified;
