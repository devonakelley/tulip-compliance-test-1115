import React, { useState } from 'react';
import {
  FileText,
  ClipboardList,
  BookOpen,
  FileCheck,
  FolderArchive,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  Info
} from 'lucide-react';
import { Badge } from './ui/badge';

/**
 * Full 5-Level Document Hierarchy Trace Component
 *
 * Displays impact analysis through all levels:
 * - Level 1: Quality Manual (QM)
 * - Level 2: Quality System Procedures (QSP)
 * - Level 3: Work Instructions (WI)
 * - Level 4: Forms
 * - Level 5: Reference Documents (RFD)
 */
export function HierarchyTrace({ hierarchyTrace, reasoning, totalDocumentsAffected }) {
  const [expandedLevels, setExpandedLevels] = useState({
    level_1: true,
    level_2: true,
    level_3: true,
    level_4: false,
    level_5: false
  });

  if (!hierarchyTrace) return null;

  const {
    level_1_quality_manual = [],
    level_2_qsp = [],
    level_3_work_instructions = [],
    level_4_forms = [],
    level_5_reference_docs = []
  } = hierarchyTrace;

  const totalCount =
    level_1_quality_manual.length +
    level_2_qsp.length +
    level_3_work_instructions.length +
    level_4_forms.length +
    level_5_reference_docs.length;

  if (totalCount === 0) {
    return (
      <div className="text-sm text-gray-500 italic mt-2 p-3 bg-gray-50 rounded-lg">
        No document hierarchy trace available. Run seed_document_hierarchy.py to initialize.
      </div>
    );
  }

  const toggleLevel = (level) => {
    setExpandedLevels(prev => ({
      ...prev,
      [level]: !prev[level]
    }));
  };

  const LevelSection = ({
    levelKey,
    title,
    icon: Icon,
    iconColor,
    docs,
    reasoningKey,
    badgeColor
  }) => {
    const isExpanded = expandedLevels[levelKey];
    const levelReasoning = reasoning?.[reasoningKey] || '';

    if (docs.length === 0 && !levelReasoning) return null;

    return (
      <div className="border-l-2 border-gray-200 pl-4 ml-2">
        <button
          onClick={() => toggleLevel(levelKey)}
          className="flex items-center gap-2 w-full text-left py-2 hover:bg-gray-50 rounded transition-colors"
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-400" />
          )}
          <Icon className={`h-5 w-5 ${iconColor}`} />
          <span className="font-semibold text-sm">{title}</span>
          <Badge variant="secondary" className={`ml-2 ${badgeColor}`}>
            {docs.length}
          </Badge>
        </button>

        {isExpanded && (
          <div className="ml-6 pb-3">
            {/* Reasoning explanation */}
            {levelReasoning && (
              <div className="flex items-start gap-2 mb-3 p-2 bg-blue-50 rounded text-sm">
                <Info className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                <p className="text-blue-700">{levelReasoning}</p>
              </div>
            )}

            {/* Document list */}
            {docs.length > 0 ? (
              <ul className="space-y-2">
                {docs.map((doc, idx) => (
                  <li key={idx} className="flex items-start gap-2 p-2 bg-white border rounded-lg shadow-sm">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-xs">
                          {doc.id}
                        </Badge>
                        <span className="font-medium text-sm">{doc.name}</span>
                      </div>
                      {doc.reason && (
                        <p className="text-xs text-gray-500 mt-1">{doc.reason}</p>
                      )}
                      {doc.impact_type && (
                        <Badge
                          variant="outline"
                          className={`mt-1 text-xs ${
                            doc.impact_type === 'direct'
                              ? 'bg-red-50 text-red-700 border-red-200'
                              : doc.impact_type === 'upstream'
                              ? 'bg-purple-50 text-purple-700 border-purple-200'
                              : 'bg-orange-50 text-orange-700 border-orange-200'
                          }`}
                        >
                          {doc.impact_type === 'direct' ? 'Direct Impact' :
                           doc.impact_type === 'upstream' ? 'Upstream' : 'Downstream'}
                        </Badge>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500 italic">No documents at this level</p>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="mt-4 border rounded-lg p-4 bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-lg flex items-center gap-2">
          <FolderArchive className="h-5 w-5 text-indigo-600" />
          Document Hierarchy Trace
        </h3>
        <Badge variant="secondary" className="bg-indigo-100 text-indigo-700">
          {totalDocumentsAffected || totalCount} Documents Affected
        </Badge>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mb-4 text-xs">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-red-100 border border-red-300"></span>
          Direct Impact
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-purple-100 border border-purple-300"></span>
          Upstream (Parent)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-orange-100 border border-orange-300"></span>
          Downstream (Child)
        </span>
      </div>

      {/* Hierarchy Levels */}
      <div className="space-y-1">
        <LevelSection
          levelKey="level_1"
          title="Level 1: Quality Manual"
          icon={BookOpen}
          iconColor="text-purple-600"
          docs={level_1_quality_manual}
          reasoningKey="level_1_quality_manual"
          badgeColor="bg-purple-100 text-purple-700"
        />

        <LevelSection
          levelKey="level_2"
          title="Level 2: QSPs"
          icon={FileCheck}
          iconColor="text-blue-600"
          docs={level_2_qsp}
          reasoningKey="level_2_qsp"
          badgeColor="bg-blue-100 text-blue-700"
        />

        <LevelSection
          levelKey="level_3"
          title="Level 3: Work Instructions"
          icon={ClipboardList}
          iconColor="text-green-600"
          docs={level_3_work_instructions}
          reasoningKey="level_3_work_instructions"
          badgeColor="bg-green-100 text-green-700"
        />

        <LevelSection
          levelKey="level_4"
          title="Level 4: Forms"
          icon={FileText}
          iconColor="text-amber-600"
          docs={level_4_forms}
          reasoningKey="level_4_forms"
          badgeColor="bg-amber-100 text-amber-700"
        />

        <LevelSection
          levelKey="level_5"
          title="Level 5: Reference Documents"
          icon={FolderArchive}
          iconColor="text-gray-600"
          docs={level_5_reference_docs}
          reasoningKey="level_5_reference_docs"
          badgeColor="bg-gray-200 text-gray-700"
        />
      </div>

      {/* Summary Footer */}
      <div className="mt-4 pt-3 border-t flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 text-gray-600">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <span>Review all affected documents for compliance</span>
        </div>
        <button
          className="text-indigo-600 hover:text-indigo-800 font-medium"
          onClick={() => setExpandedLevels({
            level_1: true,
            level_2: true,
            level_3: true,
            level_4: true,
            level_5: true
          })}
        >
          Expand All
        </button>
      </div>
    </div>
  );
}

/**
 * Compact version for inline display
 */
export function HierarchyTraceSummary({ hierarchyTrace, totalDocumentsAffected }) {
  if (!hierarchyTrace) return null;

  const {
    level_1_quality_manual = [],
    level_2_qsp = [],
    level_3_work_instructions = [],
    level_4_forms = [],
    level_5_reference_docs = []
  } = hierarchyTrace;

  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {level_1_quality_manual.length > 0 && (
        <Badge variant="outline" className="bg-purple-50">
          <BookOpen className="h-3 w-3 mr-1" />
          {level_1_quality_manual.length} QM
        </Badge>
      )}
      {level_2_qsp.length > 0 && (
        <Badge variant="outline" className="bg-blue-50">
          <FileCheck className="h-3 w-3 mr-1" />
          {level_2_qsp.length} QSP
        </Badge>
      )}
      {level_3_work_instructions.length > 0 && (
        <Badge variant="outline" className="bg-green-50">
          <ClipboardList className="h-3 w-3 mr-1" />
          {level_3_work_instructions.length} WI
        </Badge>
      )}
      {level_4_forms.length > 0 && (
        <Badge variant="outline" className="bg-amber-50">
          <FileText className="h-3 w-3 mr-1" />
          {level_4_forms.length} Forms
        </Badge>
      )}
      {level_5_reference_docs.length > 0 && (
        <Badge variant="outline" className="bg-gray-100">
          <FolderArchive className="h-3 w-3 mr-1" />
          {level_5_reference_docs.length} Refs
        </Badge>
      )}
      {totalDocumentsAffected > 0 && (
        <Badge className="bg-indigo-600 text-white">
          Total: {totalDocumentsAffected}
        </Badge>
      )}
    </div>
  );
}

export default HierarchyTrace;
