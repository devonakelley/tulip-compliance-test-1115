import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const QSPUpload = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [mapping, setMapping] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [mappingResults, setMappingResults] = useState(null);
  const [qspDocuments, setQspDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const handleFileSelect = (event) => {
    const selectedFiles = Array.from(event.target.files);
    setFiles(selectedFiles);
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error('Please select files to upload');
      return;
    }

    setUploading(true);
    let successCount = 0;

    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        await axios.post(`${API}/api/documents/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        successCount++;
        setUploadedDocs(prev => [...prev, file.name]);
      } catch (error) {
        console.error(`Error uploading ${file.name}:`, error);
        toast.error(`Failed to upload ${file.name}`);
      }
    }

    setUploading(false);
    
    if (successCount > 0) {
      toast.success(`Successfully uploaded ${successCount} document(s)`);
      setFiles([]);
    }
  };

  const handleGenerateClauseMap = async () => {
    if (uploadedDocs.length === 0) {
      toast.error('Please upload QSP documents first');
      return;
    }

    try {
      setMapping(true);
      toast.loading('Generating clause map...', { id: 'mapping' });

      // Fetch uploaded documents to get their content
      const docsResponse = await axios.get(`${API}/api/documents`);
      const documents = docsResponse.data;

      if (!documents || documents.length === 0) {
        toast.error('No documents found to map', { id: 'mapping' });
        return;
      }

      // Prepare QSP sections for ingestion
      const qspSections = [];
      documents.forEach(doc => {
        if (doc.sections) {
          Object.entries(doc.sections).forEach(([sectionPath, content]) => {
            qspSections.push({
              section_path: sectionPath,
              heading: `Section ${sectionPath}`,
              text: typeof content === 'string' ? content : JSON.stringify(content),
              source: doc.filename
            });
          });
        }
      });

      // Call ingest endpoint
      const response = await axios.post(`${API}/api/impact/ingest_qsp`, {
        doc_name: 'Consolidated QSP',
        sections: qspSections
      });

      if (response.data.success) {
        setMappingResults(response.data);
        
        // Save clause map to localStorage for Gap Analysis tab
        localStorage.setItem('clause_map', JSON.stringify(response.data));
        
        toast.success(
          `✅ Clause map created for ${documents.length} documents (${response.data.sections_count} clauses)`,
          { id: 'mapping' }
        );
      }
    } catch (error) {
      console.error('Error generating clause map:', error);
      toast.error('Failed to generate clause map', { id: 'mapping' });
    } finally {
      setMapping(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Internal Document Upload (QSPs)</h2>
        <p className="text-gray-600 mt-1">
          Upload your Quality System Procedure documents for clause mapping
        </p>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Upload QSP Documents</CardTitle>
          <CardDescription>
            Select multiple .docx or .txt files containing your internal procedures
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

      {/* Uploaded Documents */}
      {uploadedDocs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              Uploaded Documents ({uploadedDocs.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {uploadedDocs.map((name, idx) => (
                <div key={idx} className="flex items-center gap-2 p-2 bg-green-50 rounded-lg">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="text-sm">{name}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Generate Clause Map Button */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <Button
            onClick={handleGenerateClauseMap}
            disabled={uploadedDocs.length === 0 || mapping}
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
        </CardContent>
      </Card>

      {/* Mapping Results */}
      {mappingResults && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-900">
              <CheckCircle className="h-5 w-5" />
              Clause Mapping Complete
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-green-900">
              <p className="text-lg font-semibold">
                Successfully mapped {mappingResults.sections_count} QSP clauses
              </p>
              <p className="text-sm">
                Document ID: {mappingResults.doc_id}
              </p>
              <p className="text-sm text-green-700">
                Your internal documents are now ready for gap analysis
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default QSPUpload;
