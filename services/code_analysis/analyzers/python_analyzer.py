from typing import Dict, List, Any, Optional
import ast
import logging
from ..base import CodeAnalyzerBase, AnalysisResult
from ..metrics.complexity import ComplexityMetrics
from .documentation_analyzer import DocumentationAnalyzer

logger = logging.getLogger(__name__)

class PythonAnalyzer(CodeAnalyzerBase):
    """Analyzer for Python code with enhanced documentation support."""
    
    def __init__(self):
        self.doc_analyzer = DocumentationAnalyzer()
        
    def analyze_code(self, content: str, filename: str) -> AnalysisResult:
        """Analyze Python code structure with enhanced documentation analysis"""
        try:
            tree = ast.parse(content)
            structures = []
            imports = []
            total_complexity = ComplexityMetrics()

            # Analyze each node
            for node in ast.walk(tree):
                try:
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                        complexity = self._calculate_complexity(node)
                        total_complexity.update(complexity)

                        if isinstance(node, ast.ClassDef):
                            structures.append({
                                'type': 'class',
                                'name': node.name,
                                'complexity': complexity,
                                'methods': self._analyze_method_complexity(node),
                                'inheritance': self._analyze_inheritance(node),
                                'api_stability': self._check_api_stability(node)
                            })
                        else:
                            structures.append({
                                'type': 'function',
                                'name': node.name,
                                'complexity': complexity,
                                'code_smells': self._detect_code_smells(node),
                                'api_stability': self._check_api_stability(node)
                            })
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        imports.extend(self._extract_imports(node))

                except Exception as e:
                    logger.error(f"Error analyzing node in {filename}: {str(e)}")
                    continue

            # Add documentation analysis
            doc_metrics = self.doc_analyzer.analyze_documentation(content, filename)

            return AnalysisResult(
                structures=structures,
                imports=imports,
                total_complexity=total_complexity,
                documentation_metrics=doc_metrics
            )

        except Exception as e:
            logger.error(f"Error in Python analysis for {filename}: {str(e)}")
            return self._empty_result()

    def _calculate_complexity(self, node: ast.AST) -> ComplexityMetrics:
        """Calculate complexity metrics for a Python AST node."""
        # Implementation remains the same...
        pass

    def _analyze_method_complexity(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Analyze complexity of class methods."""
        # Implementation remains the same...
        pass

    def _analyze_inheritance(self, node: ast.ClassDef) -> List[str]:
        """Analyze class inheritance hierarchy."""
        # Implementation remains the same...
        pass

    def _check_api_stability(self, node: ast.AST) -> Dict[str, Any]:
        """Check API stability metrics."""
        # Implementation remains the same...
        pass

    def _detect_code_smells(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Detect code smells in Python code."""
        # Implementation remains the same...
        pass

    def _extract_imports(self, node: ast.AST) -> List[str]:
        """Extract import statements from Python code."""
        # Implementation remains the same...
        pass
