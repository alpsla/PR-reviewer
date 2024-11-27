import React, { useState } from 'react';
import { ChevronDown, AlertCircle, CheckCircle, TrendingUp, TrendingDown, Download, Clipboard, FileText, GitPullRequest, ArrowRight } from 'lucide-react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

interface MetricProps {
  label: string;
  value: number;
  trend: number;
  chartData?: number[];
}

interface TypeSystemMetrics {
  interfaces: number;
  genericTypes: number;
  mappedTypes: number;
  utilityTypes: number;
  brandedTypes: number;
  typePredicates: number;
  typeGuards: number;
  typeAssertions: number;
}

interface DocumentationMetrics {
  overall: number;
  jsdoc: number;
  parameters: number;
  returnTypes: number;
  typeDefinitions: number;
  interfaces: number;
  completeness: number;
  clarity: number;
  examples: number;
}

interface FileAnalysis {
  name: string;
  score: number;
  strengths: string[];
  issues: string[];
  metrics: {
    typeGuards: number;
    typeAliases: number;
    interfaces: number;
  };
}

const MetricCard: React.FC<MetricProps> = ({ label, value, trend, chartData = [] }) => (
  <div className="bg-slate-800 p-4 rounded-lg">
    <div className="flex justify-between items-center">
      <h3 className="text-white">{label}</h3>
      <div className="flex items-center">
        {trend > 0 ? (
          <TrendingUp className="w-4 h-4 text-green-500 mr-2" />
        ) : (
          <TrendingDown className="w-4 h-4 text-red-500 mr-2" />
        )}
        <span className={trend > 0 ? "text-green-500" : "text-red-500"}>
          {trend > 0 ? "+" : ""}{trend}%
        </span>
      </div>
    </div>
    <div className="mt-2 flex items-end justify-between">
      <span className="text-2xl font-bold text-green-500">{value}%</span>
      <div className="h-16 w-24 flex items-end space-x-1">
        {chartData.map((dataPoint, index) => (
          <div 
            key={index} 
            className="w-2 bg-slate-700 relative flex-1"
            style={{ height: '48px' }}
          >
            <div 
              className="w-full bg-green-500 absolute bottom-0 transition-all duration-300 ease-in-out"
              style={{ height: `${dataPoint}%` }}
            ></div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

const TypeDistributionBar: React.FC<{ label: string; count: number; total: number }> = 
  ({ label, count, total }) => {
    const percentage = (count / total) * 100;
    return (
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-slate-300">{label}</span>
          <span className="text-slate-400">{count} ({percentage.toFixed(1)}%)</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2">
          <div 
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
      </div>
    );
  };

const FileAnalysisCard: React.FC<{ file: FileAnalysis }> = ({ file }) => (
  <div className="bg-slate-800 p-4 rounded-lg space-y-4">
    <div className="flex items-center justify-between">
      <h3 className="text-lg font-semibold text-white">{file.name}</h3>
      <span className={`text-${file.score >= 90 ? 'green' : 'yellow'}-500`}>
        {file.score}%
      </span>
    </div>
    <div className="space-y-2">
      <div>
        <h4 className="text-green-500 mb-2">Strengths:</h4>
        <ul className="space-y-1">
          {file.strengths.map((strength, index) => (
            <li key={index} className="text-slate-300 flex items-center">
              <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
              {strength}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h4 className="text-yellow-500 mb-2">Issues:</h4>
        <ul className="space-y-1">
          {file.issues.map((issue, index) => (
            <li key={index} className="text-slate-300 flex items-center">
              <AlertCircle className="w-4 h-4 text-yellow-500 mr-2" />
              {issue}
            </li>
          ))}
        </ul>
      </div>
    </div>
  </div>
);

const ActionItems: React.FC<{ items: { priority: string; tasks: string[] }[] }> = ({ items }) => (
  <div className="space-y-4">
    {items.map((item, index) => (
      <div key={index} className="bg-slate-800 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-3">{item.priority}</h3>
        <ul className="space-y-2">
          {item.tasks.map((task, taskIndex) => (
            <li key={taskIndex} className="text-slate-300 flex items-center">
              <ArrowRight className="w-4 h-4 text-blue-500 mr-2" />
              {task}
            </li>
          ))}
        </ul>
      </div>
    ))}
  </div>
);

interface TypeScriptReportProps {
  data: any;
}

export const TypeScriptReport: React.FC<TypeScriptReportProps> = ({ data }) => {
  const [showExportMenu, setShowExportMenu] = useState(false);

  const copyToClipboard = async () => {
    try {
      const markdownText = generateMarkdownReport();
      await navigator.clipboard.writeText(markdownText);
      alert('Report copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      alert('Failed to copy to clipboard');
    }
  };

  const downloadMarkdown = () => {
    const markdownText = generateMarkdownReport();
    const blob = new Blob([markdownText], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'typescript_analysis.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadPDF = async () => {
    try {
      const element = document.getElementById('typescript-report');
      if (!element) return;

      const canvas = await html2canvas(element);
      const imgData = canvas.toDataURL('image/png');
      
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'px',
        format: 'a4'
      });
      
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = canvas.width;
      const imgHeight = canvas.height;
      const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
      
      pdf.addImage(imgData, 'PNG', 0, 0, imgWidth * ratio, imgHeight * ratio);
      pdf.save('typescript_analysis.pdf');
    } catch (err) {
      console.error('Failed to generate PDF:', err);
      alert('Failed to generate PDF');
    }
  };

  const generateMarkdownReport = () => {
    // Generate markdown representation of the analysis data
    let markdown = '# TypeScript Analysis Report\n\n';
    
    if (data.type_metrics) {
      markdown += '## Type Metrics\n\n';
      markdown += `- Type Coverage: ${data.type_metrics.type_coverage}%\n`;
      markdown += `- Explicit Types: ${data.type_metrics.explicit_types}\n`;
      // Add other type metrics...
    }
    
    if (data.doc_metrics) {
      markdown += '\n## Documentation Metrics\n\n';
      markdown += `- Documentation Coverage: ${data.doc_metrics.coverage}%\n`;
      // Add other doc metrics...
    }
    
    return markdown;
  };

  const reviewNewPR = () => {
    window.location.href = '/';
  };

  return (
    <div id="typescript-report" className="space-y-8 p-6">
      {/* Header with buttons */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">TypeScript Analysis Report</h1>
        <div className="flex space-x-4">
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-blue-700"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
            
            {showExportMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg z-50">
                <button
                  onClick={copyToClipboard}
                  className="w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-100 flex items-center space-x-2 rounded-t-lg"
                >
                  <Clipboard className="w-4 h-4" />
                  <span>Copy to Clipboard</span>
                </button>
                <button
                  onClick={downloadMarkdown}
                  className="w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                >
                  <FileText className="w-4 h-4" />
                  <span>Download Markdown</span>
                </button>
                <button
                  onClick={downloadPDF}
                  className="w-full px-4 py-2 text-left text-gray-700 hover:bg-gray-100 flex items-center space-x-2 rounded-b-lg"
                >
                  <Download className="w-4 h-4" />
                  <span>Download PDF</span>
                </button>
              </div>
            )}
          </div>
          
          <button
            onClick={reviewNewPR}
            className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-green-700"
          >
            <GitPullRequest className="w-4 h-4" />
            <span>Review New PR</span>
          </button>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="bg-slate-800 p-6 rounded-lg space-y-6">
        <h2 className="text-2xl font-bold text-white">Executive Summary</h2>
        <div className="grid grid-cols-4 gap-4">
          <MetricCard
            label="Overall Health"
            value={data.overallHealth}
            trend={data.trends.overall}
            chartData={data.historicalData.overall}
          />
          <MetricCard
            label="Type Safety"
            value={data.typeSafety}
            trend={data.trends.typeSafety}
            chartData={data.historicalData.typeSafety}
          />
          <MetricCard
            label="Documentation"
            value={data.documentation}
            trend={data.trends.documentation}
            chartData={data.historicalData.documentation}
          />
          <MetricCard
            label="Code Quality"
            value={data.codeQuality}
            trend={data.trends.codeQuality}
            chartData={data.historicalData.codeQuality}
          />
        </div>
      </div>

      {/* Type System Analysis */}
      <div className="bg-slate-800 p-6 rounded-lg space-y-6">
        <h2 className="text-2xl font-bold text-white">Type System Analysis</h2>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Type Distribution</h3>
            <div className="space-y-4">
              {Object.entries(data.typeMetrics).map(([type, count]) => (
                <TypeDistributionBar
                  key={type}
                  label={type}
                  count={count as number}
                  total={data.typeMetrics.total}
                />
              ))}
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Safety Metrics</h3>
            <div className="space-y-4">
              {Object.entries(data.safetyMetrics).map(([metric, value]) => (
                <div key={metric} className="flex justify-between items-center">
                  <span className="text-slate-300">{metric}</span>
                  <span className={`text-${(value as number) >= 90 ? 'green' : 'yellow'}-500`}>
                    {value}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Documentation Coverage */}
      <div className="bg-slate-800 p-6 rounded-lg space-y-6">
        <h2 className="text-2xl font-bold text-white">Documentation Coverage</h2>
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-4">
            {Object.entries(data.docMetrics).map(([category, value]) => (
              <TypeDistributionBar
                key={category}
                label={category}
                count={value as number}
                total={100}
              />
            ))}
          </div>
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Quality Metrics</h3>
            {Object.entries(data.docQuality).map(([metric, value]) => (
              <div key={metric} className="flex justify-between items-center">
                <span className="text-slate-300">{metric}</span>
                <span className={`text-${(value as number) >= 85 ? 'green' : 'yellow'}-500`}>
                  {value}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* File Analysis */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-white">File Analysis</h2>
        <div className="grid grid-cols-2 gap-6">
          {data.fileAnalysis.map((file: FileAnalysis) => (
            <FileAnalysisCard key={file.name} file={file} />
          ))}
        </div>
      </div>

      {/* Quality Gates */}
      <div className="bg-slate-800 p-6 rounded-lg space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">Quality Gates</h2>
          <span className="text-green-500 font-semibold">PASSED ✅</span>
        </div>
        <div className="space-y-4">
          {Object.entries(data.qualityGates).map(([gate, metrics]) => (
            <div key={gate} className="flex justify-between items-center">
              <span className="text-slate-300">{gate}</span>
              <div className="flex items-center space-x-4">
                <span className="text-slate-400">Target: {(metrics as any).target}%</span>
                <span className={`text-${(metrics as any).actual >= (metrics as any).target ? 'green' : 'red'}-500`}>
                  Actual: {(metrics as any).actual}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Action Items */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-white">Action Items</h2>
        <ActionItems items={data.actionItems} />
      </div>

      {/* Critical Issues Panel */}
      <div className="bg-slate-800 p-4 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
            <h2 className="text-white text-lg">Critical Issues</h2>
          </div>
          <span className="bg-red-500/20 text-red-500 px-2 py-1 rounded text-sm">
            2 Issues
          </span>
        </div>
        <div className="mt-4 space-y-4">
          {data?.criticalIssues?.map((issue: any, index: number) => (
            <div key={index} className="border-l-2 border-red-500 pl-4">
              <h3 className="text-white font-medium">{issue.title}</h3>
              <p className="text-slate-400 text-sm mt-1">{issue.description}</p>
              <div className="flex items-center mt-2">
                <span className="text-slate-500 text-xs">
                  {issue.file}:{issue.line}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TypeScriptReport;
