import React from 'react';
import { createRoot } from 'react-dom/client';
import { TypeScriptReport } from './components/TypeScriptReport';
import '../css/tailwind.css';

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('typescript-report');
  if (container) {
    const root = createRoot(container);
    
    // Get the analysis data from the window object (populated by Flask)
    const analysisData = (window as any).analysisData || {};
    
    root.render(
      <React.StrictMode>
        <TypeScriptReport data={analysisData} />
      </React.StrictMode>
    );
  }
});
