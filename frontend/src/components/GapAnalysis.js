import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingUp, Download, AlertCircle, CheckCircle, FileText } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const GapAnalysis = () => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [runId, setRunId] = useState(null);
  const [exporting, setExporting] = useState(false);

  const handleRunAnalysis = async () => {
    try {
      setAnalyzing(true);
      toast.loading('Running gap analysis...', { id: 'analysis' });

      // Get diff results from Tab 1
      const diffResults = localStorage.getItem('regulatory_diff');
      if (!diffResults) {
        toast.error('No regulatory diff found. Please complete Tab 1 first.', { id: 'analysis' });
        setAnalyzing(false);
        return;
      }

      // Get clause map from Tab 2
      const clauseMap = localStorage.getItem('clause_map');
      if (!clauseMap) {
        toast.error('No clause map found. Please complete Tab 2 first.', { id: 'analysis' });
        setAnalyzing(false);
        return;
      }

      const deltas = JSON.parse(diffResults);

      // Run impact analysis
      const response = await axios.post(`${API}/api/impact/analyze`, {
        deltas: deltas.deltas || [],
        top_k: 10
      });

      if (response.data.success) {
        setAnalysisResults(response.data);
        setRunId(response.data.run_id);
        toast.success(
          `✅ Analysis complete: ${response.data.total_impacts_found} impacts found`,
          { id: 'analysis' }
        );
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
      setExporting(true);
      toast.loading('Generating CSV...', { id: 'csv-export' });
      
      const response = await axios.get(
        `${API}/api/impact/report/${runId}?format=csv`,
        { 
          responseType: 'blob',
          headers: {
            'Accept': 'text/csv'
          }
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().toISOString().slice(0, 10);
      link.setAttribute('download', `gap_analysis_${timestamp}_${runId}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('CSV exported successfully', { id: 'csv-export' });
    } catch (error) {
      console.error('Error exporting CSV:', error);
      toast.error(error.response?.data?.message || 'Failed to export CSV', { id: 'csv-export' });
    } finally {
      setExporting(false);
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

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Gap Analysis</h2>
        <p className="text-gray-600 mt-1">
          Run detected regulatory diffs against QSP clause map
        </p>
      </div>

      {/* Run Analysis Button */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="space-y-3">
            <p className="text-sm text-gray-700">
              This will analyze regulatory changes from Tab 1 against the QSP clause map from Tab 2.
            </p>
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
          </div>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {analysisResults && (
        <>
          {/* Summary Stats */}
          <div className="grid md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Changes Analyzed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">
                  {analysisResults.total_changes_analyzed}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Impacts Found
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-orange-600">
                  {analysisResults.total_impacts_found}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-600">
                  Export Results
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={handleExportCSV}
                  disabled={exporting}
                  variant="outline"
                  className="w-full"
                >
                  {exporting ? (
                    <>
                      <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full mr-2"></div>
                      Exporting...
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-2" />
                      Export CSV
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Results Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Clause-Level Mapping Results</CardTitle>
                {analysisResults.warning && (
                  <Badge variant="outline" className="text-yellow-600">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    {analysisResults.warning}
                  </Badge>
                )}
              </div>
              <CardDescription>
                Regulatory changes mapped to internal QSP sections
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Disclaimer */}
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs text-blue-900 italic">
                  ⚠️ Certaro makes intelligent suggestions for human teams to review.
                </p>
              </div>
              {analysisResults.impacts && analysisResults.impacts.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                          Regulatory Clause
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                          Change Type
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                          QSP Document & Clause
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                          Rationale
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysisResults.impacts.map((impact, idx) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <span className="font-mono text-sm font-semibold text-blue-600">
                              {impact.clause_id}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            {getChangeTypeBadge(impact.change_type)}
                          </td>
                          <td className="px-4 py-3">
                            <div>
                              <div className="font-medium text-sm text-gray-900">
                                📄 Document: {impact.qsp_doc || 'N/A'}
                              </div>
                              <div className="font-mono text-sm text-blue-700 font-bold mt-1">
                                Clause: {impact.section_path || 'N/A'}
                              </div>
                              <div className="text-xs text-gray-600 mt-1">
                                Section: {impact.heading}
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm text-gray-700 max-w-md">
                              {impact.rationale ? impact.rationale.replace(/confidence[:\s]*[\d.]+/gi, '').replace(/\(confidence[^)]*\)/gi, '').trim() : 'No rationale provided'}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600 font-medium">No impacts found</p>
                  <p className="text-sm text-gray-500 mt-1">
                    The regulatory changes may not affect your current QSP sections.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* No Results State */}
      {!analysisResults && (
        <Card className="border-gray-200">
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 font-medium text-lg">No Analysis Results Yet</p>
              <p className="text-sm text-gray-500 mt-2 max-w-md mx-auto">
                Complete the workflow in Tab 1 (generate diff) and Tab 2 (upload QSPs), then click "Run Gap Analysis" above.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default GapAnalysis;
