import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, FileText, Trash2, CheckCircle, Eye, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

const API = process.env.REACT_APP_BACKEND_URL;

const QSPUploadSimplified = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [mapping, setMapping] = useState(false);
  const [qspDocuments, setQspDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [viewingClause, setViewingClause] = useState(null);
  const [mappingComplete, setMappingComplete] = useState(false);

  useEffect(() => {
    fetchQSPDocuments();
    // Check if mapping was previously completed
    const clauseMap = localStorage.getItem('clause_map');
    if (clauseMap) {
      setMappingComplete(true);
    }
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
        
        // Save mapping confirmation to localStorage
        localStorage.setItem('clause_map', JSON.stringify({
          success: true,
          total_qsp_documents: response.data.total_qsp_documents,
          total_clauses_mapped: response.data.total_clauses_mapped,
          timestamp: new Date().toISOString()
        }));
        
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

  const handleDeleteDocument = async (document) => {
    if (!window.confirm(`Delete "${document.filename}"? This will remove all its clauses.`)) {
      return;
    }

    try {
      toast.loading('Deleting document...', { id: 'delete-doc' });
      
      const response = await axios.delete(
        `${API}/api/regulatory/delete/qsp/${encodeURIComponent(document.filename)}`,
        { headers: getAuthHeaders() }
      );

      if (response.data && response.data.success) {
        toast.success('Document deleted successfully', { id: 'delete-doc' });
        fetchQSPDocuments();
        setMappingComplete(false);
        localStorage.removeItem('clause_map');
      }
    } catch (error) {
      console.error('Error deleting document:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to delete document';
      toast.error(errorMsg, { id: 'delete-doc' });
    }
  };

  // Flatten clauses from all documents for table display
  const getAllClauses = () => {
    const allClauses = [];
    qspDocuments.forEach(doc => {
      if (doc.clauses && Array.isArray(doc.clauses)) {
        doc.clauses.forEach(clause => {
          allClauses.push({
            ...clause,
            filename: doc.filename,
            document_number: doc.document_number,
            revision: doc.revision
          });
        });
      }
    });
    return allClauses;
  };

  const allClauses = getAllClauses();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Internal Docs (QSPs)</h2>
        <p className="text-gray-600 mt-1">
          Upload Quality System Procedure documents for clause mapping
        </p>
      </div>

      {/* Single File Uploader */}
      <Card>
        <CardHeader>
          <CardTitle>Upload QSP Documents</CardTitle>
          <CardDescription>
            Supported formats: .docx, .pdf, .txt • Expecting 5-15 clauses per document
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
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
              className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer transition-colors"
            >
              <Upload className="h-5 w-5 mr-2" />
              Select Files
            </label>
            <p className="mt-2 text-sm text-gray-500">
              Multiple files allowed
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
                    Uploading & Parsing...
                  </>
                ) : (
                  'Upload & Parse Files'
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Clause Table */}
      {allClauses.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Parsed QSP Clauses</CardTitle>
            <CardDescription>
              {allClauses.length} clause(s) from {qspDocuments.length} document(s)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b-2 bg-gray-50">
                    <th className="px-4 py-3 text-left font-semibold">Document</th>
                    <th className="px-4 py-3 text-left font-semibold">Revision</th>
                    <th className="px-4 py-3 text-left font-semibold">Clause</th>
                    <th className="px-4 py-3 text-left font-semibold">Title</th>
                    <th className="px-4 py-3 text-left font-semibold">Characters</th>
                    <th className="px-4 py-3 text-left font-semibold">View Text</th>
                  </tr>
                </thead>
                <tbody>
                  {allClauses.map((clause, idx) => (
                    <tr key={idx} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-sm font-bold text-blue-900">
                        {clause.document_number}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-500">
                        {clause.revision}
                      </td>
                      <td className="px-4 py-3 font-mono font-bold text-blue-700">
                        {clause.clause_number}
                      </td>
                      <td className="px-4 py-3">{clause.title}</td>
                      <td className="px-4 py-3 text-gray-600">{clause.characters}</td>
                      <td className="px-4 py-3">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleViewText(clause)}
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </Button>
                      </td>
                    </tr>
                  ))}
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
                <div>
                  <div className="font-semibold">✅ Clause mapping complete!</div>
                  <div className="text-sm">QSP clauses are ready for gap analysis in Tab 3</div>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-start gap-2 text-sm text-blue-900">
                  <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                  <p>
                    <strong>Next Step:</strong> Generate clause map to prepare for gap analysis.
                  </p>
                </div>
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
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {loadingDocs && (
        <Card>
          <CardContent className="py-8 text-center">
            <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-3"></div>
            <p className="text-gray-600">Loading QSP documents...</p>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!loadingDocs && qspDocuments.length === 0 && (
        <Card className="bg-gray-50">
          <CardContent className="py-8 text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400 mb-3" />
            <p className="text-gray-600">No QSP documents uploaded yet</p>
            <p className="text-sm text-gray-500 mt-1">Upload your first QSP document to get started</p>
          </CardContent>
        </Card>
      )}

      {/* Text Viewing Modal */}
      {viewingClause && (
        <Dialog open={!!viewingClause} onOpenChange={() => setViewingClause(null)}>
          <DialogContent className="max-w-3xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-600" />
                {viewingClause.document_number} - Clause {viewingClause.clause}: {viewingClause.title}
              </DialogTitle>
            </DialogHeader>
            <div className="overflow-auto max-h-[60vh] mt-4">
              <div className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded border">
                {viewingClause.text || 'No text available'}
              </div>
              <div className="mt-4 text-xs text-gray-500 flex justify-between">
                <span>Clause: <strong>{viewingClause.clause}</strong></span>
                <span>Characters: <strong>{viewingClause.characters || 0}</strong></span>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default QSPUploadSimplified;
