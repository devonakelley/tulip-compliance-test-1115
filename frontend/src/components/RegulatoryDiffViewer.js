import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Download, FileText, Search } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const RegulatoryDiffViewer = ({ diffData }) => {
  const [expandedClauses, setExpandedClauses] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [exportingPDF, setExportingPDF] = useState(false);
  const [exportingCSV, setExportingCSV] = useState(false);

  if (!diffData || !diffData.deltas || diffData.deltas.length === 0) {
    return (
      <Card className="bg-gray-50">
        <CardContent className="py-12 text-center">
          <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">No Diff Generated Yet</h3>
          <p className="text-gray-600">
            Upload two regulatory documents to generate your first diff.
          </p>
        </CardContent>
      </Card>
    );
  }

  const toggleClause = (clauseId) => {
    setExpandedClauses(prev => ({
      ...prev,
      [clauseId]: !prev[clauseId]
    }));
  };

  const expandAll = () => {
    const allExpanded = {};
    diffData.deltas.forEach(delta => {
      allExpanded[delta.clause_id] = true;
    });
    setExpandedClauses(allExpanded);
  };

  const collapseAll = () => {
    setExpandedClauses({});
  };

  const getChangeTypeColor = (changeType) => {
    switch (changeType?.toLowerCase()) {
      case 'added':
      case 'new':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'deleted':
      case 'removed':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'modified':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getChangeTypeBadge = (changeType) => {
    const colorClass = getChangeTypeColor(changeType);
    return (
      <Badge className={`${colorClass} font-semibold`}>
        {changeType?.toUpperCase() || 'UNKNOWN'}
      </Badge>
    );
  };

  const filteredDeltas = diffData.deltas.filter(delta => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      delta.clause_id?.toLowerCase().includes(searchLower) ||
      delta.title?.toLowerCase().includes(searchLower) ||
      delta.old_text?.toLowerCase().includes(searchLower) ||
      delta.new_text?.toLowerCase().includes(searchLower)
    );
  });

  const handleExportCSV = async () => {
    try {
      setExportingCSV(true);
      toast.loading('Generating CSV...', { id: 'csv-export' });

      // Create CSV content
      const headers = ['Clause ID', 'Title', 'Change Type', 'Old Text', 'New Text'];
      const rows = diffData.deltas.map(delta => [
        delta.clause_id || '',
        delta.title || '',
        delta.change_type || '',
        (delta.old_text || '').replace(/"/g, '""'),
        (delta.new_text || '').replace(/"/g, '""')
      ]);

      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().toISOString().slice(0, 10);
      link.setAttribute('download', `regulatory_diff_${timestamp}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('CSV exported successfully', { id: 'csv-export' });
    } catch (error) {
      console.error('Error exporting CSV:', error);
      toast.error('Failed to export CSV', { id: 'csv-export' });
    } finally {
      setExportingCSV(false);
    }
  };

  const handleExportPDF = async () => {
    try {
      setExportingPDF(true);
      toast.loading('Generating PDF...', { id: 'pdf-export' });

      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/regulatory/export_diff_pdf`,
        { diff_id: diffData.id },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          responseType: 'blob'
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().toISOString().slice(0, 10);
      link.setAttribute('download', `regulatory_diff_report_${timestamp}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('PDF exported successfully', { id: 'pdf-export' });
    } catch (error) {
      console.error('Error exporting PDF:', error);
      toast.error('Failed to export PDF. Please try again.', { id: 'pdf-export' });
    } finally {
      setExportingPDF(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Regulatory Diff Viewer</CardTitle>
              <p className="text-sm text-gray-600 mt-1">
                {filteredDeltas.length} clause(s) {searchTerm && `matching "${searchTerm}"`}
              </p>
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={expandAll}>
                Expand All
              </Button>
              <Button size="sm" variant="outline" onClick={collapseAll}>
                Collapse All
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleExportCSV}
                disabled={exportingCSV}
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
                size="sm"
                variant="outline"
                onClick={handleExportPDF}
                disabled={exportingPDF}
              >
                {exportingPDF ? (
                  <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                ) : (
                  <>
                    <FileText className="h-4 w-4 mr-1" />
                    PDF
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by clause number or text..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </CardContent>
      </Card>

      {/* Diff Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b-2">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold w-12"></th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Clause ID</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Title</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Change Type</th>
                </tr>
              </thead>
              <tbody>
                {filteredDeltas.map((delta, idx) => (
                  <React.Fragment key={idx}>
                    <tr
                      className="border-b hover:bg-gray-50 cursor-pointer"
                      onClick={() => toggleClause(delta.clause_id)}
                    >
                      <td className="px-4 py-3">
                        {expandedClauses[delta.clause_id] ? (
                          <ChevronUp className="h-5 w-5 text-gray-600" />
                        ) : (
                          <ChevronDown className="h-5 w-5 text-gray-600" />
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono font-bold text-blue-700">
                        {delta.clause_id}
                      </td>
                      <td className="px-4 py-3">{delta.title || 'N/A'}</td>
                      <td className="px-4 py-3">{getChangeTypeBadge(delta.change_type)}</td>
                    </tr>
                    {expandedClauses[delta.clause_id] && (
                      <tr className="bg-gray-50 border-b">
                        <td colSpan={4} className="p-4">
                          <div className="grid grid-cols-2 gap-4">
                            {/* Old Text */}
                            <div>
                              <div className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-2">
                                <span className="inline-block w-3 h-3 bg-red-500 rounded"></span>
                                OLD VERSION
                              </div>
                              <div className="bg-red-50 border-l-4 border-red-500 p-3 rounded text-sm text-gray-800 whitespace-pre-wrap">
                                {delta.old_text || 'N/A'}
                              </div>
                            </div>
                            {/* New Text */}
                            <div>
                              <div className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-2">
                                <span className="inline-block w-3 h-3 bg-green-500 rounded"></span>
                                NEW VERSION
                              </div>
                              <div className="bg-green-50 border-l-4 border-green-500 p-3 rounded text-sm text-gray-800 whitespace-pre-wrap">
                                {delta.new_text || 'N/A'}
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

      {filteredDeltas.length === 0 && searchTerm && (
        <Card className="bg-gray-50">
          <CardContent className="py-8 text-center">
            <Search className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-600">No clauses match your search: "{searchTerm}"</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default RegulatoryDiffViewer;
