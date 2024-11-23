from typing import Dict, List, Any
import re
import logging
from ..base import CodeAnalyzerBase, AnalysisResult
from ..metrics.complexity import ComplexityMetrics
from .documentation_analyzer import DocumentationAnalyzer

logger = logging.getLogger(__name__)

class JavaScriptAnalyzer(CodeAnalyzerBase):
    """Analyzer for JavaScript/TypeScript code with documentation support."""
    
    def __init__(self):
        self.doc_analyzer = DocumentationAnalyzer()
        
    def analyze_code(self, content: str, filename: str) -> AnalysisResult:
        """Analyze JavaScript/TypeScript code structure."""
        try:
            # Basic structure analysis
            structures = []
            imports = []

            # Parse imports using regex
            import_patterns = [
                r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'require\([\'"]([^\'"]+)[\'"]\)',
                r'import\([\'"]([^\'"]+)[\'"]\)'
            ]

            for pattern in import_patterns:
                imports.extend(re.findall(pattern, content))

            # Calculate complexity metrics
            total_complexity = ComplexityMetrics(
                cyclomatic_complexity=self._calculate_cyclomatic_complexity(content),
                cognitive_complexity=self._calculate_cognitive_complexity(content),
                nesting_depth=self._calculate_nesting_depth(content),
                maintainability_index=100.0  # Default value
            )

            # Add documentation analysis
            doc_metrics = self.doc_analyzer.analyze_documentation(content, filename)

            return AnalysisResult(
                structures=structures,
                imports=list(set(imports)),
                total_complexity=total_complexity,
                documentation_metrics=doc_metrics
            )

        except Exception as e:
            logger.error(f"Error analyzing JavaScript file {filename}: {str(e)}")
            return self._empty_result()

    def _calculate_cyclomatic_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity for JavaScript code."""
        # Count decision points
        decision_points = len(re.findall(r'\b(if|while|for|switch|case|&&|\|\|)\b', content))
        return decision_points + 1

    def _calculate_cognitive_complexity(self, content: str) -> int:
        """Calculate cognitive complexity for JavaScript code."""
        return len(re.findall(r'\b(if|while|for|switch)\b', content))

    def _calculate_nesting_depth(self, content: str) -> int:
        """Calculate maximum nesting depth in JavaScript code."""
        max_depth = 0
        current_depth = 0
        
        for char in content:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
                
        return max_depth
