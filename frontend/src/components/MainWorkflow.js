import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { GitCompare, Upload, TrendingUp, CheckCircle2, Circle } from 'lucide-react';
import RegulatoryDashboard from './RegulatoryDashboard';
import QSPUploadSimplified from './QSPUploadSimplified';
import GapAnalysisSimplified from './GapAnalysisSimplified';

const MainWorkflow = () => {
  const [activeTab, setActiveTab] = useState('diff');

  // Check completion status from localStorage
  const hasDiff = !!localStorage.getItem('regulatory_diff');
  const hasClauseMap = !!localStorage.getItem('clause_map');

  const getStepStatus = (step) => {
    if (step === 1) return hasDiff;
    if (step === 2) return hasClauseMap;
    return false;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900 bg-clip-text text-transparent">
            Regulatory Compliance Workflow
          </h1>
          <p className="text-lg text-slate-600 mt-3 max-w-2xl mx-auto">
            Analyze regulatory changes, map your QSP documents, and identify compliance gaps
          </p>
          {/* Progress indicator */}
          <div className="flex items-center justify-center gap-4 mt-6">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${hasDiff ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
              {hasDiff ? <CheckCircle2 className="h-4 w-4" /> : <Circle className="h-4 w-4" />}
              Diff Ready
            </div>
            <div className="w-8 h-0.5 bg-slate-200" />
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${hasClauseMap ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
              {hasClauseMap ? <CheckCircle2 className="h-4 w-4" /> : <Circle className="h-4 w-4" />}
              Clauses Mapped
            </div>
            <div className="w-8 h-0.5 bg-slate-200" />
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${hasDiff && hasClauseMap ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-500'}`}>
              <TrendingUp className="h-4 w-4" />
              Ready for Analysis
            </div>
          </div>
        </div>

        {/* Tabbed Interface */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 h-auto bg-white shadow-sm border rounded-xl p-1">
            <TabsTrigger
              value="diff"
              className="flex items-center gap-3 py-4 px-4 text-base rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-md transition-all"
            >
              <div className={`flex items-center justify-center w-8 h-8 rounded-full ${getStepStatus(1) ? 'bg-emerald-500' : 'bg-blue-100'} ${activeTab === 'diff' ? 'bg-white/20' : ''}`}>
                {getStepStatus(1) ? <CheckCircle2 className="h-5 w-5 text-white" /> : <GitCompare className={`h-5 w-5 ${activeTab === 'diff' ? 'text-white' : 'text-blue-600'}`} />}
              </div>
              <div className="text-left">
                <div className="font-semibold">1. Regulatory Diff</div>
                <div className="text-xs opacity-75">Compare standards</div>
              </div>
            </TabsTrigger>
            <TabsTrigger
              value="qsp"
              className="flex items-center gap-3 py-4 px-4 text-base rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-md transition-all"
            >
              <div className={`flex items-center justify-center w-8 h-8 rounded-full ${getStepStatus(2) ? 'bg-emerald-500' : 'bg-blue-100'} ${activeTab === 'qsp' ? 'bg-white/20' : ''}`}>
                {getStepStatus(2) ? <CheckCircle2 className="h-5 w-5 text-white" /> : <Upload className={`h-5 w-5 ${activeTab === 'qsp' ? 'text-white' : 'text-blue-600'}`} />}
              </div>
              <div className="text-left">
                <div className="font-semibold">2. QSP Documents</div>
                <div className="text-xs opacity-75">Upload & map</div>
              </div>
            </TabsTrigger>
            <TabsTrigger
              value="analysis"
              className="flex items-center gap-3 py-4 px-4 text-base rounded-lg data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-blue-700 data-[state=active]:text-white data-[state=active]:shadow-md transition-all"
            >
              <div className={`flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 ${activeTab === 'analysis' ? 'bg-white/20' : ''}`}>
                <TrendingUp className={`h-5 w-5 ${activeTab === 'analysis' ? 'text-white' : 'text-blue-600'}`} />
              </div>
              <div className="text-left">
                <div className="font-semibold">3. Gap Analysis</div>
                <div className="text-xs opacity-75">Identify gaps</div>
              </div>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="diff" className="mt-6">
            <RegulatoryDashboard />
          </TabsContent>

          <TabsContent value="qsp" className="mt-6">
            <QSPUploadSimplified />
          </TabsContent>

          <TabsContent value="analysis" className="mt-6">
            <GapAnalysisSimplified />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default MainWorkflow;
