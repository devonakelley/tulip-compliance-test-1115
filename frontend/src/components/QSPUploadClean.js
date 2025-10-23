import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, FileText, CheckCircle, Eye, Trash2, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

const API = process.env.REACT_APP_BACKEND_URL;

const QSPUploadClean = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [mapping, setMapping] = useState(false);
  const [qspDocuments, setQspDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [viewingClause, setViewingClause] = useState(null);
  const [mappingComplete, setMappingComplete] = useState(false);

  useEffect(() => {
    fetchQSPDocuments();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  };

  const fetchQSPDocuments = async () => {
    try {
      setLoadingDocs(true);
      const response = await axios.get(`${API}/api/regulatory/list/qsp`, {
        headers: getAuthHeaders()
      });
      
      if (response.data && response.data.success) {
        setQspDocuments(response.data.documents || []);
      }
    } catch (error) {
      console.error('Error fetching QSP documents:', error);
      if (error.response?.status === 401) {
        toast.error('Please login to access QSP documents');
      }
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleFileSelect = (event) => {
    const selectedFiles = Array.from(event.target.files);
    
    // Validate file types
    const validFiles = selectedFiles.filter(file => {
      const ext = file.name.toLowerCase().split('.').pop();
      return ['docx', 'pdf', 'txt'].includes(ext);
    });
    
    if (validFiles.length !== selectedFiles.length) {
      toast.error('Only DOCX, PDF, and TXT files are supported');
    }
    
    setFiles(validFiles);
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error('Please select files to upload');
      return;
    }

    setUploading(true);
    let successCount = 0;
    let failCount = 0;

    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(
          `${API}/api/regulatory/upload/qsp`, 
          formData,
          {
            headers: {
              ...getAuthHeaders(),
              'Content-Type': 'multipart/form-data'
            }
          }
        );
        
        if (response.data && response.data.success) {
          successCount++;
          toast.success(`✅ ${file.name}: Parsed ${response.data.total_clauses} clauses`);
        }
      } catch (error) {
        failCount++;
        console.error(`Error uploading ${file.name}:`, error);
        const errorMsg = error.response?.data?.detail || 'Upload failed';
        toast.error(`❌ ${file.name}: ${errorMsg}`);
      }
    }

    setUploading(false);
    
    if (successCount > 0) {
      setFiles([]);
      fetchQSPDocuments();
      toast.success(`Successfully uploaded ${successCount} document(s)`);
    }
    
    if (failCount > 0) {
      toast.error(`Failed to upload ${failCount} document(s)`);
    }
  };

  const handleGenerateClauseMap = async () => {
    if (qspDocuments.length === 0) {
      toast.error('Please upload QSP documents first');
      return;
    }

    try {
      setMapping(true);
      toast.loading('Generating clause map...', { id: 'mapping' });

      const response = await axios.post(
        `${API}/api/regulatory/map_clauses`,
        {},
        { headers: getAuthHeaders() }
      );

      if (response.data && response.data.success) {
        setMappingComplete(true);
        toast.success(
          `✅ Mapped ${response.data.total_clauses_mapped} clauses from ${response.data.total_qsp_documents} documents`,
          { id: 'mapping' }
        );
      }
    } catch (error) {
      console.error('Error generating clause map:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to generate clause map';
      toast.error(errorMsg, { id: 'mapping' });
    } finally {
      setMapping(false);
    }
  };

  const handleViewText = (clause) => {
    setViewingClause(clause);
  };

  const handleDeleteQSP = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this QSP document?')) {
      return;
    }

    try {
      await axios.delete(`${API}/api/documents/${docId}`);
      toast.success('Document deleted successfully');
      fetchQSPDocuments();
    } catch (error) {
      console.error('Error deleting document:', error);
      toast.error('Failed to delete document');
    }
  };

  const handleDeleteAllQSPs = async () => {
    if (!window.confirm(`Are you sure you want to delete ALL ${qspDocuments.length} QSP documents? This action cannot be undone.`)) {
      return;
    }

    try {
      await axios.delete(`${API}/api/documents/all`);
      toast.success('All QSP documents deleted successfully');
      setParsedQSPs([]);
      setMappingComplete(false);
      fetchQSPDocuments();
    } catch (error) {
      console.error('Error deleting all documents:', error);
      toast.error('Failed to delete all documents');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Internal Docs (QSPs)</h2>
        <p className="text-gray-600 mt-1">
          Upload Quality System Procedure documents for clause mapping
        </p>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Upload QSP Documents</CardTitle>
          <CardDescription>
            Upload .docx or .pdf files containing your internal procedures
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-3" />
            <input
              type="file"
              id="qsp-files"
              accept=".docx,.txt,.pdf"
              multiple
              className="hidden"
              onChange={handleFileSelect}
            />
            <label
              htmlFor="qsp-files"
              className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
            >
              <Upload className="h-5 w-5 mr-2" />
              Select QSP Files
            </label>
            <p className="mt-2 text-sm text-gray-500">
              Supports .docx, .txt, and .pdf files • Multiple files allowed
            </p>
          </div>

          {files.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">{files.length} file(s) selected:</p>
              {files.map((file, idx) => (
                <div key={idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                  <FileText className="h-4 w-4 text-blue-600" />
                  <span className="text-sm flex-1">{file.name}</span>
                  <span className="text-xs text-gray-500">
                    {(file.size / 1024).toFixed(2)} KB
                  </span>
                </div>
              ))}
              <Button
                onClick={handleUpload}
                disabled={uploading}
                className="w-full mt-3"
              >
                {uploading ? (
                  <>
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    Uploading...
                  </>
                ) : (
                  'Upload Files'
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Parsed QSP Structure Table */}
      {parsedQSPs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Parsed QSP Structure</CardTitle>
            <CardDescription>
              Review extracted clauses from uploaded documents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="px-4 py-3 text-left font-semibold">Document</th>
                    <th className="px-4 py-3 text-left font-semibold">Clause</th>
                    <th className="px-4 py-3 text-left font-semibold">Title</th>
                    <th className="px-4 py-3 text-left font-semibold">Characters</th>
                    <th className="px-4 py-3 text-left font-semibold">View Text</th>
                  </tr>
                </thead>
                <tbody>
                  {parsedQSPs.map((doc, docIdx) =>
                    doc.clauses.map((clause, clauseIdx) => (
                      <tr key={`${docIdx}-${clauseIdx}`} className="border-b hover:bg-gray-50">
                        <td className="px-4 py-3 font-mono text-sm">
                          {doc.document_number}
                        </td>
                        <td className="px-4 py-3 font-mono font-bold text-blue-700">
                          {clause.clause_number}
                        </td>
                        <td className="px-4 py-3">{clause.title}</td>
                        <td className="px-4 py-3 text-gray-600">{clause.char_count}</td>
                        <td className="px-4 py-3">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setViewingText(clause.text)}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            View
                          </Button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Generate Clause Map Button */}
      {qspDocuments.length > 0 && (
        <Card className={mappingComplete ? "bg-green-50 border-green-200" : "bg-blue-50 border-blue-200"}>
          <CardContent className="pt-6">
            {mappingComplete ? (
              <div className="flex items-center gap-3 text-green-900">
                <CheckCircle className="h-6 w-6" />
                <span className="font-semibold">Clause map generated and ready for gap analysis</span>
              </div>
            ) : (
              <Button
                onClick={handleGenerateClauseMap}
                disabled={mapping}
                size="lg"
                className="w-full h-14 text-lg"
              >
                {mapping ? (
                  <>
                    <div className="animate-spin h-6 w-6 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    Generating Clause Map...
                  </>
                ) : (
                  'Generate Clause Map'
                )}
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Uploaded QSP Documents */}
      {qspDocuments.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Uploaded QSP Documents</CardTitle>
                <CardDescription>
                  {qspDocuments.length} document(s) in system
                </CardDescription>
              </div>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDeleteAllQSPs}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Delete All ({qspDocuments.length})
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {qspDocuments.map((doc, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-blue-600" />
                    <span className="font-medium text-sm">{doc.filename || doc.doc_name}</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeleteQSP(doc.doc_id || doc._id)}
                    className="text-red-600"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Text Viewing Modal */}
      {viewingText && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setViewingText(null)}>
          <div className="bg-white rounded-lg p-6 max-w-2xl max-h-[80vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">Clause Text</h3>
              <Button size="sm" variant="outline" onClick={() => setViewingText(null)}>Close</Button>
            </div>
            <div className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-gray-50 p-4 rounded">
              {viewingText}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QSPUploadClean;
