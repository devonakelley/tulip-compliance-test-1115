import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingUp, Download, AlertCircle, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import LoaderSpinner from './LoaderSpinner';
import { DownstreamImpacts } from './DownstreamImpacts';

const API = process.env.REACT_APP_BACKEND_URL;

const GapAnalysisSimplified = () => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [runId, setRunId] = useState(null);
  const [exportingCSV, setExportingCSV] = useState(false);
  const [expandedRows, setExpandedRows] = useState({});
  const [reviewedItems, setReviewedItems] = useState({});
  const [customRationales, setCustomRationales] = useState({});
  const [loadingResults, setLoadingResults] = useState(false);
  const [savingReview, setSavingReview] = useState({});

  // Load saved results on mount if runId exists in localStorage
  useEffect(() => {
    const savedRunId = localStorage.getItem('gap_analysis_run_id');
    if (savedRunId) {
      loadSavedResults(savedRunId);
    }
  }, []);

  const loadSavedResults = async (savedRunId) => {
    try {
      setLoadingResults(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/impact/results/${savedRunId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data && response.data.success) {
        setAnalysisResults(response.data);
        setRunId(savedRunId);
        
        // Restore review states and rationales
        const reviewed = {};
        const rationales = {};
        response.data.impacts?.forEach((impact, idx) => {
          reviewed[idx] = impact.is_reviewed || false;
          rationales[idx] = impact.custom_rationale || '';
        });
        setReviewedItems(reviewed);
        setCustomRationales(rationales);
      }
    } catch (error) {
      console.error('Error loading saved results:', error);
      // Don't show error toast - just means no saved results exist
    } finally {
      setLoadingResults(false);
    }
  };

  const updateGapResult = async (resultId, updates) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API}/api/impact/update_result/${resultId}`,
        updates,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
    } catch (error) {
      console.error('Error updating gap result:', error);
      toast.error('Failed to save changes');
    }
  };

  const handleReviewToggle = async (idx) => {
    const newValue = !reviewedItems[idx];
    setReviewedItems(prev => ({
      ...prev,
      [idx]: newValue
    }));

    // Save to backend
    const impact = analysisResults?.impacts?.[idx];
    if (impact && impact.id) {
      setSavingReview(prev => ({ ...prev, [idx]: true }));
      await updateGapResult(impact.id, { is_reviewed: newValue });
      setSavingReview(prev => ({ ...prev, [idx]: false }));
    }
  };

  const handleRationaleBlur = async (idx) => {
    const impact = analysisResults?.impacts?.[idx];
    if (impact && impact.id) {
      setSavingReview(prev => ({ ...prev, [idx]: true }));
      await updateGapResult(impact.id, { custom_rationale: customRationales[idx] || '' });
      setSavingReview(prev => ({ ...prev, [idx]: false }));
      toast.success('Rationale saved', { duration: 1000 });
    }
  };

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
        
        // Save runId for persistence across sessions
        localStorage.setItem('gap_analysis_run_id', response.data.run_id);
        
        // Initialize review states from saved data
        const reviewed = {};
        const rationales = {};
        response.data.impacts?.forEach((impact, idx) => {
          reviewed[idx] = impact.is_reviewed || false;
          rationales[idx] = impact.custom_rationale || '';
        });
        setReviewedItems(reviewed);
        setCustomRationales(rationales);
        
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

  const toggleReviewed = async (idx) => {
    await handleReviewToggle(idx);
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
    return text.length > 250 ? text.substring(0, 250) + '...' : text;
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
            disabled={analyzing || loadingResults}
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

      {/* Loading State */}
      {(analyzing || loadingResults) && (
        <Card>
          <CardContent>
            <LoaderSpinner message={analyzing ? "Analyzing compliance gaps..." : "Loading saved results..."} size="lg" />
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!analysisResults && !analyzing && !loadingResults && (
        <Card className="bg-gray-50">
          <CardContent className="py-12 text-center">
            <AlertCircle className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 mb-2">No Analysis Results</h3>
            <p className="text-gray-600">
              Run a gap analysis to view compliance impacts.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Results Table */}
      {analysisResults && analysisResults.impacts && analysisResults.impacts.length > 0 && !analyzing && !loadingResults ? (
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
                    <th className="px-4 py-3 text-left font-semibold">Impact</th>
                    <th className="px-4 py-3 text-left font-semibold">Match Type</th>
                    <th className="px-4 py-3 text-left font-semibold">Confidence</th>
                    <th className="px-4 py-3 text-left font-semibold">QSP Doc</th>
                    <th className="px-4 py-3 text-left font-semibold">QSP Clause</th>
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
                          <span className="font-mono text-sm font-bold text-blue-700">
                            {impact.regulatory_clause || 
                             `${impact.regulatory_doc || 'ISO 14971:2020'} | Clause ${impact.reg_clause || impact.clause_id || 'N/A'}${impact.reg_title ? ` — ${impact.reg_title}` : ''}`}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {getChangeTypeBadge(impact.change_type)}
                        </td>
                        <td className="px-4 py-3">
                          {getImpactBadge(impact.impact_level)}
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
                          <td colSpan={9} className="px-4 py-4">
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
                                <div className="text-xs font-semibold text-gray-700 mb-1">AI RATIONALE:</div>
                                <div className="text-sm text-blue-900 bg-blue-50 p-3 rounded">
                                  {impact.rationale || 'Model flagged this section for review based on semantic similarity to regulatory change.'}
                                  {impact.similarity_score && (
                                    <div className="mt-2 text-xs text-blue-700">
                                      Semantic Similarity Score: <strong>{(impact.similarity_score * 100).toFixed(1)}%</strong>
                                    </div>
                                  )}
                                </div>
                              </div>
                              
                              {/* DOWNSTREAM IMPACTS: Forms and Work Instructions */}
                              {impact.downstream_impacts && (
                                <div>
                                  <div className="text-xs font-semibold text-gray-700 mb-2">CASCADE IMPACT ANALYSIS:</div>
                                  <div className="bg-white p-3 rounded border">
                                    <DownstreamImpacts impacts={impact.downstream_impacts} />
                                  </div>
                                </div>
                              )}
                              
                              {!impact.downstream_impacts && (
                                <div className="text-sm text-amber-600 bg-amber-50 p-3 rounded border-l-4 border-amber-400">
                                  ⚠️ Cascade analysis not available. Re-generate clause map to enable downstream impact detection.
                                </div>
                              )}
                              
                              <div>
                                <div className="text-xs font-semibold text-gray-700 mb-2">CUSTOM RATIONALE / NOTES:</div>
                                <textarea
                                  className="w-full text-sm p-3 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                  rows="3"
                                  placeholder="Add custom rationale, justification, or notes for audit trail..."
                                  value={customRationales[idx] || ''}
                                  onChange={(e) => handleRationaleChange(idx, e.target.value)}
                                  onBlur={() => handleRationaleBlur(idx)}
                                  disabled={savingReview[idx]}
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                  {savingReview[idx] ? 'Saving...' : 'Auto-saves when you click away'}
                                </p>
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
