import ast
import math
import re
import logging
import concurrent.futures
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TypedDict, Union, Set
from pathlib import Path
import tempfile
import subprocess
import json
from functools import lru_cache
import lizard
@dataclass
class LanguageConfig:
    """Configuration for language-specific analysis"""
    name: str
    extensions: Set[str]
    analyzers: List[str]
    max_line_length: int
    complexity_threshold: int
    parse_command: Optional[str] = None
    style_checker: Optional[str] = None

# Define language configurations
LANGUAGE_CONFIGS = {
    'python': LanguageConfig(
        name='Python',
        extensions={'.py', '.pyi', '.pyx'},
        analyzers=['ast', 'pylint', 'mypy'],
        max_line_length=88,  # Black formatter default
        complexity_threshold=10,
        style_checker='flake8'
    ),
    'javascript': LanguageConfig(
        name='JavaScript',
        extensions={'.js', '.jsx', '.mjs'},
        analyzers=['esprima', 'eslint'],
        max_line_length=80,
        complexity_threshold=12,
        style_checker='eslint'
    ),
    'typescript': LanguageConfig(
        name='TypeScript',
        extensions={'.ts', '.tsx'},
        analyzers=['typescript', 'eslint'],
        max_line_length=80,
        complexity_threshold=12,
        style_checker='tslint'
    )
}

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
    format='%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s'
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
        self.maintainability_index = (self.maintainability_index + other.maintainability_index) / 2

@dataclass
class AnalysisResult:
    """Result of code structure analysis"""
    structures: List[Dict]
    imports: List[str]
    total_complexity: ComplexityMetrics

class CodeStructureService:
    """Enhanced service for analyzing code structure with multi-language support"""
    
    def __init__(self):
        """Initialize the service with enhanced capabilities"""
        self.metrics_cache = {}  # Cache for analysis results
        self.language_stats = {}  # Store language detection results
        self.dependency_graph = {}  # Store dependency relationships
        self.api_stability_info = {}  # Store API stability information
        self._init_language_analyzers()
        
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
                'documentation_coverage': self._calculate_doc_coverage(result),
                'dependency_count': len(result.imports),
                'complexity_score': result.total_complexity.cyclomatic_complexity,
                'maintainability_index': result.total_complexity.maintainability_index
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

    def analyze_code(self, content: str, filename: str) -> AnalysisResult:
        """Analyze code structure with enhanced multi-language support and error handling"""
        logger.info(f"Starting analysis for file: {filename}")
        
        # Check cache first
        cache_key = self._get_cache_key(content, filename)
        if cache_key in self.metrics_cache:
            cached = self.metrics_cache[cache_key]
            if (datetime.utcnow() - cached['timestamp']).total_seconds() < 3600:  # 1 hour cache
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
                return self._empty_result()

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

            logger.info(f"Using {language_config.name} analyzer for {filename}")

            try:
                # Basic metrics using lizard
                metrics = lizard.analyze_file.analyze_source(content, language_config.name)
                
                # Language-specific analysis
                if language_config.name == 'Python':
                    result = self._analyze_python_enhanced(content, filename, metrics)
                elif language_config.name in ('JavaScript', 'TypeScript'):
                    result = self._analyze_javascript_enhanced(content, filename, metrics)
                else:
                    logger.warning(f"Falling back to basic analysis for {filename}")
                    result = self._analyze_generic(content, filename, metrics)

                # Enhance result with security and performance metrics
                result.security_metrics = self._analyze_security(content, language_config)
                result.performance_metrics = self._analyze_performance(content, language_config)

                logger.info(f"Analysis completed successfully for {filename}")
                return result

            except SyntaxError as e:
                logger.error(f"Syntax error in {filename}: {str(e)}")
                return self._empty_result()
            except Exception as e:
                logger.error(f"Error during analysis of {filename}: {str(e)}")
                return self._empty_result()

        except Exception as e:
            logger.error(f"Unexpected error analyzing {filename}: {str(e)}")
            return self._empty_result()
        finally:
            logger.info(f"Analysis finished for file: {filename}")

    def _analyze_python(self, content: str, filename: str) -> AnalysisResult:
        """Analyze Python code structure"""
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

            return AnalysisResult(
                structures=structures,
                imports=imports,
                total_complexity=total_complexity
            )
            
        except Exception as e:
            logger.error(f"Error in Python analysis for {filename}: {str(e)}")
            return self._empty_result()

    def _analyze_javascript(self, content: str, filename: str) -> AnalysisResult:
        """Analyze JavaScript/TypeScript code structure"""
        try:
            import esprima
            tree = esprima.parseModule(content, {'loc': True, 'comment': True})
            
            structures = []
            imports = []
            total_complexity = ComplexityMetrics()

            for node in self._walk_js_ast(tree):
                try:
                    if node.type in {'FunctionDeclaration', 'MethodDefinition', 'ClassDeclaration'}:
                        complexity = self._calculate_js_complexity(node)
                        total_complexity.update(complexity)
                        
                        if node.type == 'ClassDeclaration':
                            structures.append({
                                'type': 'class',
                                'name': node.id.name,
                                'complexity': complexity,
                                'methods': self._analyze_js_method_complexity(node),
                                'inheritance': self._analyze_js_inheritance(node),
                                'api_stability': self._check_js_api_stability(node)
                            })
                        else:
                            structures.append({
                                'type': 'function',
                                'name': getattr(node, 'id', {}).get('name', 'anonymous'),
                                'complexity': complexity,
                                'code_smells': self._detect_js_code_smells(node),
                                'api_stability': self._check_js_api_stability(node)
                            })
                            
                except Exception as e:
                    logger.error(f"Error analyzing JavaScript node in {filename}: {str(e)}")
                    continue

            # Find imports
            imports.extend(self._find_js_imports(tree))

            return AnalysisResult(
                structures=structures,
                imports=imports,
                total_complexity=total_complexity
            )
            
        except Exception as e:
            logger.error(f"Error in JavaScript analysis for {filename}: {str(e)}")
            return self._empty_result()

    def _calculate_complexity(self, node: Union[ast.ClassDef, ast.FunctionDef]) -> ComplexityMetrics:
        """Calculate complexity metrics for Python code"""
        cyclomatic = 1
        cognitive = 0
        current_depth = 0
        max_depth = 0
        
        for child in ast.walk(node):
            # Calculate cyclomatic complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
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
        mi = 171 - 5.2 * math.log(cognitive + 1) - 0.23 * cyclomatic - 16.2 * math.log(loc)
        mi = max(0, mi) * 100 / 171
        
        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            nesting_depth=max_depth,
            maintainability_index=round(mi, 2)
        )

    def _extract_imports(self, node: Union[ast.Import, ast.ImportFrom]) -> List[str]:
        """Extract import statements"""
        imports = []
        try:
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module if node.module else ''
                for name in node.names:
                    imports.append(f"{module}.{name.name}" if module else name.name)
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

    def _detect_code_smells(self, node: Union[ast.ClassDef, ast.FunctionDef]) -> List[CodeSmell]:
        """Detect code smells"""
        try:
            smells = []
            
            # Check function/method length
            loc = self._count_lines(node)
            if loc > 50:
                smells.append({
                    'type': 'long_function',
                    'description': f'Function/method is too long ({loc} lines)',
                    'severity': 'medium',
                    'location': f'Line {node.lineno}'
                })
            
            # Check parameter count
            if isinstance(node, ast.FunctionDef):
                args_count = len(node.args.args)
                if args_count > 5:
                    smells.append({
                        'type': 'long_parameter_list',
                        'description': f'Function has too many parameters ({args_count})',
                        'severity': 'medium',
                        'location': f'Line {node.lineno}'
                    })
            
            return smells
        except Exception as e:
            logger.error(f"Error detecting code smells: {str(e)}")
            return []

    def _check_api_stability(self, node: Union[ast.ClassDef, ast.FunctionDef]) -> APIStabilityInfo:
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
                has_breaking_changes = any(indicator in docstring for indicator in breaking_indicators)
            
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
            return {
                'bases': [],
                'depth': 0,
                'multiple_inheritance': False
            }

    def _analyze_method_complexity(self, node: ast.ClassDef) -> Dict[str, ComplexityMetrics]:
        """Analyze complexity of class methods"""
        try:
            method_complexity = {}
            
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    method_complexity[child.name] = self._calculate_complexity(child)
                    
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
        return AnalysisResult(
            structures=[],
            imports=[],
            total_complexity=ComplexityMetrics()
        )

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
            if child.type in {'IfStatement', 'WhileStatement', 'DoWhileStatement', 
                            'ForStatement', 'ForInStatement', 'ForOfStatement',
                            'ConditionalExpression', 'LogicalExpression'}:
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
        mi = 171 - 5.2 * math.log(cognitive + 1) - 0.23 * cyclomatic - 16.2 * math.log(loc)
        mi = max(0, mi) * 100 / 171
        
        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            nesting_depth=max_depth,
            maintainability_index=round(mi, 2)
        )

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
                    'description': f'Function has too many parameters ({len(params)})',
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
                        version_match = re.search(r'@version\s+(\S+)', comment.value)
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
                base_name = node.superClass.name if hasattr(node.superClass, 'name') else str(node.superClass)
                inheritance_info['bases'].append(base_name)
                inheritance_info['depth'] = 1
        
        return inheritance_info

    def _analyze_js_method_complexity(self, node) -> Dict[str, ComplexityMetrics]:
        """Analyze complexity of class methods"""
        method_complexity = {}
        
        for child in self._walk_js_ast(node):
            if child.type == 'MethodDefinition':
                method_name = child.key.name if hasattr(child.key, 'name') else str(child.key)
                method_complexity[method_name] = self._calculate_js_complexity(child.value)
        
        return method_complexity

    def _count_js_lines(self, node) -> int:
        """Count lines of code in JavaScript/TypeScript node"""
        if hasattr(node, 'loc'):
            return node.loc.end.line - node.loc.start.line + 1
        return 1