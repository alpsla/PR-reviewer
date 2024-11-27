import React from 'react';
import { ChevronDown, AlertCircle, CheckCircle, TrendingUp, TrendingDown } from 'lucide-react';

export const MetricCard = ({ title, value, trend, status }) => (
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-sm font-medium text-gray-500">{title}</h3>
    <div className="mt-2 flex items-baseline justify-between">
      <p className={`text-2xl font-semibold ${status === 'success' ? 'text-green-600' : 'text-yellow-600'}`}>
        {value.toFixed(1)}%
      </p>
      {trend !== 0 && (
        <span className={`flex items-center ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
          {trend > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          <span className="ml-1 text-sm">{Math.abs(trend)}%</span>
        </span>
      )}
    </div>
  </div>
);

export const CollapsibleSection = ({ title, score, issueCount, children }) => {
  const [isOpen, setIsOpen] = React.useState(true);
  
  return (
    <div className="border rounded-lg">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 text-left"
      >
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-medium">{title}</h3>
          {score !== null && (
            <span className={`px-2 py-1 rounded text-sm ${
              score > 80 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
            }`}>
              {score?.toFixed(1)}%
            </span>
          )}
          {issueCount !== undefined && (
            <span className="px-2 py-1 rounded text-sm bg-red-100 text-red-800">
              {issueCount} issues
            </span>
          )}
        </div>
        <ChevronDown className={`w-5 h-5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && <div className="p-4 border-t">{children}</div>}
    </div>
  );
};

export const TypeMetric = ({ title, value, total }) => {
  const percentage = total > 0 ? (value / total) * 100 : 0;
  
  return (
    <div className="bg-gray-50 p-4 rounded-lg">
      <div className="flex justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{title}</span>
        <span className="text-sm text-gray-500">{value}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export const DocMetric = ({ title, value, status }) => (
  <div className="bg-gray-50 p-4 rounded-lg">
    <div className="flex justify-between items-center">
      <span className="text-sm font-medium text-gray-600">{title}</span>
      <span className={`flex items-center ${status === 'success' ? 'text-green-600' : 'text-yellow-600'}`}>
        {status === 'success' ? (
          <CheckCircle className="w-4 h-4 mr-2" />
        ) : (
          <AlertCircle className="w-4 h-4 mr-2" />
        )}
        {value.toFixed(1)}%
      </span>
    </div>
  </div>
);
