import re
import logging
import functools
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable, TypeVar, ParamSpec, Tuple
from enum import Enum
import traceback
import os
from logging_config import setup_logging, get_logger
from github import Github, Repository, ContentFile, RateLimitExceededException, Auth
from config.github_config import get_github_token
import time
import json
from datetime import datetime
import tempfile
from pathlib import Path

# Configure component-specific logging
logger = get_logger(__name__, "typescript_analyzer")

# Type variables for decorator
P = ParamSpec('P')
T = TypeVar('T')

def log_method_call(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator to log method calls with parameters and return values."""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            logger.info("Method call started", 
                       extra={
                           "method": func.__name__, 
                           "args": str(args[1:]), 
                           "kwargs": str(kwargs)
                       })
            result = func(*args, **kwargs)
            logger.info("Method call completed", 
                       extra={
                           "method": func.__name__, 
                           "status": "success"
                       })
            return result
        except Exception as e:
            logger.error("Method call failed",
                        extra={
                            "method": func.__name__,
                            "status": "error",
                            "error": str(e),
                            "args": str(args[1:]),
                            "kwargs": str(kwargs),
                            "traceback": traceback.format_exc()
                        })
            raise
    return wrapper

@dataclass
class CodeSample:
    """A code sample with context and metadata."""
    original: str
    line_number: int
    context: str = ""

@dataclass
class CodeExample:
    """A code example with title, location, and suggestion."""
    title: str = ""
    code: str = ""
    location: str = ""
    suggestion: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary with safe string handling."""
        try:
            return {
                'title': str(self.title) if self.title else '',
                'code': str(self.code) if self.code else '',
                'location': str(self.location) if self.location else '',
                'suggestion': str(self.suggestion) if self.suggestion else ''
            }
        except Exception as e:
            logger.error(f"Error converting CodeExample to dict: {str(e)}")
            return {
                'title': '',
                'code': '',
                'location': '',
                'suggestion': ''
            }

class AnalysisError(Exception):
    """Custom exception for analysis errors."""
    pass

@dataclass
class QualityGate:
    """Quality gate configuration for TypeScript analysis."""
    name: str
    threshold: float
    actual: float
    status: bool

@dataclass
class TypeMetrics:
    """Metrics for type analysis"""
    type_coverage: float = 0.0
    interfaces: int = 0
    type_aliases: int = 0
    utility_types: int = 0
    type_guards: int = 0
    type_assertions: int = 0
    total_declarations: int = 0
    any_types: int = 0
    explicit_types: int = 0
    untyped: int = 0
    declaration_file_coverage: float = 0.0
    test_file_coverage: float = 0.0
    implementation_coverage: float = 0.0
    declaration_any_types: int = 0
    implementation_any_types: int = 0
    test_assertions: int = 0
    generics: int = 0
    mapped_types: int = 0
    conditional_types: int = 0

    def __post_init__(self):
        # Ensure all counts are initialized to 0 if not set
        for field_name, field_type in self.__annotations__.items():
            if isinstance(field_type, type) and issubclass(field_type, (int, float)):
                if getattr(self, field_name) is None:
                    setattr(self, field_name, 0 if field_type is int else 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a dictionary."""
        return asdict(self)

@dataclass
class DocumentationMetrics:
    """Metrics for documentation analysis"""
    coverage: float = 0.0
    jsdoc_coverage: float = 0.0
    param_docs: int = 0
    return_docs: int = 0
    interface_docs: int = 0
    class_docs: int = 0
    total_jsdoc_comments: int = 0

@dataclass
class FrameworkMetrics:
    """Metrics for framework analysis."""
    framework_name: str
    framework_score: float
    component_count: int
    hook_count: int
    state_management_count: int

@dataclass
class DocumentationAnalysis:
    """Analysis results for documentation coverage."""
    metrics: DocumentationMetrics
    examples: List[CodeExample] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    quality_improvements: List[Dict[str, str]] = field(default_factory=list)
    issues: List[Dict[str, str]] = field(default_factory=list)
    quality_gates: List[QualityGate] = field(default_factory=list)
    action_items: Dict[str, List[dict]] = field(default_factory=lambda: {"critical": [], "high": [], "medium": []})
    best_practices: Dict[str, List[str]] = field(default_factory=lambda: {"strong_areas": [], "needs_improvement": []})
    samples: List[CodeSample] = field(default_factory=list)

@dataclass
class TypeAnalysis:
    """Analysis results for type system usage."""
    metrics: TypeMetrics
    code_samples: List[str] = None
    suggestions: List[str] = None
    quality_gates: List[QualityGate] = field(default_factory=list)

    def __post_init__(self):
        self.code_samples = self.code_samples or []
        self.suggestions = self.suggestions or []

@dataclass
class FrameworkAnalysis:
    """Analysis results for framework detection."""
    framework: str
    patterns: Dict[str, int]
    examples: List[CodeExample] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list) 

@dataclass
class AnalysisOutput:
    """Output of TypeScript analysis."""
    type_analysis: TypeAnalysis
    doc_analysis: DocumentationAnalysis
    framework_analysis: FrameworkAnalysis
    quality_gates: List[QualityGate] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    best_practices: Dict[str, List[str]] = field(default_factory=lambda: {"strong_areas": [], "needs_improvement": []})
    quality_score: float = 0.0

    def _safe_convert_metrics(self, metrics: Any, name: str) -> Dict[str, Any]:
        """Safely convert metrics to dictionary."""
        try:
            return asdict(metrics) if metrics else {}
        except Exception as e:
            logger.error(f"Error converting {name} metrics to dict: {str(e)}")
            return {}

    def _safe_convert_examples(self, examples: List[CodeExample], name: str) -> List[Dict[str, str]]:
        """Safely convert examples to dictionary list."""
        try:
            return [ex.to_dict() for ex in (examples or [])]
        except Exception as e:
            logger.error(f"Error converting {name} examples to dict: {str(e)}")
            return []

    def _safe_convert_quality_gates(self, gates: List[QualityGate], name: str) -> List[Dict[str, Any]]:
        """Safely convert quality gates to dictionary list."""
        try:
            return [asdict(gate) for gate in (gates or [])]
        except Exception as e:
            logger.error(f"Error converting {name} quality gates to dict: {str(e)}")
            return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis results to a dictionary format."""
        try:
            framework_dict = {}
            if self.framework_analysis:
                framework_dict = {
                    'framework': self.framework_analysis.framework,
                    'patterns': self.framework_analysis.patterns,
                    'examples': self._safe_convert_examples(self.framework_analysis.examples, 'framework'),
                    'suggestions': self.framework_analysis.suggestions
                }

            return {
                'type_analysis': {
                    'metrics': self._safe_convert_metrics(self.type_analysis.metrics, 'type'),
                    'code_samples': self.type_analysis.code_samples,
                    'suggestions': self.type_analysis.suggestions,
                    'quality_gates': self._safe_convert_quality_gates(self.type_analysis.quality_gates, 'type')
                },
                'doc_analysis': {
                    'metrics': self._safe_convert_metrics(self.doc_analysis.metrics, 'doc'),
                    'examples': self._safe_convert_examples(self.doc_analysis.examples, 'doc'),
                    'suggestions': self.doc_analysis.suggestions,
                    'quality_improvements': self.doc_analysis.quality_improvements,
                    'issues': self.doc_analysis.issues,
                    'quality_gates': self._safe_convert_quality_gates(self.doc_analysis.quality_gates, 'doc'),
                    'action_items': self.doc_analysis.action_items,
                    'best_practices': self.doc_analysis.best_practices,
                    'samples': [sample.__dict__ for sample in self.doc_analysis.samples]
                },
                'framework_analysis': framework_dict,
                'quality_gates': self._safe_convert_quality_gates(self.quality_gates, 'overall'),
                'action_items': self.action_items,
                'best_practices': self.best_practices,
                'quality_score': self.quality_score
            }
        except Exception as e:
            logger.error("Error converting analysis to dict: " + str(e),
                        extra={
                            'traceback': traceback.format_exc()
                        })
            return {}

class FrameworkType(Enum):
    """Supported framework types"""
    REACT = "react"
    NEXTJS = "nextjs"
    ANGULAR = "angular"
    VUE = "vue"

class TypeScriptAnalyzer:
    """Enhanced TypeScript code analyzer with GitHub support"""
    
    def __init__(self, pr_url: Optional[str] = None, user_id: Optional[str] = None, github_token: Optional[str] = None):
        # Initialize logging
        setup_logging(
            component="typescript_analyzer",
            log_level="DEBUG",
            log_to_console=True
        )
        
        # Set analysis context
        self.logger = get_logger(__name__, "typescript_analyzer")
        self.logger.set_context(
            analyzer="typescript",
            pr_url=pr_url,
            user_id=user_id,
            language="typescript"
        )
        self.logger.info("Initializing TypeScript analyzer", 
                        extra={
                            "analyzer": "typescript",
                            "pr_url": pr_url,
                            "user_id": user_id,
                            "language": "typescript"
                        })
        
        # Initialize patterns
        self.patterns = self._compile_patterns()
        
        # Initialize GitHub client
        self.github = None
        self.github_config = {
            'rate_limit': {
                'max_retries': 3,
                'retry_delay': 1
            },
            'timeout': 10,
            'verify_ssl': True
        }
        self._init_github_client(github_token)

    @log_method_call
    def _init_github_client(self, github_token: Optional[str] = None):
        """Initialize GitHub client with token and configuration"""
        # Use provided token or get from environment
        token = github_token or get_github_token()
        
        if not token:
            self.logger.warning("No valid GitHub token provided", 
                                extra={
                                    "token": token
                                })
            return
        
        try:
            # Initialize GitHub client with configuration
            self.github = Github(
                auth=Auth.Token(token),
                timeout=self.github_config['timeout'],
                verify=self.github_config['verify_ssl']
            )
            # Test the connection
            self.github.get_user().login
        except Exception as e:
            self.logger.error(f"Failed to initialize GitHub client: {str(e)}", 
                              extra={
                                  "error": str(e)
                              })
            self.github = None
    
    @log_method_call
    def analyze_github_repo(self, repo_url: str, branch: str = "main") -> Dict[str, Any]:
        """Analyze TypeScript files in a GitHub repository"""
        if not self.github:
            raise ValueError("GitHub token not provided or invalid. Cannot analyze repository.")
            
        try:
            # Extract owner and repo name from URL
            owner, repo_name = self._parse_github_url(repo_url)
            
            # Get repository with retry logic
            repo = self._get_repo_with_retry(f"{owner}/{repo_name}")
            
            # Get all TypeScript files
            ts_files = self._get_typescript_files(repo, branch)
            
            # Analyze each file
            files_to_analyze = []
            for file in ts_files:
                try:
                    content = self._get_file_content_with_retry(file)
                    if content:
                        files_to_analyze.append({
                            'filename': file.path,
                            'content': content
                        })
                except Exception as e:
                    self.logger.error(f"Error reading file {file.path}: {str(e)}", 
                                      extra={
                                          "error": str(e),
                                          "file_path": file.path
                                      })
                    
            # Run analysis
            return self.analyze_files(files_to_analyze).to_dict()
            
        except Exception as e:
            self.logger.error(f"Error analyzing repository: {str(e)}", 
                              extra={
                                  "error": str(e)
                              })
            raise
            
    @log_method_call
    def _get_repo_with_retry(self, repo_full_name: str) -> Repository:
        """Get repository with rate limit handling and retry logic"""
        max_retries = self.github_config['rate_limit']['max_retries']
        retry_delay = self.github_config['rate_limit']['retry_delay']
        
        for attempt in range(max_retries):
            try:
                return self.github.get_repo(repo_full_name)
            except RateLimitExceededException:
                if attempt == max_retries - 1:
                    raise  # Re-raise on last attempt
                
                # Wait for rate limit reset
                reset_time = self.github.rate_limiting_resettime
                wait_time = max(0, reset_time - time.time())
                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    time.sleep(retry_delay)
            except Exception as e:
                self.logger.error(f"Error getting repository: {str(e)}", 
                                  extra={
                                      "error": str(e)
                                  })
                raise
        
        raise RuntimeError("Max retries exceeded while getting repository")

    @log_method_call
    def _get_file_content_with_retry(self, file: ContentFile) -> Optional[str]:
        """Get file content with rate limit handling and retry logic"""
        max_retries = self.github_config['rate_limit']['max_retries']
        retry_delay = self.github_config['rate_limit']['retry_delay']
        
        for attempt in range(max_retries):
            try:
                if not file or not hasattr(file, 'decoded_content'):
                    return None
                content = file.decoded_content
                return content.decode('utf-8') if content else None
            except RateLimitExceededException:
                if attempt == max_retries - 1:
                    raise  # Re-raise on last attempt
                
                # Wait for rate limit reset
                reset_time = self.github.rate_limiting_resettime
                wait_time = max(0, reset_time - time.time())
                if wait_time > 0:
                    time.sleep(wait_time)
                else:
                    time.sleep(retry_delay)
            except Exception as e:
                self.logger.error(f"Error getting file content: {str(e)}", 
                                  extra={
                                      "error": str(e)
                                  })
                return None
        
        return None

    def _analyze_code_quality(self, content: str) -> Dict[str, Any]:
        """Analyze code quality metrics."""
        try:
            score = 100.0
            issues = []
            complex_functions = []
            
            # Check for long functions
            functions = list(re.finditer(r'function\s+\w+\s*{([^}]*)}', content))
            for func in functions:
                func_body = func.group(1)
                lines = func_body.count('\n')
                if lines > 30:
                    score -= 5.0
                    complex_functions.append({
                        'name': 'Long Function',
                        'content': func_body
                    })
            
            # Check for nested callbacks
            if content.count('callback(') > 3:
                score -= 10.0
                issues.append('Too many nested callbacks')
            
            # Check for magic numbers
            magic_numbers = len(list(re.finditer(r'\b\d+\b(?!\s*[x\/%\+\-\*])', content)))
            if magic_numbers > 5:
                score -= 5.0
                issues.append('Too many magic numbers')
            
            return {
                'score': max(0.0, score),
                'issues': issues,
                'complex_functions': complex_functions
            }
            
        except Exception as e:
            self.logger.error(f"Error in _analyze_code_quality: {str(e)}")
            return {'score': 0.0, 'issues': [], 'complex_functions': []}

    def analyze_directory(self, directory_path: str) -> Dict[str, Any]:
        """Analyze TypeScript files in a directory."""
        try:
            # Find all TypeScript files
            typescript_files = []
            for root, _, files in os.walk(directory_path):
                for file in files:
                    if file.endswith(('.ts', '.tsx', '.d.ts')):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            typescript_files.append({
                                'path': os.path.relpath(file_path, directory_path),
                                'content': content
                            })
            
            # Group files by type
            declaration_files = []
            test_files = []
            implementation_files = []
            
            for file_info in typescript_files:
                file_path = file_info['path']
                if file_path.endswith('.d.ts'):
                    declaration_files.append(file_info)
                elif any(pattern in file_path for pattern in ['.test.', '-test.', '-tests.', '.spec.']):
                    test_files.append(file_info)
                else:
                    implementation_files.append(file_info)
            
            self.logger.info(
                f"Found {len(declaration_files)} declaration files, "
                f"{len(test_files)} test files, and "
                f"{len(implementation_files)} implementation files",
                extra={
                    "declaration_files": len(declaration_files), 
                    "test_files": len(test_files), 
                    "implementation_files": len(implementation_files)
                }
            )
            
            # Analyze files
            analysis = self.analyze_files([
                *declaration_files,
                *implementation_files,
                *test_files
            ])
            
            # Convert to dictionary
            return analysis.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error analyzing directory {directory_path}: {str(e)}", 
                              extra={
                                  "error": str(e),
                                  "directory_path": directory_path
                              })
            return self._create_empty_analysis().to_dict()

    def analyze_files(self, file_paths: List[Dict[str, str]]) -> AnalysisOutput:
        """Analyze TypeScript files and generate comprehensive metrics."""
        try:
            # Initialize metrics
            type_metrics = TypeMetrics()
            doc_metrics = DocumentationMetrics()
            
            total_coverage = 0
            total_files = len(file_paths)
            
            # Group files by type
            declaration_files = []
            test_files = []
            implementation_files = []
            
            for file_info in file_paths:
                file_path = file_info.get('path', '')
                content = file_info.get('content', '')
                
                # Determine file type
                if file_path.endswith('.d.ts'):
                    declaration_files.append(file_info)
                elif any(pattern in file_path for pattern in ['.test.', '-test.', '-tests.', '.spec.']):
                    test_files.append(file_info)
                else:
                    implementation_files.append(file_info)
                
                # Count type-related features
                type_metrics.type_assertions += len(list(self.patterns['type_assertions'].finditer(content)))
                type_metrics.type_guards += len(list(self.patterns['type_guards'].finditer(content)))
                type_metrics.mapped_types += len(list(self.patterns['mapped_types'].finditer(content)))
                type_metrics.conditional_types += len(list(self.patterns['conditional_types'].finditer(content)))
                type_metrics.utility_types += len(list(self.patterns['utility_types'].finditer(content)))
                type_metrics.total_declarations += len(list(self.patterns['declarations'].finditer(content)))
                type_metrics.interfaces += len(list(self.patterns['interfaces'].finditer(content)))
                type_metrics.type_aliases += len(list(self.patterns['type_aliases'].finditer(content)))
                type_metrics.generics += len(list(self.patterns['generics'].finditer(content)))
                
                # Calculate type coverage for this file
                file_coverage = self._calculate_type_coverage(content)
                total_coverage += file_coverage
                
                # Analyze documentation
                doc_metrics.total_jsdoc_comments += len(list(re.finditer(r'/\*\*[\s\S]*?\*/', content)))
                doc_metrics.param_docs += len(list(re.finditer(r'@param\s+(?:\{[^}]+\})?\s*\w+[^-]', content)))
                doc_metrics.return_docs += len(list(re.finditer(r'@returns?\s+(?:\{[^}]+\})?', content)))
                doc_metrics.interface_docs += len(list(re.finditer(r'/\*\*[\s\S]*?\*/\s*interface\s+\w+', content)))
                doc_metrics.class_docs += len(list(re.finditer(r'/\*\*[\s\S]*?\*/\s*class\s+\w+', content)))
            
            # Calculate averages and coverage
            if total_files > 0:
                type_metrics.type_coverage = total_coverage / total_files
                
                # Calculate file type coverage
                if declaration_files:
                    type_metrics.declaration_file_coverage = 100.0
                if test_files:
                    type_metrics.test_file_coverage = 100.0
                if implementation_files:
                    type_metrics.implementation_coverage = total_coverage / len(implementation_files)
                
                # Calculate documentation coverage
                total_items = type_metrics.interfaces + type_metrics.total_declarations
                if total_items > 0:
                    doc_metrics.coverage = (doc_metrics.total_jsdoc_comments / total_items) * 100
            
            return AnalysisOutput(
                type_analysis=TypeAnalysis(metrics=type_metrics),
                doc_analysis=DocumentationAnalysis(metrics=doc_metrics),
                framework_analysis=None
            )
        except Exception as e:
            self.logger.error("Error analyzing files", 
                            extra={
                                "error": str(e)
                            })
            return self._create_empty_analysis()

    def _determine_file_type(self, file_path: str) -> str:
        """Determine the type of TypeScript file."""
        if file_path.endswith('.d.ts'):
            return 'declaration'
        elif any(pattern in file_path for pattern in ['.test.', '-test.', '-tests.', '.spec.']):
            return 'test'
        return 'implementation'

    def _analyze_types(self, content: str, file_type: str = 'implementation') -> TypeAnalysis:
        """
        Analyze TypeScript types in content.
        
        Args:
            content: The TypeScript code content to analyze
            file_type: The type of file being analyzed (implementation, declaration, or test)
            
        Returns:
            TypeAnalysis with type metrics and suggestions
        """
        try:
            metrics = TypeMetrics()
            code_samples = []
            suggestions = []
            
            # Count total declarations
            total_declarations = 0
            typed_declarations = 0
            
            # Count interface declarations (each property is a typed declaration)
            interface_matches = list(self.patterns['interfaces'].finditer(content))
            for match in interface_matches:
                # Find properties in interface
                interface_text = content[match.start():].split('}')[0]
                # Updated regex to better match interface properties
                properties = re.findall(r'(?:\/\*\*[^*]*\*+(?:[^/*][^*]*\*+)*\/\s*)?[\w]+\s*:\s*[^;,\n]+', interface_text)
                typed_declarations += len(properties)
                total_declarations += len(properties)

            # Count type aliases (each is a typed declaration)
            type_alias_matches = list(self.patterns['type_aliases'].finditer(content))
            typed_declarations += len(type_alias_matches)
            total_declarations += len(type_alias_matches)

            # Count function parameters with type annotations
            func_param_types = re.finditer(r'(?:function\s+\w+\s*\(|\(\s*)([^)]*)\)', content)
            for match in func_param_types:
                params = match.group(1).split(',')
                for param in params:
                    if param.strip():
                        total_declarations += 1
                        if ':' in param:
                            typed_declarations += 1

            # Count variable declarations
            var_decls = re.finditer(r'(?:const|let|var)\s+(\w+)(?:\s*:\s*([^=\s]+))?(?:\s*=\s*)?', content)
            for match in var_decls:
                total_declarations += 1
                if match.group(2):  # Has type annotation
                    typed_declarations += 1

            # Calculate coverage
            if total_declarations > 0:
                metrics.type_coverage = (typed_declarations / total_declarations) * 100.0
                metrics.explicit_types = typed_declarations
                metrics.untyped = total_declarations - typed_declarations
            else:
                metrics.type_coverage = 100.0  # If no declarations, consider it fully typed
            
            # Add suggestions based on metrics
            if metrics.type_coverage < 80:
                suggestions.append("Increase type coverage to at least 80% by adding explicit type annotations")
            
            if metrics.any_types > 0:
                suggestions.append("Replace 'any' types with more specific type annotations")
            
            if metrics.type_assertions > metrics.total_declarations * 0.1:
                suggestions.append("Reduce the use of type assertions by using proper type definitions")
            
            return TypeAnalysis(
                metrics=metrics,
                code_samples=code_samples,
                suggestions=suggestions
            )
            
        except Exception as e:
            self.logger.error("Error in analyze_types", 
                              extra={
                                  "error": str(e)
                              })
            return TypeAnalysis(metrics=TypeMetrics(), code_samples=[], suggestions=[])

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for TypeScript analysis."""
        try:
            return {
                'imports': re.compile(r'import\s+.*?\s+from\s+[\'"].*?[\'"]'),
                'exports': re.compile(r'export\s+(?:default\s+)?(?:const|let|var|function|class|interface|type)\s+\w+'),
                'declarations': re.compile(r'(?:interface|type|declare)\s+\w+'),
                'functions': re.compile(r'function\s+\w+\s*\([^)]*\)'),
                'classes': re.compile(r'class\s+\w+'),
                'type_annotations': re.compile(r':\s*[A-Za-z][\w\.<>|&\[\]]*'),
                'type_assertions': re.compile(r'(?:as\s+[\w\.<>|&\[\]]+|<[\w\.<>|&\[\]]+>)'),
                'type_guards': re.compile(r'(?:function\s+\w+\([^)]*\):\s*[^{]+?\s+is\s+[^{]*{[^}]*}|is\s+[^{]*{[^}]*})'),
                'mapped_types': re.compile(r'type\s+\w+(?:<[^>]+>)?\s*=\s*\{\s*(?:readonly\s+)?\[\s*[KP]\s+in\s+(?:keyof\s+)?\w+[^\}]*\}'),
                'conditional_types': re.compile(r'type\s+\w+\s*[<[].+?[>\]]\s*=\s*.+?\s+extends\s+.+?\s*\?\s*.+?\s*:\s*.+'),
                'utility_types': re.compile(r'(?:Partial|Readonly|Record|Pick|Omit|Exclude|Extract|NonNullable|Parameters|ConstructorParameters|ReturnType|InstanceType|Required|ThisParameterType|OmitThisParameter|ThisType|Uppercase|Lowercase|Capitalize|Uncapitalize)<'),
                'any_type': re.compile(r':\s*any\b'),
                'explicit_types': re.compile(r'(?:const|let|var)\s+\w+\s*:\s*[A-Za-z][\w\.<>|&\[\]]*'),
                'generics': re.compile(r'<[^>]+>'),
                'interfaces': re.compile(r'interface\s+\w+'),
                'type_aliases': re.compile(r'type\s+\w+\s*[<[=]')
            }
        except Exception as e:
            self.logger.error("Error compiling TypeScript patterns", 
                            extra={
                                "error": str(e)
                            })
            return {}

    def _calculate_type_coverage(self, content: str) -> float:
        """Calculate type coverage percentage."""
        try:
            total_declarations = 0
            typed_declarations = 0
            
            # Special handling for declaration files (.d.ts)
            if ('declare module' in content or 
                content.strip().startswith('declare ') or 
                'declare namespace' in content):
                return 100.0  # Declaration files are always fully typed

            # Count interface declarations and properties
            interface_matches = list(self.patterns['interfaces'].finditer(content))
            for match in interface_matches:
                # Count interface itself as typed
                typed_declarations += 1
                total_declarations += 1
                
                # Get interface text and find properties
                interface_text = content[match.start():].split('}')[0]
                properties = re.findall(r'\b\w+\s*:\s*[^;,\n]+', interface_text)
                # All interface properties are typed by definition
                typed_declarations += len(properties)
                total_declarations += len(properties)

            # Count variable declarations with type annotations or initialized with typed values
            var_declarations = re.finditer(r'(?:const|let|var)\s+(\w+)(?:\s*:\s*([^=\s]+))?(?:\s*=\s*(.+?))?(?:;|$)', content)
            for decl in var_declarations:
                total_declarations += 1
                has_type_annotation = bool(decl.group(2))  # Has explicit type
                has_typed_init = False
                
                if decl.group(3):  # Has initializer
                    init_value = decl.group(3).strip()
                    has_typed_init = (
                        re.search(r':\s*\w+\s*=\s*{', decl.group(0)) or  # Typed object literal
                        re.search(r'as\s+const\b', init_value) or  # const assertion
                        re.search(r'<[^>]+>', init_value)  # Generic type
                    )
                
                if has_type_annotation or has_typed_init:
                    typed_declarations += 1

            # Count function declarations with type annotations
            func_matches = re.finditer(r'function\s+\w+\s*\((.*?)\)(?:\s*:\s*([^{]+))?', content)
            for match in func_matches:
                # Count function itself
                total_declarations += 1
                # Check return type
                if match.group(2):  # Has return type
                    typed_declarations += 1
                
                # Count parameters
                params_text = match.group(1).strip()
                if params_text:
                    params = [p.strip() for p in params_text.split(',')]
                    for param in params:
                        if param:
                            total_declarations += 1
                            if ':' in param:  # Parameter has type annotation
                                typed_declarations += 1

            # Calculate coverage
            if total_declarations > 0:
                coverage = (typed_declarations / total_declarations) * 100.0
                return min(coverage, 100.0)  # Cap at 100%
            return 100.0  # Empty files are considered fully typed
        
        except Exception as e:
            logger.error("Error calculating type coverage", 
                        extra={"error": str(e)})
            return 0.0

    def analyze_file(self, content: str, file_path: str) -> AnalysisOutput:
        """Analyze a TypeScript file and return comprehensive analysis results."""
        try:
            # Analyze types
            type_analysis = self._analyze_types(content)
            
            # Analyze documentation
            doc_analysis = self._analyze_documentation(content)
            
            # Detect framework usage
            framework_analysis = self._detect_framework(content, file_path)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(type_analysis, doc_analysis)
            
            return AnalysisOutput(
                type_analysis=type_analysis,
                doc_analysis=doc_analysis,
                framework_analysis=framework_analysis,
                quality_score=quality_score
            )
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {str(e)}", 
                              extra={
                                  "error": str(e),
                                  "file_path": file_path
                              })
            return self._create_empty_analysis()

    def _detect_framework(self, content: str, file_path: str) -> Optional[FrameworkAnalysis]:
        """
        Detect which framework the TypeScript file is using.
        
        Args:
            content: The file content
            file_path: Path to the file
            
        Returns:
            FrameworkAnalysis with detected framework and patterns
        """
        patterns = self._compile_framework_patterns()
        
        # Count pattern matches for each framework
        framework_matches = {}
        for framework_type, framework_patterns in patterns.items():
            pattern_counts = {
                pattern_name: len(list(pattern.finditer(content)))
                for pattern_name, pattern in framework_patterns.items()
            }
            framework_matches[framework_type] = pattern_counts
        
        # Determine the most likely framework based on pattern matches
        max_matches = 0
        detected_framework = None
        for framework_type, counts in framework_matches.items():
            total_matches = sum(counts.values())
            if total_matches > max_matches:
                max_matches = total_matches
                detected_framework = framework_type
        
        if detected_framework and max_matches > 0:
            return FrameworkAnalysis(
                framework=detected_framework,
                patterns=framework_matches[detected_framework],
                examples=[],
                suggestions=[]
            )
        
        return None

    def _calculate_quality_score(self, type_analysis: TypeAnalysis, doc_analysis: DocumentationAnalysis) -> float:
        """Calculate overall code quality score."""
        try:
            # Type system usage score (40% weight)
            type_score = (
                (type_analysis.metrics.type_coverage * 0.4) +
                (type_analysis.metrics.implementation_coverage * 0.3) +
                ((1 - min(type_analysis.metrics.any_types / max(type_analysis.metrics.total_declarations, 1), 1)) * 0.3)
            ) * 0.4

            # Documentation score (40% weight)
            doc_score = (
                (doc_analysis.metrics.coverage * 0.5) +
                (doc_analysis.metrics.total_jsdoc_comments * 0.5)
            ) * 0.4

            # Best practices score (20% weight)
            best_practices_score = (
                (type_analysis.metrics.type_guards / max(type_analysis.metrics.total_declarations, 1) * 0.3) +
                (type_analysis.metrics.explicit_types / max(type_analysis.metrics.total_declarations, 1) * 0.4) +
                ((1 - type_analysis.metrics.type_assertions / max(type_analysis.metrics.total_declarations, 1)) * 0.3)
            ) * 0.2

            # Combine scores
            total_score = type_score + doc_score + best_practices_score
            
            # Ensure score is between 0 and 1
            return max(0.0, min(1.0, total_score))
        except Exception as e:
            self.logger.error(f"Error calculating quality score: {str(e)}", 
                              extra={
                                  "error": str(e)
                              })
            return 0.0

    def _create_empty_analysis(self) -> AnalysisOutput:
        """Create an empty analysis result."""
        try:
            # Initialize metrics
            type_metrics = TypeMetrics()
            doc_metrics = DocumentationMetrics()
            framework_metrics = FrameworkMetrics(
                framework_name="",
                framework_score=0.0,
                component_count=0,
                hook_count=0,
                state_management_count=0
            )
            
            # Initialize analysis objects with empty metrics
            type_analysis = TypeAnalysis(
                metrics=type_metrics,
                code_samples=[],
                suggestions=[]
            )
            
            doc_analysis = DocumentationAnalysis(
                metrics=doc_metrics,
                examples=[],
                suggestions=[],
                quality_improvements=[],
                issues=[],
                quality_gates=[],
                action_items={"critical": [], "high": [], "medium": []},
                best_practices={"strong_areas": [], "needs_improvement": []},
                samples=[]
            )
            
            framework_analysis = FrameworkAnalysis(
                framework="",
                patterns={},
                examples=[],
                suggestions=[]
            )
            
            # Create and return the complete analysis output
            return AnalysisOutput(
                type_analysis=type_analysis,
                doc_analysis=doc_analysis,
                framework_analysis=framework_analysis,
                quality_gates=[],
                action_items=[],
                best_practices={"strong_areas": [], "needs_improvement": []},
                quality_score=0.0
            )
        except Exception as e:
            self.logger.error(f"Error creating empty analysis: {str(e)}", 
                              extra={
                                  "error": str(e)
                              })
            raise

    def _analyze_documentation(self, content: str) -> DocumentationAnalysis:
        """
        Analyze TypeScript documentation.
        
        Args:
            content: The TypeScript code content to analyze
            
        Returns:
            DocumentationAnalysis with documentation metrics and suggestions
        """
        metrics = DocumentationMetrics()
        examples = []
        suggestions = []
        quality_improvements = []
        
        # Count JSDoc comments
        jsdoc_matches = re.finditer(r'/\*\*[\s\S]*?\*/', content)
        metrics.total_jsdoc_comments = sum(1 for _ in jsdoc_matches)
        
        # Count param and return documentation
        param_matches = re.finditer(r'@param\s+(?:\{[^}]+\})?\s*\w+[^-]', content)
        metrics.param_docs = sum(1 for _ in param_matches)
        
        return_matches = re.finditer(r'@returns?\s+(?:\{[^}]+\})?', content)
        metrics.return_docs = sum(1 for _ in return_matches)
        
        # Count interface and class documentation
        interface_matches = re.finditer(r'/\*\*[\s\S]*?\*/\s*interface\s+\w+', content)
        metrics.interface_docs = sum(1 for _ in interface_matches)
        
        class_matches = re.finditer(r'/\*\*[\s\S]*?\*/\s*class\s+\w+', content)
        metrics.class_docs = sum(1 for _ in class_matches)
        
        # Calculate coverage
        total_items = len(re.findall(r'(?:interface|class|function|const\s+\w+\s*=\s*(?:async\s+)?function|\w+\s*:\s*function)\s+\w+', content))
        documented_items = metrics.total_jsdoc_comments
        metrics.coverage = (documented_items / total_items * 100) if total_items > 0 else 0
        
        # Add quality gates
        quality_gates = [
            QualityGate("Documentation Coverage", 80.0, metrics.coverage, metrics.coverage >= 80.0),
            QualityGate("JSDoc Comments", 5, metrics.total_jsdoc_comments, metrics.total_jsdoc_comments >= 5),
            QualityGate("Parameter Documentation", 3, metrics.param_docs, metrics.param_docs >= 3)
        ]
        
        # Add suggestions for improvement
        if metrics.coverage < 80:
            quality_improvements.append({
                'type': 'documentation_coverage',
                'message': 'Documentation coverage is below 80%. Consider adding JSDoc comments to undocumented items.',
                'severity': 'high'
            })
        
        if metrics.param_docs < metrics.total_jsdoc_comments * 0.5:
            quality_improvements.append({
                'type': 'param_documentation',
                'message': 'Many functions lack parameter documentation. Add @param tags with descriptions.',
                'severity': 'medium'
            })
        
        if metrics.return_docs < metrics.total_jsdoc_comments * 0.5:
            quality_improvements.append({
                'type': 'return_documentation',
                'message': 'Many functions lack return value documentation. Add @returns tags with descriptions.',
                'severity': 'medium'
            })
        
        return DocumentationAnalysis(
            metrics=metrics,
            examples=examples,
            suggestions=suggestions,
            quality_improvements=quality_improvements,
            quality_gates=quality_gates
        )
