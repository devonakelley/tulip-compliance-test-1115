import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingUp, Download, AlertCircle, CheckCircle, FileText, ChevronDown, ChevronUp, Eye, Code } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const GapAnalysisNew = () => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [runId, setRunId] = useState(null);
  const [exportingCSV, setExportingCSV] = useState(false);
  const [exportingPDF, setExportingPDF] = useState(false);
  const [expandedClauses, setExpandedClauses] = useState({});
  const [viewMode, setViewMode] = useState({}); // 'summary' or 'diff' per clause
  const [editedSuggestions, setEditedSuggestions] = useState({});
  const [groupedResults, setGroupedResults] = useState([]);

  useEffect(() => {
    if (analysisResults && analysisResults.impacts) {
      // Group impacts by regulatory clause
      const grouped = {};
      analysisResults.impacts.forEach(impact => {
        const clauseId = impact.clause_id;
        if (!grouped[clauseId]) {
          grouped[clauseId] = {
            clause_id: clauseId,
            change_type: impact.change_type,
            impacts: []
          };
        }
        grouped[clauseId].impacts.push(impact);
      });
      setGroupedResults(Object.values(grouped));
    }
  }, [analysisResults]);

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
      setExportingCSV(true);
      toast.loading('Generating CSV...', { id: 'csv-export' });
      
      const response = await axios.get(
        `${API}/api/impact/report/${runId}?format=csv`,
        { 
          responseType: 'blob'
        }
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
    toast.info('PDF export coming soon');
    // TODO: Implement PDF generation using jsPDF or similar
  };

  const toggleClause = (clauseId) => {
    setExpandedClauses(prev => ({
      ...prev,
      [clauseId]: !prev[clauseId]
    }));
  };

  const toggleViewMode = (clauseId) => {
    setViewMode(prev => ({
      ...prev,
      [clauseId]: prev[clauseId] === 'diff' ? 'summary' : 'diff'
    }));
  };

  const handleEditSuggestion = (impactId, newText) => {
    setEditedSuggestions(prev => ({
      ...prev,
      [impactId]: newText
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

  const getImpactColor = (confidence) => {
    if (confidence > 0.75) return 'bg-green-50 border-green-200';
    if (confidence > 0.6) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  const getStatusBadge = (impacts) => {
    const avgConfidence = impacts.reduce((sum, i) => sum + (i.confidence || 0), 0) / impacts.length;
    if (avgConfidence > 0.75) return <Badge className="bg-green-500">✓ Low Impact</Badge>;
    if (avgConfidence > 0.6) return <Badge className="bg-yellow-500">⚠️ Review Needed</Badge>;
    return <Badge className="bg-red-500">🔴 High Impact</Badge>;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Gap Analysis</h2>
        <p className="text-gray-600 mt-1">
          Review regulatory changes mapped to internal QSP sections
        </p>
      </div>

      {/* Disclaimer */}
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-900 italic">
          ⚠️ Certaro makes intelligent suggestions for human teams to review.
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
          {/* Summary Counters */}
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
                <div className="flex gap-2">
                  <Button
                    onClick={handleExportCSV}
                    disabled={exportingCSV}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    {exportingCSV ? (
                      <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                    ) : (
                      <>
                        <Download className="h-4 w-4 mr-1" />
                        CSV
                      </>
                    )}
                  </Button>
                  <Button
                    onClick={handleExportPDF}
                    disabled={exportingPDF}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <Download className="h-4 w-4 mr-1" />
                    PDF
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Clause-Grouped Results */}
          <div className="space-y-4">
            {groupedResults.length > 0 ? (
              groupedResults.map((clause) => (
                <Card key={clause.clause_id} className={`${getImpactColor(clause.impacts[0]?.confidence || 0)}`}>
                  {/* Collapsed View */}
                  <CardHeader 
                    className="cursor-pointer hover:bg-gray-50/50"
                    onClick={() => toggleClause(clause.clause_id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="font-mono font-bold text-lg text-blue-700">
                          Clause {clause.clause_id}
                        </span>
                        {getChangeTypeBadge(clause.change_type)}
                        {getStatusBadge(clause.impacts)}
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm text-gray-600">
                          Impacted QSPs: {clause.impacts.length}
                        </span>
                        {expandedClauses[clause.clause_id] ? (
                          <ChevronUp className="h-5 w-5" />
                        ) : (
                          <ChevronDown className="h-5 w-5" />
                        )}
                      </div>
                    </div>
                  </CardHeader>

                  {/* Expanded View */}
                  {expandedClauses[clause.clause_id] && (
                    <CardContent>
                      {/* View Toggle */}
                      <div className="flex gap-2 mb-4">
                        <Button
                          size="sm"
                          variant={viewMode[clause.clause_id] !== 'diff' ? 'default' : 'outline'}
                          onClick={() => setViewMode(prev => ({ ...prev, [clause.clause_id]: 'summary' }))}
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          Summary
                        </Button>
                        <Button
                          size="sm"
                          variant={viewMode[clause.clause_id] === 'diff' ? 'default' : 'outline'}
                          onClick={() => toggleViewMode(clause.clause_id)}
                        >
                          <Code className="h-4 w-4 mr-1" />
                          Diff View
                        </Button>
                      </div>

                      {/* Diff View */}
                      {viewMode[clause.clause_id] === 'diff' && (
                        <div className="mb-4 p-4 bg-gray-50 rounded-lg font-mono text-sm">
                          <div className="space-y-2">
                            <div className="text-red-700">
                              - Old: {clause.impacts[0]?.old_text || 'N/A'}
                            </div>
                            <div className="text-green-700">
                              + New: {clause.impacts[0]?.new_text || 'N/A'}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Impacts Table */}
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse">
                          <thead>
                            <tr className="border-b bg-white">
                              <th className="px-4 py-3 text-left text-sm font-semibold">QSP Document & Clause</th>
                              <th className="px-4 py-3 text-left text-sm font-semibold">Current Text</th>
                              <th className="px-4 py-3 text-left text-sm font-semibold">Suggested Change</th>
                              <th className="px-4 py-3 text-left text-sm font-semibold">Rationale</th>
                            </tr>
                          </thead>
                          <tbody>
                            {clause.impacts.map((impact, idx) => (
                              <tr key={idx} className="border-b bg-white hover:bg-gray-50">
                                <td className="px-4 py-3">
                                  <div>
                                    <div className="font-medium text-sm">
                                      📄 {impact.qsp_doc || 'N/A'}
                                    </div>
                                    <div className="font-mono text-sm font-bold text-blue-700 mt-1">
                                      Clause: {impact.section_path || 'N/A'}
                                    </div>
                                    <div className="text-xs text-gray-600 mt-1">
                                      {impact.heading}
                                    </div>
                                  </div>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="text-sm text-gray-700 max-w-xs">
                                    {impact.qsp_text || 'No current text available'}
                                  </div>
                                </td>
                                <td className="px-4 py-3">
                                  <textarea
                                    className="w-full p-2 text-sm border rounded-md focus:ring-2 focus:ring-blue-500"
                                    rows={3}
                                    defaultValue={editedSuggestions[impact.impact_id] || impact.suggested_text || 'Update section to align with new regulatory requirements.'}
                                    onChange={(e) => handleEditSuggestion(impact.impact_id, e.target.value)}
                                    placeholder="Enter suggested changes..."
                                  />
                                </td>
                                <td className="px-4 py-3">
                                  <div className="text-sm text-gray-700 max-w-xs">
                                    {impact.rationale?.replace(/confidence[:\s]*[\d.]+/gi, '').replace(/\(confidence[^)]*\)/gi, '').trim() || 'No rationale provided'}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  )}
                </Card>
              ))
            ) : (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-8 text-gray-500">
                    <AlertCircle className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p>No impacts found</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </>
      )}

      {/* Empty State */}
      {!analysisResults && (
        <Card className="border-gray-200">
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 font-medium text-lg">No results yet.</p>
              <p className="text-sm text-gray-500 mt-2 max-w-md mx-auto">
                Please complete Tabs 1 and 2, then click "Run Gap Analysis."
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default GapAnalysisNew;
