import React from 'react';
import { FileText, ClipboardList } from 'lucide-react';
import { Badge } from './ui/badge';

export function DownstreamImpacts({ impacts }) {
  if (!impacts) return null;
  
  const { forms = [], work_instructions = [] } = impacts;
  
  if (forms.length === 0 && work_instructions.length === 0) {
    return (
      <div className="text-sm text-gray-500 italic mt-2">
        No downstream impacts detected
      </div>
    );
  }
  
  return (
    <div className="mt-4 space-y-3 border-t pt-3">
      {forms.length > 0 && (
        <div className="downstream-section">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="h-4 w-4 text-blue-600" />
            <h4 className="font-semibold text-sm">
              📄 Forms Affected ({forms.length})
            </h4>
          </div>
          <ul className="space-y-1 ml-6">
            {forms.map((form, idx) => (
              <li key={idx} className="text-sm flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-xs">
                  {form.id}
                </Badge>
                <span>{form.name}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {work_instructions.length > 0 && (
        <div className="downstream-section">
          <div className="flex items-center gap-2 mb-2">
            <ClipboardList className="h-4 w-4 text-green-600" />
            <h4 className="font-semibold text-sm">
              📋 Work Instructions Affected ({work_instructions.length})
            </h4>
          </div>
          <ul className="space-y-1 ml-6">
            {work_instructions.map((wi, idx) => (
              <li key={idx} className="text-sm flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-xs">
                  {wi.id}
                </Badge>
                <span>{wi.name}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
