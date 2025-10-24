import React, { useState } from 'react';
import axios from 'axios';
import { TrendingUp, Download, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const GapAnalysisClean = () => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [runId, setRunId] = useState(null);
  const [exportingCSV, setExportingCSV] = useState(false);
  const [expandedRows, setExpandedRows] = useState({});

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

      {/* Results Table */}
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
                  {analysisResults.impacts.map((impact, idx) => (
                    <React.Fragment key={idx}>
                      <tr className="border-b hover:bg-gray-50">
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
                          <td colSpan={7} className="px-4 py-4">
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
              <p className="text-gray-600 font-medium text-lg">No results yet.</p>
              <p className="text-sm text-gray-500 mt-2">
                Please complete Tabs 1 and 2, then click "Run Gap Analysis."
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default GapAnalysisClean;
