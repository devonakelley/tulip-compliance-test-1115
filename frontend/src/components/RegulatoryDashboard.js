import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, FileText, GitCompare, TrendingUp, Download, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const RegulatoryDashboard = () => {
  const [oldPdf, setOldPdf] = useState(null);
  const [newPdf, setNewPdf] = useState(null);
  const [uploadingOld, setUploadingOld] = useState(false);
  const [uploadingNew, setUploadingNew] = useState(false);
  const [processingDiff, setProcessingDiff] = useState(false);
  const [deltas, setDeltas] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [impactResults, setImpactResults] = useState(null);
  const [internalDocs, setInternalDocs] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [loadingInternalDocs, setLoadingInternalDocs] = useState(false);
  const [expandedDeltas, setExpandedDeltas] = useState({});
  const [expandedImpacts, setExpandedImpacts] = useState({});
  
  // Fetch previously uploaded internal documents
  useEffect(() => {
    const fetchInternalDocs = async () => {
      try {
        setLoadingInternalDocs(true);
        const response = await axios.get(`${API}/regulatory/list/internal`);
        if (response.data.success) {
          setInternalDocs(response.data.documents || []);
        }
      } catch (error) {
        console.error('Error fetching internal docs:', error);
      } finally {
        setLoadingInternalDocs(false);
      }
    };
    fetchInternalDocs();
  }, []);

  const handleOldPdfUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Please upload a PDF file');
      return;
    }
    
    try {
      setUploadingOld(true);
      toast.loading('Uploading old version...', { id: 'old-upload' });
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_type', 'old');
      formData.append('standard_name', 'ISO 13485');
      
      const response = await axios.post(`${API}/api/regulatory/upload/regulatory`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setOldPdf(response.data);
      toast.success('Old version uploaded', { id: 'old-upload' });
    } catch (error) {
      console.error(error);
      toast.error('Failed to upload old version', { id: 'old-upload' });
    } finally {
      setUploadingOld(false);
    }
  };
  
  const handleNewPdfUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Please upload a PDF file');
      return;
    }
    
    try {
      setUploadingNew(true);
      toast.loading('Uploading new version...', { id: 'new-upload' });
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_type', 'new');
      formData.append('standard_name', 'ISO 13485');
      
      const response = await axios.post(`${API}/api/regulatory/upload/regulatory`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setNewPdf(response.data);
      toast.success('New version uploaded', { id: 'new-upload' });
    } catch (error) {
      console.error(error);
      toast.error('Failed to upload new version', { id: 'new-upload' });
    } finally {
      setUploadingNew(false);
    }
  };
  
  const handleQSPUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    let successCount = 0;
    let failCount = 0;

    for (const file of files) {
      try {
        toast.loading(`Uploading ${file.name}...`, { id: `qsp-${file.name}` });
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(`${API}/api/documents/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        successCount++;
        toast.success(`✅ Uploaded ${file.name}`, { id: `qsp-${file.name}` });
      } catch (error) {
        console.error(`Error uploading ${file.name}:`, error);
        failCount++;
        toast.error(`❌ Failed to upload ${file.name}`, { id: `qsp-${file.name}` });
      }
    }

    if (files.length > 1) {
      if (successCount > 0 && failCount === 0) {
        toast.success(`🎉 All ${successCount} files uploaded successfully!`);
      } else if (successCount > 0) {
        toast.info(`⚠️ Uploaded ${successCount} files, ${failCount} failed`);
      }
    }

    // Refresh internal docs list
    if (successCount > 0) {
      try {
        const response = await axios.get(`${API}/api/documents`);
        if (response.data) {
          setInternalDocs(response.data);
        }
      } catch (error) {
        console.error('Error fetching updated docs:', error);
      }
    }

    event.target.value = '';
  };

  const processDiff = async () => {
    if (!oldPdf || !newPdf) {
      toast.error('Please upload both old and new versions');
      return;
    }
    
    try {
      setProcessingDiff(true);
      toast.loading('Processing differences...', { id: 'diff' });
      
      const formData = new FormData();
      formData.append('old_file_path', oldPdf.file_path);
      formData.append('new_file_path', newPdf.file_path);
      
      const response = await axios.post(`${API}/api/regulatory/preprocess/iso_diff`, formData);
      
      setDeltas(response.data);
      toast.success(`Found ${response.data.total_changes} changes`, { id: 'diff' });
    } catch (error) {
      console.error(error);
      toast.error('Failed to process differences', { id: 'diff' });
    } finally {
      setProcessingDiff(false);
    }
  };
  
  const runImpactAnalysis = async () => {
    if (!deltas) {
      toast.error('Please process differences first');
      return;
    }
    
    try {
      setAnalyzing(true);
      toast.loading('Analyzing impact on QSP sections...', { id: 'analyze' });
      
      // Use the deltas to run impact analysis
      const response = await axios.post(`${API}/api/impact/analyze`, {
        deltas: deltas.deltas || deltas.deltas?.slice(0, 10) || [],
        top_k: 5
      });
      
      setImpactResults(response.data);
      toast.success(`Found ${response.data.total_impacts_found} potential impacts`, { id: 'analyze' });
    } catch (error) {
      console.error(error);
      toast.error('Failed to analyze impacts', { id: 'analyze' });
    } finally {
      setAnalyzing(false);
    }
  };
  
  const getChangeTypeBadge = (type) => {
    if (type === 'added') return <Badge className="bg-green-500">Added</Badge>;
    if (type === 'modified') return <Badge className="bg-yellow-500">Modified</Badge>;
    if (type === 'deleted') return <Badge className="bg-red-500">Deleted</Badge>;
    return <Badge>{type}</Badge>;
  };
  
  const getConfidenceBadge = (confidence) => {
    if (confidence > 0.75) return <Badge className="bg-green-500">High: {(confidence * 100).toFixed(0)}%</Badge>;
    if (confidence > 0.60) return <Badge className="bg-yellow-500">Medium: {(confidence * 100).toFixed(0)}%</Badge>;
    return <Badge className="bg-gray-500">Low: {(confidence * 100).toFixed(0)}%</Badge>;
  };
  
  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Regulatory Change Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Upload old & new regulatory PDFs to auto-detect changes and map impacts
          </p>
        </div>
      </div>
      
      {/* Step 1: Upload PDFs */}
      <Card>
        <CardHeader>
          <CardTitle>Step 1: Upload Regulatory Documents</CardTitle>
          <CardDescription>
            Upload both old and new versions to automatically detect changes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            {/* Old Version Upload */}
            <div className="space-y-4">
              <h3 className="font-semibold flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-500" />
                Old Version (e.g., ISO 13485:2016)
              </h3>
              <div>
                <input
                  type="file"
                  id="old-pdf-upload"
                  accept=".pdf"
                  className="hidden"
                  onChange={handleOldPdfUpload}
                  disabled={uploadingOld}
                />
                <label
                  htmlFor="old-pdf-upload"
                  className={`flex items-center justify-center gap-2 p-6 border-2 border-dashed rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors ${
                    uploadingOld ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  <Upload className="h-5 w-5" />
                  <span>{oldPdf ? oldPdf.filename : 'Choose PDF file'}</span>
                </label>
              </div>
              
              {oldPdf && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="font-medium">{oldPdf.filename}</p>
                      <p className="text-sm text-muted-foreground">
                        {(oldPdf.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* New Version Upload */}
            <div className="space-y-4">
              <h3 className="font-semibold flex items-center gap-2">
                <FileText className="h-5 w-5 text-green-500" />
                New Version (e.g., ISO 13485:2024)
              </h3>
              <div>
                <input
                  type="file"
                  id="new-pdf-upload"
                  accept=".pdf"
                  className="hidden"
                  onChange={handleNewPdfUpload}
                  disabled={uploadingNew}
                />
                <label
                  htmlFor="new-pdf-upload"
                  className={`flex items-center justify-center gap-2 p-6 border-2 border-dashed rounded-lg cursor-pointer hover:border-green-500 hover:bg-green-50 transition-colors ${
                    uploadingNew ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  <Upload className="h-5 w-5" />
                  <span>{newPdf ? newPdf.filename : 'Choose PDF file'}</span>
                </label>
              </div>
              
              {newPdf && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="font-medium">{newPdf.filename}</p>
                      <p className="text-sm text-muted-foreground">
                        {(newPdf.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <div className="mt-6">
            <Button
              onClick={processDiff}
              disabled={!oldPdf || !newPdf || processingDiff}
              className="w-full h-12"
            >
              {processingDiff ? (
                <>
                  <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                  Processing Differences...
                </>
              ) : (
                <>
                  <GitCompare className="h-5 w-5 mr-2" />
                  Generate Diff & Detect Changes
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Internal QSP Upload */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Internal QSP Documents</CardTitle>
          <CardDescription>
            Upload your Quality System Procedure documents to analyze impact
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-3" />
            <input
              type="file"
              id="qsp-upload"
              accept=".docx,.txt,.pdf"
              multiple
              className="hidden"
              onChange={handleQSPUpload}
            />
            <label
              htmlFor="qsp-upload"
              className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
            >
              <Upload className="h-5 w-5 mr-2" />
              Select QSP Files
            </label>
            <p className="mt-2 text-sm text-gray-500">
              Supports .docx, .txt, and .pdf files • Select multiple files at once
            </p>
          </div>
          
          {internalDocs.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">
                {internalDocs.length} QSP document(s) uploaded
              </p>
              <div className="max-h-40 overflow-y-auto space-y-2">
                {internalDocs.map((doc, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                    <FileText className="h-4 w-4 text-blue-600" />
                    <span className="text-sm flex-1">{doc.filename}</span>
                    <span className="text-xs text-gray-500">
                      {(doc.size / 1024).toFixed(2)} KB
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Step 2: Diff Results */}
      {deltas && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Step 2: Detected Changes (Unified Diff)</CardTitle>
                <CardDescription>
                  {deltas.total_changes} changes found between versions
                </CardDescription>
              </div>
              <div className="flex gap-2 text-sm">
                <Badge className="bg-green-500">{deltas.summary?.added || 0} Added</Badge>
                <Badge className="bg-yellow-500">{deltas.summary?.modified || 0} Modified</Badge>
                <Badge className="bg-red-500">{deltas.summary?.deleted || 0} Deleted</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[500px] overflow-y-auto">
              {(deltas.deltas || []).map((delta, idx) => (
                <div key={idx} className="border rounded-lg overflow-hidden">
                  <div className="bg-gray-50 p-3 flex items-center justify-between cursor-pointer hover:bg-gray-100" onClick={() => setExpandedDeltas(prev => ({...prev, [idx]: !prev[idx]}))}>
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-blue-600 font-mono">Clause {delta.clause_id}</h4>
                      {getChangeTypeBadge(delta.change_type)}
                    </div>
                    <span className="text-sm text-gray-500">{expandedDeltas[idx] ? '▲' : '▼'} Details</span>
                  </div>
                  
                  {expandedDeltas[idx] && (
                    <div className="p-4 space-y-3 bg-white">
                      {delta.change_type === 'added' && (
                        <div className="bg-green-50 border-l-4 border-green-500 p-3 rounded">
                          <div className="text-sm font-semibold text-green-900 mb-2">✅ ADDED (New Requirement)</div>
                          <div className="text-sm text-green-800 whitespace-pre-wrap">{delta.new_text}</div>
                        </div>
                      )}
                      
                      {delta.change_type === 'deleted' && (
                        <div className="bg-red-50 border-l-4 border-red-500 p-3 rounded">
                          <div className="text-sm font-semibold text-red-900 mb-2">❌ DELETED (Removed Requirement)</div>
                          <div className="text-sm text-red-800 line-through whitespace-pre-wrap">{delta.old_text}</div>
                        </div>
                      )}
                      
                      {delta.change_type === 'modified' && (
                        <>
                          <div className="bg-red-50 border-l-4 border-red-500 p-3 rounded">
                            <div className="text-sm font-semibold text-red-900 mb-2">📝 OLD VERSION</div>
                            <div className="text-sm text-red-800 whitespace-pre-wrap">{delta.old_text}</div>
                          </div>
                          <div className="bg-green-50 border-l-4 border-green-500 p-3 rounded">
                            <div className="text-sm font-semibold text-green-900 mb-2">📝 NEW VERSION</div>
                            <div className="text-sm text-green-800 whitespace-pre-wrap">{delta.new_text}</div>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Step 2.5: Select Internal Docs */}
      {deltas && (
        <Card>
          <CardHeader>
            <CardTitle>Step 2.5: Select Internal QSP Documents ({selectedDocs.length} selected)</CardTitle>
            <CardDescription>
              Choose which internal documents to analyze for potential impacts
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingInternalDocs ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
              </div>
            ) : internalDocs.length === 0 ? (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-center gap-2 text-yellow-800">
                  <AlertCircle className="h-5 w-5" />
                  <p className="text-sm">No internal documents found. Please upload QSP documents first via the Documents page.</p>
                </div>
              </div>
            ) : (
              <>
                <div className="space-y-2 max-h-80 overflow-y-auto mb-4">
                  {internalDocs.map((doc, idx) => (
                    <div
                      key={idx}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedDocs.some(d => d.filename === doc.filename)
                          ? 'bg-blue-50 border-blue-300'
                          : 'bg-white hover:bg-gray-50'
                      }`}
                      onClick={() => {
                        setSelectedDocs(prev => {
                          const isSelected = prev.some(d => d.filename === doc.filename);
                          if (isSelected) {
                            return prev.filter(d => d.filename !== doc.filename);
                          } else {
                            return [...prev, doc];
                          }
                        });
                      }}
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={selectedDocs.some(d => d.filename === doc.filename)}
                          onChange={() => {}}
                          className="w-4 h-4"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-sm">{doc.filename}</div>
                          <div className="text-xs text-gray-500">
                            {(doc.size / 1024).toFixed(2)} KB
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-4">
                  <Button
                    onClick={runImpactAnalysis}
                    disabled={analyzing || selectedDocs.length === 0}
                    className="w-full h-12"
                  >
                    {analyzing ? (
                      <>
                        <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                        Analyzing Impact on {selectedDocs.length} QSPs...
                      </>
                    ) : (
                      <>
                        <TrendingUp className="h-5 w-5 mr-2" />
                        Run Impact Analysis on {selectedDocs.length} Selected QSPs
                      </>
                    )}
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}
      
      {/* Step 3: Impact Results */}
      {impactResults && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Step 3: Impact on Internal QSPs</CardTitle>
                <CardDescription>
                  {impactResults.total_impacts_found} QSP sections may need review
                </CardDescription>
              </div>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export Report
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {impactResults.warning && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg mb-4">
                <div className="flex items-center gap-2 text-yellow-800">
                  <AlertCircle className="h-5 w-5" />
                  <p className="text-sm">{impactResults.warning}</p>
                </div>
              </div>
            )}
            
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {(impactResults.impacts || []).map((impact, idx) => (
                <div key={idx} className="border rounded-lg overflow-hidden hover:shadow-md transition-shadow">
                  <div className="bg-orange-50 p-3 flex items-start justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <AlertCircle className="h-5 w-5 text-orange-500 flex-shrink-0 mt-1" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono font-bold text-blue-600 text-sm">Reg: {impact.clause_id}</span>
                          <span className="text-gray-400">→</span>
                          <span className="font-mono font-semibold text-sm">{impact.section_path}</span>
                          {getChangeTypeBadge(impact.change_type)}
                        </div>
                        <p className="font-medium text-sm">{impact.qsp_doc}</p>
                        <p className="text-sm text-gray-600">{impact.heading}</p>
                      </div>
                    </div>
                    <div className="ml-4 flex-shrink-0">
                      {getConfidenceBadge(impact.confidence)}
                    </div>
                  </div>
                  
                  <div className="p-4 bg-white space-y-3">
                    <div 
                      className="cursor-pointer flex items-center gap-2 text-blue-600 hover:text-blue-800"
                      onClick={() => setExpandedImpacts(prev => ({...prev, [idx]: !prev[idx]}))}
                    >
                      <span className="text-sm font-semibold">
                        {expandedImpacts[idx] ? '▼' : '▶'} Show Details
                      </span>
                    </div>
                    
                    {expandedImpacts[idx] && (
                      <div className="space-y-3 pl-4 border-l-2 border-blue-200">
                        <div className="bg-blue-50 p-3 rounded">
                          <div className="text-xs font-semibold text-blue-900 mb-2">🔍 WHY THIS WAS FLAGGED:</div>
                          <p className="text-sm text-blue-800">{impact.rationale}</p>
                        </div>
                        
                        <div className="bg-gray-50 p-3 rounded">
                          <div className="text-xs font-semibold text-gray-900 mb-2">📄 REGULATORY CHANGE SOURCE:</div>
                          <div className="text-sm text-gray-700">
                            <span className="font-mono font-bold text-blue-600">Clause {impact.clause_id}</span>
                            {deltas && deltas.deltas && (() => {
                              const relatedDelta = deltas.deltas.find(d => d.clause_id === impact.clause_id);
                              if (relatedDelta) {
                                return (
                                  <div className="mt-2 space-y-2">
                                    {relatedDelta.change_type === 'added' && (
                                      <div className="bg-green-50 border-l-2 border-green-500 p-2 rounded text-xs">
                                        <div className="font-semibold text-green-900 mb-1">New Requirement:</div>
                                        <div className="text-green-800">{relatedDelta.new_text?.slice(0, 300)}...</div>
                                      </div>
                                    )}
                                    {relatedDelta.change_type === 'modified' && (
                                      <div className="bg-yellow-50 border-l-2 border-yellow-500 p-2 rounded text-xs">
                                        <div className="font-semibold text-yellow-900 mb-1">Modified Requirement:</div>
                                        <div className="text-yellow-800">{relatedDelta.new_text?.slice(0, 300)}...</div>
                                      </div>
                                    )}
                                    {relatedDelta.change_type === 'deleted' && (
                                      <div className="bg-red-50 border-l-2 border-red-500 p-2 rounded text-xs">
                                        <div className="font-semibold text-red-900 mb-1">Deleted Requirement:</div>
                                        <div className="text-red-800">{relatedDelta.old_text?.slice(0, 300)}...</div>
                                      </div>
                                    )}
                                  </div>
                                );
                              }
                              return <p className="text-xs text-gray-500 mt-1">(Full text available in Diff view)</p>;
                            })()}
                          </div>
                        </div>
                        
                        <div className="bg-purple-50 p-3 rounded">
                          <div className="text-xs font-semibold text-purple-900 mb-2">✏️ ACTION REQUIRED:</div>
                          <p className="text-sm text-purple-800">Review section "{impact.heading}" in {impact.qsp_doc} and update to align with the new regulatory requirement.</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Instructions */}
      {!deltas && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="h-10 w-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                  ?
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-2">How to Use This Dashboard</h3>
                <ol className="space-y-2 text-sm">
                  <li>1. Upload the <strong>old version</strong> of your regulatory standard (e.g., ISO 13485:2016)</li>
                  <li>2. Upload the <strong>new version</strong> (e.g., ISO 13485:2024)</li>
                  <li>3. Click <strong>"Generate Diff"</strong> to automatically detect all changes</li>
                  <li>4. Review the detected changes (added, modified, deleted clauses)</li>
                  <li>5. Click <strong>"Run Impact Analysis"</strong> to see which QSP sections need updating</li>
                  <li>6. Export the report for your QA/RA team to review</li>
                </ol>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default RegulatoryDashboard;
