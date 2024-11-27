from typing import Dict, Any, Optional, Union, List
import logging
import re
import ast
from dataclasses import dataclass, field
from pathlib import Path
from ..base import DocumentationMetrics

@dataclass
class DocumentationMetrics:
    """Documentation analysis metrics"""
    coverage: float = 0.0
    quality_score: float = 0.0
    module_doc: Optional[str] = None
    classes: Dict[str, Dict] = field(default_factory=dict)
    functions: Dict[str, Dict] = field(default_factory=dict)
    error: Optional[str] = None

    def __post_init__(self):
        if self.classes is None:
            self.classes = {}
        if self.functions is None:
            self.functions = {}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentationAnalyzer:
    """Analyzer for documentation quality and coverage."""
    
    def __init__(self):
        """Initialize the documentation analyzer."""
        self.doc_parser = None
        self.initialized = False
        self.initialization_error = None
    
    def initialize(self) -> None:
        """Initialize the analyzer."""
        if self.initialized:
            return
            
        try:
            self._initialize_parser()
            self.initialized = True
            logger.info("Documentation analyzer initialized successfully")
        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"Failed to initialize documentation analyzer: {str(e)}")
            raise
            
    def _initialize_parser(self) -> None:
        """Initialize documentation parser if not already done."""
        if self.doc_parser is not None:
            return
            
        try:
            from plugins.documentation_parser import DocumentationParser
            self.doc_parser = DocumentationParser()
            self.doc_parser.initialize()
            logger.info("Documentation parser initialized successfully")
        except ImportError as e:
            logger.error(f"Documentation parser module not found: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize documentation parser: {str(e)}")
            raise
            
    def analyze_documentation(self, content: str, filename: str) -> DocumentationMetrics:
        """Analyze documentation quality and coverage with multi-language support.
        
        Args:
            content: Source code content to analyze
            filename: Name of the file being analyzed
            
        Returns:
            DocumentationMetrics containing analysis results
        """
        try:
            if not self.initialized:
                self.initialize()

            # Determine file type and use appropriate parser
            ext = Path(filename).suffix.lower()
            if ext in ['.py']:
                return self._analyze_python_docs(content)
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                return self._analyze_jsdoc(content)
            else:
                return self._empty_doc_metrics(f'Unsupported file type: {ext}')

        except Exception as e:
            logger.error(f"Documentation analysis failed: {str(e)}")
            return self._empty_doc_metrics(str(e))

    def _analyze_python_docs(self, content: str) -> DocumentationMetrics:
        """Analyze Python documentation using AST."""
        try:
            tree = ast.parse(content)
            metrics = DocumentationMetrics()
            
            # Get module docstring
            metrics.module_doc = ast.get_docstring(tree)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_doc = ast.get_docstring(node)
                    methods = {}
                    
                    for child in node.body:
                        if isinstance(child, ast.FunctionDef):
                            methods[child.name] = {
                                'docstring': ast.get_docstring(child),
                                'args': [arg.arg for arg in child.args.args],
                                'returns': self._extract_return_info(child)
                            }
                            
                    metrics.classes[node.name] = {
                        'docstring': class_doc,
                        'methods': methods
                    }
                    
                elif isinstance(node, ast.FunctionDef):
                    metrics.functions[node.name] = {
                        'docstring': ast.get_docstring(node),
                        'args': [arg.arg for arg in node.args.args],
                        'returns': self._extract_return_info(node)
                    }
                    
            self._calculate_metrics(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Python documentation analysis failed: {str(e)}")
            return self._empty_doc_metrics(str(e))

    def _analyze_jsdoc(self, content: str) -> DocumentationMetrics:
        """Analyze JSDoc documentation using regex patterns."""
        try:
            metrics = DocumentationMetrics()
            
            # Match JSDoc blocks
            jsdoc_pattern = r'/\*\*\s*(.*?)\s*\*/'
            class_pattern = r'class\s+(\w+)'
            function_pattern = r'(async\s+)?function\s+(\w+)|const\s+(\w+)\s*=\s*(async\s+)?\('
            
            # Find all JSDoc blocks
            matches = list(re.finditer(jsdoc_pattern, content, re.DOTALL))
            
            for i, match in enumerate(matches):
                doc_block = match.group(1)
                next_code = content[match.end():].strip()
                
                if re.match(class_pattern, next_code):
                    class_name = re.match(class_pattern, next_code).group(1)
                    metrics.classes[class_name] = {
                        'docstring': doc_block,
                        'methods': {}
                    }
                elif re.match(function_pattern, next_code):
                    func_match = re.match(function_pattern, next_code)
                    func_name = func_match.group(2) or func_match.group(3)
                    metrics.functions[func_name] = {
                        'docstring': doc_block,
                        'args': self._extract_jsdoc_params(doc_block),
                        'returns': self._extract_jsdoc_returns(doc_block)
                    }
                elif i == 0 and not metrics.module_doc:
                    metrics.module_doc = doc_block
                    
            self._calculate_metrics(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"JSDoc analysis failed: {str(e)}")
            return self._empty_doc_metrics(str(e))

    def _extract_return_info(self, node: ast.FunctionDef) -> Optional[str]:
        """Extract return type information from function definition."""
        returns = None
        if node.returns:
            returns = ast.unparse(node.returns)
        return returns

    def _extract_jsdoc_params(self, docstring: str) -> List[str]:
        """Extract parameter names from JSDoc @param tags."""
        params = []
        param_pattern = r'@param\s+{[^}]+}\s+(\w+)'
        for match in re.finditer(param_pattern, docstring):
            params.append(match.group(1))
        return params

    def _extract_jsdoc_returns(self, docstring: str) -> Optional[str]:
        """Extract return type from JSDoc @returns tag."""
        returns_pattern = r'@returns?\s+{([^}]+)}'
        match = re.search(returns_pattern, docstring)
        return match.group(1) if match else None

    def _calculate_metrics(self, metrics: DocumentationMetrics) -> None:
        """Calculate coverage and quality scores."""
        total_elements = 1  # Module
        documented_elements = 1 if metrics.module_doc else 0
        
        # Calculate for classes and methods
        for class_info in metrics.classes.values():
            total_elements += 1
            if class_info['docstring']:
                documented_elements += 1
            
            for method_info in class_info.get('methods', {}).values():
                total_elements += 1
                if method_info.get('docstring'):
                    documented_elements += 1
        
        # Calculate for standalone functions
        for func_info in metrics.functions.values():
            total_elements += 1
            if func_info['docstring']:
                documented_elements += 1
        
        metrics.coverage = (documented_elements / total_elements * 100) if total_elements > 0 else 0
        metrics.quality_score = self._calculate_quality_score(metrics)
            
    def _empty_doc_metrics(self, error_message: Optional[str] = None) -> DocumentationMetrics:
        """Create empty documentation metrics."""
        return DocumentationMetrics(
            module_doc=None,
            classes={},
            functions={},
            coverage=0.0,
            quality_score=0.0,
            error=error_message if error_message else 'No documentation available'
        )
