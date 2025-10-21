import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, FileText, AlertCircle, CheckCircle, TrendingUp, Download } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import toast from 'react-hot-toast';

const API = process.env.REACT_APP_BACKEND_URL;

const ChangeImpactDetector = () => {
  const [deltasFile, setDeltasFile] = useState(null);
  const [qspSections, setQspSections] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [runs, setRuns] = useState([]);
  
  useEffect(() => {
    fetchRuns();
  }, []);
  
  const fetchRuns = async () => {
    try {
      const response = await axios.get(`${API}/impact/runs`);
      setRuns(response.data.runs || []);
    } catch (error) {
      console.error('Error fetching runs:', error);
    }
  };
  
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const deltas = JSON.parse(e.target.result);
        setDeltasFile({ name: file.name, deltas });
        toast.success(`Loaded ${deltas.length} regulatory changes`);
      } catch (error) {
        toast.error('Invalid JSON file');
      }
    };
    reader.readAsText(file);
  };
  
  const handleQSPUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const sections = JSON.parse(e.target.result);
        setQspSections(sections);
        toast.success(`Loaded ${sections.length} QSP sections`);
      } catch (error) {
        toast.error('Invalid JSON file');
      }
    };
    reader.readAsText(file);
  };
  
  const ingestQSP = async () => {
    if (qspSections.length === 0) {
      toast.error('Please upload QSP sections first');
      return;
    }
    
    try {
      toast.loading('Ingesting QSP sections...', { id: 'ingest' });
      
      const response = await axios.post(`${API}/impact/ingest_qsp`, {
        doc_name: 'Uploaded QSP Document',
        sections: qspSections
      });
      
      toast.success(`Ingested ${response.data.sections_embedded} sections`, { id: 'ingest' });
    } catch (error) {
      toast.error('Failed to ingest QSP', { id: 'ingest' });
      console.error(error);
    }
  };
  
  const runAnalysis = async () => {
    if (!deltasFile) {
      toast.error('Please upload regulatory changes first');
      return;
    }
    
    try {
      setAnalyzing(true);
      toast.loading('Analyzing change impacts...', { id: 'analyze' });
      
      const response = await axios.post(`${API}/impact/analyze`, {
        deltas: deltasFile.deltas,
        top_k: 5
      });
      
      setResults(response.data);
      toast.success(
        `Found ${response.data.total_impacts_found} potential impacts`,
        { id: 'analyze' }
      );
      
      fetchRuns();
    } catch (error) {
      toast.error('Analysis failed', { id: 'analyze' });
      console.error(error);
    } finally {
      setAnalyzing(false);
    }
  };
  
  const downloadReport = async (runId, format = 'csv') => {
    try {
      const response = await axios.get(
        `${API}/impact/report/${runId}?format=${format}`,
        { responseType: format === 'csv' ? 'blob' : 'json' }
      );
      
      if (format === 'csv') {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `impact_report_${runId}.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        toast.success('Report downloaded');
      } else {
        console.log('JSON Report:', response.data);
        toast.success('Report loaded');
      }
    } catch (error) {
      toast.error('Failed to download report');
      console.error(error);
    }
  };
  
  const getConfidenceBadge = (confidence) => {
    if (confidence > 0.75) return <Badge className="bg-green-500">High: {(confidence * 100).toFixed(0)}%</Badge>;
    if (confidence > 0.60) return <Badge className="bg-yellow-500">Medium: {(confidence * 100).toFixed(0)}%</Badge>;
    return <Badge className="bg-gray-500">Low: {(confidence * 100).toFixed(0)}%</Badge>;
  };
  
  const groupByClause = (impacts) => {
    const grouped = {};
    impacts.forEach(impact => {
      if (!grouped[impact.clause_id]) {
        grouped[impact.clause_id] = [];
      }
      grouped[impact.clause_id].push(impact);
    });
    return grouped;
  };
  
  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Change Impact Detector</h1>
          <p className="text-muted-foreground mt-1">
            Identify which QSP sections are affected by regulatory changes
          </p>
        </div>
      </div>
      
      {/* Upload Section */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>1. Upload Regulatory Changes</CardTitle>
            <CardDescription>
              JSON file with clause_id, change_text, change_type
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <input
                type="file"
                id="deltas-upload"
                accept=".json"
                className="hidden"
                onChange={handleFileUpload}
              />
              <label
                htmlFor="deltas-upload"
                className="flex items-center justify-center gap-2 p-4 border-2 border-dashed rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors"
              >
                <Upload className="h-5 w-5" />
                <span>{deltasFile ? deltasFile.name : 'Choose JSON file'}</span>
              </label>
            </div>
            
            {deltasFile && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="font-medium">{deltasFile.deltas.length} changes loaded</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>2. Upload QSP Sections (Optional)</CardTitle>
            <CardDescription>
              JSON file with section_path, heading, text
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <input
                type="file"
                id="qsp-upload"
                accept=".json"
                className="hidden"
                onChange={handleQSPUpload}
              />
              <label
                htmlFor="qsp-upload"
                className="flex items-center justify-center gap-2 p-4 border-2 border-dashed rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors"
              >
                <FileText className="h-5 w-5" />
                <span>{qspSections.length > 0 ? `${qspSections.length} sections` : 'Choose JSON file'}</span>
              </label>
            </div>
            
            {qspSections.length > 0 && (
              <Button onClick={ingestQSP} className="w-full">
                Ingest QSP Sections
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Analyze Button */}
      <Card>
        <CardContent className="py-6">
          <Button
            onClick={runAnalysis}
            disabled={!deltasFile || analyzing}
            className="w-full h-12 text-lg"
          >
            {analyzing ? (
              <>
                <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                Analyzing...
              </>
            ) : (
              <>
                <TrendingUp className="h-5 w-5 mr-2" />
                Run Impact Analysis
              </>
            )}
          </Button>
        </CardContent>
      </Card>
      
      {/* Results */}
      {results && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Analysis Results</CardTitle>
                <CardDescription>
                  Run ID: {results.run_id} • {results.total_impacts_found} impacts found
                </CardDescription>
              </div>
              <Button
                variant="outline"
                onClick={() => downloadReport(results.run_id, 'csv')}
              >
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {Object.entries(groupByClause(results.impacts)).map(([clauseId, impacts]) => (
              <div key={clauseId} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-lg">Clause {clauseId}</h3>
                    <Badge variant="outline" className="mt-1">
                      {impacts[0].change_type}
                    </Badge>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {impacts.length} section{impacts.length > 1 ? 's' : ''} affected
                  </span>
                </div>
                
                <div className="space-y-2">
                  {impacts.map((impact, idx) => (
                    <div key={idx} className="pl-4 border-l-2 border-blue-200 py-2">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <AlertCircle className="h-4 w-4 text-blue-500" />
                            <span className="font-medium">
                              {impact.section_path}: {impact.heading}
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground mt-1 ml-6">
                            {impact.qsp_doc || 'QSP Document'}
                          </p>
                          <p className="text-sm mt-2 ml-6">
                            {impact.rationale}
                          </p>
                        </div>
                        <div className="ml-4">
                          {getConfidenceBadge(impact.confidence)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
      
      {/* Previous Runs */}
      {runs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Previous Analysis Runs</CardTitle>
            <CardDescription>{runs.length} recent runs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {runs.map((run) => (
                <div
                  key={run.run_id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div>
                    <div className="font-medium">{run.run_id.slice(0, 8)}...</div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(run.started_at).toLocaleString()} • {run.total_impacts} impacts
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => downloadReport(run.run_id, 'csv')}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ChangeImpactDetector;
