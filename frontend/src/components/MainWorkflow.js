import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { GitCompare, Upload, TrendingUp } from 'lucide-react';
import RegulatoryDashboard from './RegulatoryDashboard';
import QSPUploadSimplified from './QSPUploadSimplified';
import GapAnalysisSimplified from './GapAnalysisSimplified';

const MainWorkflow = () => {
  const [activeTab, setActiveTab] = useState('diff');

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Tulip Compliance Workflow</h1>
          <p className="text-lg text-gray-600 mt-2">
            Three-step regulatory compliance management system
          </p>
        </div>

        {/* Tabbed Interface */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 h-auto">
            <TabsTrigger 
              value="diff" 
              className="flex items-center gap-2 py-4 text-base data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <GitCompare className="h-5 w-5" />
              <div className="text-left">
                <div className="font-semibold">1. Regulatory Diff Checker</div>
                <div className="text-xs opacity-80">Compare old vs new standards</div>
              </div>
            </TabsTrigger>
            <TabsTrigger 
              value="qsp" 
              className="flex items-center gap-2 py-4 text-base data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <Upload className="h-5 w-5" />
              <div className="text-left">
                <div className="font-semibold">2. Internal Docs (QSPs)</div>
                <div className="text-xs opacity-80">Upload & map clauses</div>
              </div>
            </TabsTrigger>
            <TabsTrigger 
              value="analysis" 
              className="flex items-center gap-2 py-4 text-base data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <TrendingUp className="h-5 w-5" />
              <div className="text-left">
                <div className="font-semibold">3. Gap Analysis</div>
                <div className="text-xs opacity-80">Run & export results</div>
              </div>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="diff" className="mt-6">
            <RegulatoryDashboard />
          </TabsContent>

          <TabsContent value="qsp" className="mt-6">
            <QSPUploadClean />
          </TabsContent>

          <TabsContent value="analysis" className="mt-6">
            <GapAnalysisEnhanced />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default MainWorkflow;
