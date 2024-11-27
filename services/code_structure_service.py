import ast
import math
import re
from datetime import datetime
import logging
from typing import Dict, Any, Optional, NamedTuple, List, Union, Set, TypedDict
from pathlib import Path
from dataclasses import dataclass, field
import concurrent.futures
import tempfile
import subprocess
import json
from functools import lru_cache
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)
import concurrent.futures
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TypedDict, Union, Set, Any
import ast
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
import tempfile
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=
    '%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LanguageConfig:
    """Configuration for language-specific analysis."""
    name: str
    extensions: List[str]
    is_compiled: bool = False
    doc_style: str = "google"  # google, numpy, sphinx, jsdoc
    max_line_length: int = 80
    complexity_threshold: int = 10
    parser_config: Dict = field(default_factory=lambda: {
        'analyze_imports': True,
        'analyze_complexity': True,
        'analyze_documentation': True,
        'require_docstrings': True,
        'min_doc_length': 10,
        'check_params': True,
        'check_returns': True,
        'check_examples': True
    })


@dataclass
class SecurityMetrics:
    """Security-related metrics"""
    vulnerabilities: List[Dict] = field(default_factory=list)
    unsafe_patterns: List[Dict] = field(default_factory=list)
    security_score: float = 100.0
    authentication_checks: bool = False
    input_validation: bool = False
    data_encryption: bool = False


@dataclass
class PerformanceMetrics:
    """Performance-related metrics"""
    memory_usage: Optional[float] = None
    time_complexity: str = "O(1)"
    space_complexity: str = "O(1)"
    async_operations: bool = False
    caching_used: bool = False
    resource_leaks: List[str] = field(default_factory=list)


import subprocess
import json
from functools import lru_cache


class FileAnalyzer:
    """Analyzer for source code files"""

    def __init__(self, content: str, language: str):
        self.content = content
        self.language = language

    def analyze(self) -> Dict:
        """Analyze the source code file"""
        try:
            metrics = lizard.analyze_file(self.content)
            return metrics
        except Exception as e:
            logger.error(f"Error analyzing file: {str(e)}")
            return {'nloc': 0, 'CCN': 0, 'token_count': 0, 'function_list': []}

    def _analyze_security(self, content: str,
                          language_config: LanguageConfig) -> SecurityMetrics:
        """Analyze security aspects of the code"""
        security_metrics = SecurityMetrics()

        # Check for common security patterns
        patterns = {
            'sql_injection':
            r'(?i)(execute|raw)\s*\(\s*[\'"][^\']*\%s[\'"]\s*\)',
            'xss': r'(?i)innerHTML\s*=|document\.write\(',
            'command_injection':
            r'(?i)(subprocess\.call|os\.system|eval|exec)\(',
            'path_traversal': r'(?i)\.\./',
        }

        for vuln_type, pattern in patterns.items():
            if re.search(pattern, content):
                security_metrics.vulnerabilities.append({
                    'type':
                    vuln_type,
                    'severity':
                    'high',
                    'description':
                    f'Potential {vuln_type} vulnerability detected'
                })

        # Check for authentication patterns
        security_metrics.authentication_checks = bool(
            re.search(r'(?i)(authenticate|login|authorize)', content))

        # Check for input validation
        security_metrics.input_validation = bool(
            re.search(r'(?i)(validate|sanitize|escape)', content))

        return security_metrics

    def _analyze_performance(
            self, content: str,
            language_config: LanguageConfig) -> PerformanceMetrics:
        """Analyze performance aspects of the code"""
        performance_metrics = PerformanceMetrics()

        # Check for common performance patterns
        if re.search(r'(?i)(cache|memoize|lru_cache)', content):
            performance_metrics.caching_used = True

        # Check for async operations
        if re.search(r'(?i)(async|await|promise|concurrent)', content):
            performance_metrics.async_operations = True

        # Check for potential resource leaks
        resource_patterns = {
            'file_handles': r'(?i)open\([^)]+\)',
            'database_connections': r'(?i)(connect|cursor)\(',
            'thread_creation': r'(?i)(thread|process)\(',
        }

        for resource_type, pattern in resource_patterns.items():
            if re.search(pattern, content):
                # Check if there's proper cleanup
                cleanup_pattern = resource_type == 'file_handles' and 'close()' or 'dispose()'
                if not re.search(f'(?i){cleanup_pattern}', content):
                    performance_metrics.resource_leaks.append(
                        f'Potential unclosed {resource_type}')

        return performance_metrics


import lizard

# Define language configurations
LANGUAGE_CONFIGS = {
    'python': LanguageConfig(
        name='Python',
        extensions=['.py', '.pyi', '.pyx'],
        is_compiled=False,
        doc_style='google',
        max_line_length=88,
        complexity_threshold=10,
        parser_config={
            'analyze_imports': True,
            'analyze_complexity': True,
            'analyze_documentation': True,
            'require_docstrings': True,
            'min_doc_length': 10,
            'check_params': True,
            'check_returns': True,
            'check_examples': True
        }
    ),
    'javascript': LanguageConfig(
        name='JavaScript',
        extensions=['.js', '.jsx', '.mjs'],
        is_compiled=False,
        doc_style='jsdoc',
        max_line_length=80,
        complexity_threshold=12,
        parser_config={
            'analyze_imports': True,
            'analyze_complexity': True,
            'analyze_documentation': True,
            'require_docstrings': True,
            'min_doc_length': 8,
            'check_params': True,
            'check_returns': True,
            'check_examples': False
        }
    ),
    'typescript': LanguageConfig(
        name='TypeScript',
        extensions=['.ts', '.tsx'],
        is_compiled=True,
        doc_style='jsdoc',
        max_line_length=80,
        complexity_threshold=12,
        parser_config={
            'analyze_imports': True,
            'analyze_complexity': True,
            'analyze_documentation': True,
            'require_docstrings': True,
            'min_doc_length': 8,
            'check_params': True,
            'check_returns': True,
            'check_examples': False
        }
    )
}

# Already defined SecurityMetrics and PerformanceMetrics above


@dataclass
class EnhancedComplexityMetrics:
    """Enhanced complexity metrics"""
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    halstead_metrics: Dict = field(default_factory=dict)
    maintainability_index: float = 100.0
    nesting_depth: int = 0
    documentation_coverage: float = 0.0


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=
    '%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)


class CodeSmell(TypedDict):
    """Code smell information"""
    type: str
    description: str
    severity: str
    location: str


class APIStabilityInfo(TypedDict):
    """API stability information"""
    is_public: bool
    has_breaking_changes: bool
    version_info: Optional[str]


@dataclass
class ComplexityMetrics:
    """Complexity metrics for code analysis"""
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    nesting_depth: int = 0
    maintainability_index: float = 100.0

    def update(self, other: 'ComplexityMetrics') -> None:
        """Update metrics from another ComplexityMetrics object"""
        self.cyclomatic_complexity += other.cyclomatic_complexity
        self.cognitive_complexity += other.cognitive_complexity
        self.nesting_depth = max(self.nesting_depth, other.nesting_depth)
        self.maintainability_index = (self.maintainability_index +
                                      other.maintainability_index) / 2


@dataclass
class AnalysisResult:
    """Result of code structure analysis"""
    structures: List[Dict]
    imports: List[str]
    total_complexity: ComplexityMetrics
    security_metrics: Optional[SecurityMetrics] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    documentation_metrics: Optional[Dict[str, Any]] = None


class CodeStructureService:
    """Enhanced service for analyzing code structure with multi-language support"""

    def __init__(self):
        """Initialize the service with enhanced capabilities"""
        self.logger = get_logger(__name__, "code_structure")
        self.logger.set_context(service="code_structure")
        
        try:
            # Initialize Python analyzer
            from services.code_analysis.analyzers.python_analyzer import PythonAnalyzer
            self.python_analyzer = PythonAnalyzer()
            self.logger.info("Python analyzer initialized successfully")
            
            # Initialize JavaScript/TypeScript analyzers
            from services.code_analysis.analyzers.javascript_analyzer import JavaScriptAnalyzer
            from services.code_analysis.analyzers.typescript_analyzer import TypeScriptAnalyzer
            self.javascript_analyzer = JavaScriptAnalyzer()
            self.typescript_analyzer = TypeScriptAnalyzer()
            self.logger.info("JavaScript/TypeScript analyzers initialized successfully")
            
        except ImportError as e:
            self.logger.error("Failed to import analyzer module", extra={
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            raise
        except Exception as e:
            self.logger.error("Failed to initialize analyzers", extra={
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            raise

        # Initialize caches and storage
        self.metrics_cache = {}
        self.language_stats = {}
        self.dependency_graph = {}
        self.api_stability_info = {}

        try:
            self._init_language_analyzers()
            self.logger.info("Language analyzers configuration completed")
        except Exception as e:
            self.logger.error("Failed to configure language analyzers", extra={
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            raise

    def _get_cache_key(self, content: str, filename: str) -> str:
        """Generate cache key for analysis results"""
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"{filename}:{content_hash}"

    def _store_result(self, cache_key: str, result: AnalysisResult) -> None:
        """Store analysis result in cache"""
        self.metrics_cache[cache_key] = {
            'result': result,
            'timestamp': datetime.utcnow(),
            'metrics': {
                'documentation_coverage':
                self._calculate_doc_coverage(result),
                'dependency_count':
                len(result.imports),
                'complexity_score':
                result.total_complexity.cyclomatic_complexity,
                'maintainability_index':
                result.total_complexity.maintainability_index
            }
        }

    def _init_language_analyzers(self):
        """Initialize language-specific analyzers"""
        try:
            import astroid
            import pylint
            import mypy
            self.python_analyzers_available = True
            logger.info("Python analyzers initialized successfully")
        except ImportError:
            self.python_analyzers_available = False
            logger.warning("Python analyzers not available")

        try:
            import esprima
            self.js_analyzers_available = True
            logger.info("JavaScript analyzers initialized successfully")
        except ImportError:
            self.js_analyzers_available = False
            logger.warning("JavaScript analyzers not available")

    def _calculate_nesting_depth(self, content: str) -> int:
        """Calculate maximum nesting depth in code."""
        try:
            lines = content.split('\n')
            max_depth = 0
            current_depth = 0

            for line in lines:
                # Count opening braces/brackets
                current_depth += line.count('{') - line.count('}')
                max_depth = max(max_depth, current_depth)

            return max_depth
        except Exception as e:
            logger.error(f"Error calculating nesting depth: {str(e)}")
            return 0

    def _empty_result(self) -> AnalysisResult:
        """Return empty analysis result."""
        return AnalysisResult(structures=[],
                              imports=[],
                              total_complexity=ComplexityMetrics(),
                              security_metrics=SecurityMetrics(),
                              performance_metrics=PerformanceMetrics(),
                              documentation_metrics=None)

    def analyze_code(self, content: str, filename: str) -> AnalysisResult:
        """Analyze code structure with enhanced multi-language support and error handling"""
        logger.info(f"Starting analysis for file: {filename}")

        # Check cache first
        cache_key = self._get_cache_key(content, filename)
        if cache_key in self.metrics_cache:
            cached = self.metrics_cache[cache_key]
            if (datetime.utcnow() - cached['timestamp']
                ).total_seconds() < 3600:  # 1 hour cache
                logger.info(f"Using cached analysis for {filename}")
                return cached['result']

        try:
            # Input validation
            if not content or not filename:
                logger.error("Invalid input: content or filename is empty")
                return self._empty_result()

            # Skip empty content
            if not content.strip():
                logger.info(f"Skipping empty file: {filename}")
                return {
                    'filename': filename,
                    'type': 'empty',
                    'size': 0,
                    'structure': {},
                    'metrics': {
                        'complexity': 0,
                        'lines': 0,
                        'functions': 0,
                        'classes': 0
                    }
                }

            # Get language configuration
            ext = Path(filename).suffix.lower()
            language_config = None

            for lang_config in LANGUAGE_CONFIGS.values():
                if ext in lang_config.extensions:
                    language_config = lang_config
                    break

            if not language_config:
                logger.warning(f"Unsupported file type: {filename}")
                return self._empty_result()

            logger.info(
                f"Using {language_config.name} analyzer for {filename}")

            # Basic metrics using file analyzer
            file_analyzer = FileAnalyzer(content, language_config.name)
            metrics = file_analyzer.analyze()

            # Language-specific analysis
            if language_config.name == 'Python':
                result = self._analyze_python_enhanced(content, filename,
                                                       metrics)
            elif language_config.name in ('JavaScript', 'TypeScript'):
                result = self._analyze_javascript_enhanced(
                    content, filename, metrics)
            else:
                logger.warning(
                    f"Falling back to basic analysis for {filename}")
                result = self._analyze_generic(content, filename, metrics)

            # Add security and performance metrics
            result.security_metrics = file_analyzer._analyze_security(
                content, language_config)
            result.performance_metrics = file_analyzer._analyze_performance(
                content, language_config)

            # Add documentation metrics with enhanced error handling
            try:
                doc_metrics = self._analyze_documentation(content, filename)
                if doc_metrics:
                    result.documentation_metrics = {
                        'module_doc': doc_metrics.module_doc,
                        'classes': doc_metrics.classes,
                        'functions': doc_metrics.functions,
                        'coverage': doc_metrics.coverage,
                        'quality_score': doc_metrics.quality_score,
                        'error': doc_metrics.error
                    }
                    logger.info(f"Documentation analysis completed for {filename}")
                else:
                    logger.warning(f"No documentation metrics available for {filename}")
                    result.documentation_metrics = None
            except Exception as e:
                logger.error(f"Documentation analysis failed for {filename}: {str(e)}")
                result.documentation_metrics = None
            
            # Cache and return result
            self._store_result(cache_key, result)
            logger.info(f"Analysis completed successfully for {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            return self._empty_result()

    def analyze_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze a list of files and return their structures."""
        results = []
        for file_info in files:
            try:
                filename = file_info.get('filename', '')
                logger.info(f"Starting analysis for file: {filename}")
                
                # Get file content from various possible sources
                content = None
                for key in ['patch', 'content', 'source', 'raw']:
                    if key in file_info and file_info[key]:
                        content = file_info[key]
                        break
                
                if not content:
                    logger.warning(f"No content found for file: {filename}")
                    continue
                
                # Create file info with content
                analysis_info = {
                    'filename': filename,
                    'content': content
                }
                
                # Analyze file
                result = self.analyze_file(analysis_info)
                if result:
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Error analyzing file {filename}: {str(e)}")
                continue
                
        return results

    def _analyze_documentation(self, content: str, filename: str) -> Dict[str, Any]:
        """Analyze documentation quality and coverage with support for multiple doc styles."""
        try:
            if not hasattr(self, 'doc_analyzer'):
                from services.code_analysis.analyzers.documentation_analyzer import DocumentationAnalyzer
                self.doc_analyzer = DocumentationAnalyzer()
                self.doc_analyzer.initialize()
                logger.info("Documentation analyzer initialized")

            # Execute documentation analysis
            doc_metrics = self.doc_analyzer.analyze_documentation(content, filename)
            if not doc_metrics:
                return self._empty_doc_info('No documentation found')

            # Convert to standardized format
            result = {
                'module_doc': doc_metrics.module_doc,
                'classes': doc_metrics.classes,
                'functions': doc_metrics.functions,
                'coverage': doc_metrics.coverage,
                'quality_score': doc_metrics.quality_score,
                'error': doc_metrics.error
            }

            logger.info(f"Documentation analysis completed for {filename}")
            return result

        except Exception as e:
            logger.error(f"Documentation analysis failed: {str(e)}")
            return self._empty_doc_info(str(e))

    def _analyze_documentation(self, content: str, filename: str) -> Dict[str, Any]:
        """Analyze documentation quality and coverage with support for multiple doc styles."""
        try:
            if not hasattr(self, 'doc_analyzer'):
                from services.code_analysis.analyzers.documentation_analyzer import DocumentationAnalyzer
                self.doc_analyzer = DocumentationAnalyzer()
                self.doc_analyzer.initialize()

            doc_metrics = self.doc_analyzer.analyze_documentation(content, filename)
            if not doc_metrics:
                return self._empty_doc_info('No documentation found')
            
            return {
                'module_doc': doc_metrics.module_doc,
                'classes': doc_metrics.classes,
                'functions': doc_metrics.functions,
                'coverage': doc_metrics.coverage,
                'quality_score': doc_metrics.quality_score,
                'error': doc_metrics.error
            }
        except Exception as e:
            logger.error(f"Documentation analysis failed: {str(e)}")
            return self._empty_doc_info(str(e))

    def _empty_doc_info(self, error_message: Optional[str] = None) -> Dict[str, Any]:
        """Create an empty documentation info structure."""
        return {
            'module_doc': None,
            'classes': {},
            'functions': {},
            'coverage': 0.0,
            'quality_score': 0.0,
            'error': error_message if error_message else 'No documentation available'
        }

    def _analyze_javascript(self, content: str, filename: str) -> AnalysisResult:
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
                maintainability_index=100.0
            )

            # Add documentation analysis
            doc_analysis = self._analyze_documentation(content, filename)

            return AnalysisResult(
                structures=structures,
                imports=list(set(imports)),
                total_complexity=total_complexity,
                documentation_metrics=doc_analysis
            )

        except Exception as e:
            logger.error(f"Error analyzing JavaScript file {filename}: {str(e)}")
            return self._empty_result()
            
            

    

    

    

    

    def _analyze_generic(self, content: str, filename: str, metrics: Dict) -> AnalysisResult:
        """Generic analysis for unsupported languages"""
        structures = []
        imports = []
        total_complexity = ComplexityMetrics()

        # Basic structure analysis
        total_complexity.cyclomatic_complexity = metrics.get('CCN', 0)
        total_complexity.cognitive_complexity = metrics.get(
            'CCN', 0)  # Using CCN as approximation
        total_complexity.maintainability_index = 100.0 - (
            metrics.get('CCN', 0) * 0.1)
        total_complexity.nesting_depth = 0

        return AnalysisResult(structures=structures,
                              imports=imports,
                              total_complexity=total_complexity)

    def _analyze_python(self, content: str, filename: str) -> AnalysisResult:
        """Analyze Python code structure with documentation analysis"""
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
            doc_analysis = self._analyze_documentation(content, filename)

            return AnalysisResult(
                structures=structures,
                imports=imports,
                total_complexity=total_complexity,
                documentation_metrics=doc_analysis
            )

        except Exception as e:
            logger.error(f"Error in Python analysis for {filename}: {str(e)}")
            return self._empty_result()

    def _analyze_javascript(self, content: str, filename: str) -> AnalysisResult:
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
                maintainability_index=100.0
            )

            # Add documentation analysis
            doc_analysis = self._analyze_documentation(content, filename)

            return AnalysisResult(
                structures=structures,
                imports=list(set(imports)),
                total_complexity=total_complexity,
                documentation_metrics=doc_analysis
            )

        except Exception as e:
            logger.error(f"Error analyzing JavaScript file {filename}: {str(e)}")
            return self._empty_result()

    def _calculate_complexity(
            self, node: Union[ast.ClassDef,
                              ast.FunctionDef]) -> ComplexityMetrics:
        """Calculate complexity metrics for Python code"""
        cyclomatic = 1
        cognitive = 0
        current_depth = 0
        max_depth = 0

        for child in ast.walk(node):
            # Calculate cyclomatic complexity
            if isinstance(child,
                          (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                cyclomatic += 1
                cognitive += (1 + current_depth)
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif isinstance(child, ast.BoolOp):
                cyclomatic += len(child.values) - 1
            else:
                current_depth = max(0, current_depth - 1)

        # Calculate maintainability index
        loc = self._count_lines(node)
        mi = 171 - 5.2 * math.log(cognitive +
                                  1) - 0.23 * cyclomatic - 16.2 * math.log(loc)
        mi = max(0, mi) * 100 / 171

        return ComplexityMetrics(cyclomatic_complexity=cyclomatic,
                                 cognitive_complexity=cognitive,
                                 nesting_depth=max_depth,
                                 maintainability_index=round(mi, 2))

    def _extract_imports(self, node: Union[ast.Import,
                                           ast.ImportFrom]) -> List[str]:
        """Extract import statements"""
        imports = []
        try:
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module if node.module else ''
                for name in node.names:
                    imports.append(
                        f"{module}.{name.name}" if module else name.name)
        except Exception as e:
            logger.error(f"Error extracting imports: {str(e)}")
        return imports

    def _get_attribute_chain(self, node: ast.Attribute) -> str:
        """Get the full chain of attribute access"""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return '.'.join(reversed(parts))

    def _detect_code_smells(
            self, node: Union[ast.ClassDef,
                              ast.FunctionDef]) -> List[CodeSmell]:
        """Detect code smells"""
        try:
            smells = []

            # Check function/method length
            loc = self._count_lines(node)
            if loc > 50:
                smells.append({
                    'type': 'long_function',
                    'description':
                    f'Function/method is too long ({loc} lines)',
                    'severity': 'medium',
                    'location': f'Line {node.lineno}'
                })

            # Check parameter count
            if isinstance(node, ast.FunctionDef):
                args_count = len(node.args.args)
                if args_count > 5:
                    smells.append({
                        'type': 'long_parameter_list',
                        'description':
                        f'Function has too many parameters ({args_count})',
                        'severity': 'medium',
                        'location': f'Line {node.lineno}'
                    })

            return smells
        except Exception as e:
            logger.error(f"Error detecting code smells: {str(e)}")
            return []

    def _check_api_stability(
            self, node: Union[ast.ClassDef,
                              ast.FunctionDef]) -> APIStabilityInfo:
        """Check API stability indicators"""
        try:
            is_public = not node.name.startswith('_')
            version_info = None
            has_breaking_changes = False

            # Check docstring for version information
            docstring = ast.get_docstring(node)
            if docstring:
                version_match = re.search(r'@version\s+(\S+)', docstring)
                if version_match:
                    version_info = version_match.group(1)

                # Check for breaking changes indicators
                breaking_indicators = ['@breaking', '@deprecated']
                has_breaking_changes = any(
                    indicator in docstring
                    for indicator in breaking_indicators)

            return {
                'is_public': is_public,
                'has_breaking_changes': has_breaking_changes,
                'version_info': version_info
            }
        except Exception as e:
            logger.error(f"Error checking API stability: {str(e)}")
            return {
                'is_public': True,
                'has_breaking_changes': False,
                'version_info': None
            }

    def _analyze_inheritance(self, node: ast.ClassDef) -> Dict:
        """Analyze class inheritance patterns"""
        try:
            inheritance_info = {
                'bases': [],
                'depth': 0,
                'multiple_inheritance': False
            }

            # Get base classes
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(self._get_attribute_chain(base))

            inheritance_info['bases'] = bases
            inheritance_info['multiple_inheritance'] = len(bases) > 1
            inheritance_info['depth'] = len(bases)

            return inheritance_info
        except Exception as e:
            logger.error(f"Error analyzing inheritance: {str(e)}")
            return {'bases': [], 'depth': 0, 'multiple_inheritance': False}

    def _analyze_method_complexity(
            self, node: ast.ClassDef) -> Dict[str, ComplexityMetrics]:
        """Analyze complexity of class methods"""
        try:
            method_complexity = {}

            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    method_complexity[child.name] = self._calculate_complexity(
                        child)

            return method_complexity
        except Exception as e:
            logger.error(f"Error analyzing method complexity: {str(e)}")
            return {}

    def _count_lines(self, node: Union[ast.ClassDef, ast.FunctionDef]) -> int:
        """Count lines of code in Python node"""
        try:
            start_line = node.lineno
            end_line = 0
            for child in ast.walk(node):
                if hasattr(child, 'lineno'):
                    end_line = max(end_line, child.lineno)
            return max(1, end_line - start_line + 1)
        except Exception as e:
            logger.error(f"Error counting lines: {str(e)}")
            return 1

    def _empty_result(self) -> AnalysisResult:
        """Create an empty analysis result"""
        return AnalysisResult(structures=[],
                              imports=[],
                              total_complexity=ComplexityMetrics())

    def _walk_js_ast(self, node):
        """Walk JavaScript/TypeScript AST"""
        yield node
        for key, value in node.__dict__.items():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, '__dict__'):
                        yield from self._walk_js_ast(item)
            elif hasattr(value, '__dict__'):
                yield from self._walk_js_ast(value)

    def _calculate_js_complexity(self, node) -> ComplexityMetrics:
        """Calculate complexity metrics for JavaScript/TypeScript code"""
        cyclomatic = 1
        cognitive = 0
        current_depth = 0
        max_depth = 0

        for child in self._walk_js_ast(node):
            # Calculate cyclomatic complexity
            if child.type in {
                    'IfStatement', 'WhileStatement', 'DoWhileStatement',
                    'ForStatement', 'ForInStatement', 'ForOfStatement',
                    'ConditionalExpression', 'LogicalExpression'
            }:
                cyclomatic += 1
                cognitive += (1 + current_depth)
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif child.type in {'CatchClause', 'SwitchCase'}:
                cyclomatic += 1
            else:
                current_depth = max(0, current_depth - 1)

        # Calculate maintainability index
        loc = self._count_js_lines(node)
        mi = 171 - 5.2 * math.log(cognitive +
                                  1) - 0.23 * cyclomatic - 16.2 * math.log(loc)
        mi = max(0, mi) * 100 / 171

        return ComplexityMetrics(cyclomatic_complexity=cyclomatic,
                                 cognitive_complexity=cognitive,
                                 nesting_depth=max_depth,
                                 maintainability_index=round(mi, 2))

    def _find_js_imports(self, tree) -> List[str]:
        """Find imports in JavaScript/TypeScript code"""
        imports = []
        for node in self._walk_js_ast(tree):
            if node.type == 'ImportDeclaration':
                imports.append(node.source.value)
            elif node.type == 'CallExpression' and node.callee.name == 'require':
                if node.arguments and node.arguments[0].type == 'Literal':
                    imports.append(node.arguments[0].value)
        return imports

    def _find_js_dependencies(self, node) -> List[str]:
        """Find dependencies in JavaScript/TypeScript code"""
        dependencies = set()
        for child in self._walk_js_ast(node):
            if child.type == 'CallExpression':
                if hasattr(child.callee, 'name'):
                    dependencies.add(child.callee.name)
                elif hasattr(child.callee, 'property'):
                    dependencies.add(child.callee.property.name)
        return list(dependencies)

    def _detect_js_code_smells(self, node) -> List[CodeSmell]:
        """Detect code smells in JavaScript/TypeScript code"""
        smells = []

        # Check function/method length
        loc = self._count_js_lines(node)
        if loc > 50:
            smells.append({
                'type': 'long_function',
                'description': f'Function/method is too long ({loc} lines)',
                'severity': 'medium',
                'location': f'Line {node.loc.start.line}'
            })

        # Check parameter count for functions
        if node.type in {'FunctionDeclaration', 'MethodDefinition'}:
            params = node.params if hasattr(node, 'params') else []
            if len(params) > 5:
                smells.append({
                    'type': 'long_parameter_list',
                    'description':
                    f'Function has too many parameters ({len(params)})',
                    'severity': 'medium',
                    'location': f'Line {node.loc.start.line}'
                })

        return smells

    def _check_js_api_stability(self, node) -> APIStabilityInfo:
        """Check API stability in JavaScript/TypeScript code"""
        is_public = not (hasattr(node, 'id') and node.id.name.startswith('_'))
        version_info = None
        has_breaking_changes = False

        # Check JSDoc comments
        if hasattr(node, 'leadingComments'):
            for comment in node.leadingComments:
                if comment.type == 'Block':
                    if '@version' in comment.value:
                        version_match = re.search(r'@version\s+(\S+)',
                                                  comment.value)
                        if version_match:
                            version_info = version_match.group(1)
                    if '@deprecated' in comment.value or '@breaking' in comment.value:
                        has_breaking_changes = True

        return {
            'is_public': is_public,
            'has_breaking_changes': has_breaking_changes,
            'version_info': version_info
        }

    def _analyze_js_inheritance(self, node) -> Dict:
        """Analyze JavaScript/TypeScript class inheritance"""
        inheritance_info = {
            'bases': [],
            'depth': 0,
            'multiple_inheritance': False
        }

        if hasattr(node, 'superClass'):
            if node.superClass:
                base_name = node.superClass.name if hasattr(
                    node.superClass, 'name') else str(node.superClass)
                inheritance_info['bases'].append(base_name)
                inheritance_info['depth'] = 1

        return inheritance_info

    def _analyze_js_method_complexity(self,
                                      node) -> Dict[str, ComplexityMetrics]:
        """Analyze complexity of class methods"""
        method_complexity = {}

        for child in self._walk_js_ast(node):
            if child.type == 'MethodDefinition':
                method_name = child.key.name if hasattr(
                    child.key, 'name') else str(child.key)
                method_complexity[method_name] = self._calculate_js_complexity(
                    child.value)

        return method_complexity

    def _count_js_lines(self, node) -> int:
        """Count lines of code in JavaScript/TypeScript node"""
        if hasattr(node, 'loc'):
            return node.loc.end.line - node.loc.start.line + 1
        return 1

    def analyze_file(self, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze a single file and return its structure."""
        try:
            filename = file_info.get('filename', '')
            content = file_info.get('content', '')
            
            if not filename:
                logger.error("Invalid input: filename is empty")
                return None
                
            # Get file extension
            ext = filename.split('.')[-1].lower() if '.' in filename else ''
            
            # Create default structure
            default_structure = {
                'filename': filename,
                'type': 'empty',
                'size': 0,
                'structure': {},
                'metrics': {
                    'complexity': 0,
                    'lines': 0,
                    'functions': 0,
                    'classes': 0
                }
            }
            
            if not content or not content.strip():
                logger.info(f"Skipping empty file: {filename}")
                return default_structure
            
            # Select appropriate analyzer
            if ext in ['py']:
                result = self.python_analyzer.analyze_code(content, filename)
            elif ext in ['js', 'jsx']:
                result = self.javascript_analyzer.analyze_code(content, filename)
            elif ext in ['ts', 'tsx']:
                result = self.typescript_analyzer.analyze_code(content, filename)
            else:
                logger.info(f"Unsupported file type: {ext}")
                return default_structure
                
            # Convert analyzer result to dictionary format
            if not isinstance(result, dict):
                result = {
                    'filename': filename,
                    'type': ext,
                    'size': len(content.encode('utf-8')),
                    'structure': getattr(result, 'structures', []),
                    'metrics': {
                        'complexity': getattr(result, 'total_complexity', {}).get('cyclomatic_complexity', 0),
                        'lines': len(content.splitlines()),
                        'functions': len([s for s in getattr(result, 'structures', []) if s.get('type') == 'function']),
                        'classes': len([s for s in getattr(result, 'structures', []) if s.get('type') == 'class'])
                    }
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing file: {str(e)}")
            return None
