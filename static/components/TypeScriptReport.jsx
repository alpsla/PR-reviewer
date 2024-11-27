import React from 'react';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const TypeScriptReport = ({ analysisData }) => {
  const { metrics, action_items, best_practices, quality_gates } = analysisData;

  // Chart data for type distribution
  const typeDistributionData = {
    labels: ['Interfaces', 'Type Aliases', 'Classes', 'Generic Types', 'Mapped Types', 'Utility Types'],
    datasets: [{
      data: [
        metrics.interfaces_count,
        metrics.type_aliases_count,
        metrics.classes_count,
        metrics.generic_types_count,
        metrics.mapped_types_count,
        metrics.utility_types_count
      ],
      backgroundColor: [
        '#FF6384',
        '#36A2EB',
        '#FFCE56',
        '#4BC0C0',
        '#9966FF',
        '#FF9F40'
      ]
    }]
  };

  // Chart data for quality gates
  const qualityGatesData = {
    labels: quality_gates.map(gate => gate.name),
    datasets: [{
      label: 'Current Score',
      data: quality_gates.map(gate => gate.current_value),
      backgroundColor: quality_gates.map(gate => 
        gate.current_value >= gate.target_value ? '#4BC0C0' : '#FF6384'
      ),
    }]
  };

  const qualityGatesOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      title: { display: true, text: 'Quality Gates' }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        title: { display: true, text: 'Score' }
      }
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">TypeScript Analysis Report</h1>
      
      {/* Quality Gates Section */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4">Quality Gates</h2>
        <div className="h-80">
          <Bar data={qualityGatesData} options={qualityGatesOptions} />
        </div>
      </section>

      {/* Type Distribution Section */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4">Type Distribution</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="h-80">
            <Pie data={typeDistributionData} />
          </div>
          <div>
            <h3 className="text-xl font-semibold mb-4">Key Metrics</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Type Coverage</p>
                <p className="text-2xl font-bold">{metrics.type_coverage.toFixed(1)}%</p>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Type Safety Score</p>
                <p className="text-2xl font-bold">{metrics.type_safety_score.toFixed(1)}%</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Action Items Section */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4">Action Items</h2>
        {Object.entries(action_items).map(([priority, items]) => (
          items.length > 0 && (
            <div key={priority} className="mb-6">
              <h3 className="text-xl font-semibold mb-2 capitalize">{priority} Priority</h3>
              <div className="space-y-4">
                {items.map((item, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded">
                    <h4 className="font-semibold">{item.title}</h4>
                    <p className="text-sm text-gray-600">Current: {item.current} → Target: {item.target}</p>
                    <ul className="mt-2 list-disc list-inside text-sm">
                      {item.strategy.map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )
        ))}
      </section>

      {/* Best Practices Section */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4">Best Practices</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-xl font-semibold mb-4 text-green-600">Strong Areas</h3>
            <ul className="list-disc list-inside space-y-2">
              {best_practices.strong_areas.map((area, index) => (
                <li key={index}>{area}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-xl font-semibold mb-4 text-amber-600">Needs Improvement</h3>
            <ul className="list-disc list-inside space-y-2">
              {best_practices.needs_improvement.map((area, index) => (
                <li key={index}>{area}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Code Samples Section */}
      {analysisData.samples && analysisData.samples.length > 0 && (
        <section>
          <h2 className="text-2xl font-semibold mb-4">Code Samples</h2>
          <div className="space-y-6">
            {analysisData.samples.map((sample, index) => (
              <div key={index} className="bg-gray-50 p-4 rounded">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">Line {sample.line_number}</span>
                </div>
                <SyntaxHighlighter language="typescript" style={tomorrow}>
                  {sample.context}
                </SyntaxHighlighter>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default TypeScriptReport;
