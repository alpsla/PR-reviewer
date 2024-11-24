# plugins/documentation_parser.py
from typing import Dict, Any, Optional, List
import ast
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentationError(Exception):
    """Custom exception for documentation parsing errors"""
    pass

class DocumentationParser:
    """Parser for code documentation with multi-language support"""
    
    def __init__(self):
        """Initialize the documentation parser plugin."""
        self.initialized = False
        self._cache = {}
        self.supported_languages = {
            '.py': self._parse_python_docs,
            '.js': self._parse_jsdoc,
            '.jsx': self._parse_jsdoc,
            '.ts': self._parse_jsdoc,
            '.tsx': self._parse_jsdoc
        }
        
    @property
    def name(self) -> str:
        return "documentation_parser"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    def initialize(self) -> None:
        """Initialize documentation parser."""
        try:
            self.initialized = True
            logger.info("Documentation parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize documentation parser: {str(e)}")
            raise DocumentationError(f"Parser initialization failed: {str(e)}")
        
    def execute_sync(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse documentation from provided code files.
        
        Args:
            context: Dictionary containing files to analyze and other context
                    Expected format: {'files': [{'filename': str, 'content': str}]}
                    
        Returns:
            Dict containing documentation analysis results and statistics
            Format: {
                'documentation': Dict[str, Dict],  # Per-file documentation info
                'stats': Dict[str, Any]  # Overall statistics
            }
            
        Raises:
            DocumentationError: If parsing fails or files are invalid
        """
        if not self.initialized:
            raise DocumentationError("Documentation parser not initialized")
            
        try:
            files = context.get('files', [])
            if not files:
                raise DocumentationError("No files provided for documentation analysis")
                
            results = {}
            total_files = len(files)
            
            for index, file in enumerate(files):
                filename = file.get('filename', '')
                content = file.get('content', '')
                
                if not filename or not content:
                    continue
                    
                # Check cache
                cache_key = f"{filename}:{hash(content)}"
                if cache_key in self._cache:
                    results[filename] = self._cache[cache_key]
                    continue
                    
                # Parse documentation
                ext = Path(filename).suffix.lower()
                parser = self.supported_languages.get(ext)
                
                if parser:
                    try:
                        doc_info = parser(content)
                        results[filename] = doc_info
                        self._cache[cache_key] = doc_info
                    except Exception as e:
                        logger.error(f"Failed to parse documentation in {filename}: {str(e)}")
                        results[filename] = {'error': str(e)}
                else:
                    logger.warning(f"No parser available for file extension: {ext}")
                    results[filename] = {
                        'error': 'Unsupported file type',
                        'module_doc': None,
                        'classes': {},
                        'functions': {},
                        'coverage': 0.0,
                        'quality_score': 0.0
                    }
                        
            return {
                'documentation': results,
                'stats': self._calculate_stats(results)
            }
            
        except Exception as e:
            logger.error(f"Documentation parsing failed: {str(e)}")
            raise DocumentationError(f"Documentation parsing failed: {str(e)}")
            
    def cleanup(self) -> None:
        """Clean up parser resources."""
        self._cache.clear()
        
    def _parse_python_docs(self, content: str) -> Dict[str, Any]:
        """Parse Python documentation strings."""
        try:
            tree = ast.parse(content)
            docs = {
                'module_doc': ast.get_docstring(tree),
                'classes': {},
                'functions': {},
                'coverage': 0,
                'quality_score': 0
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docs['classes'][node.name] = {
                        'docstring': ast.get_docstring(node),
                        'methods': {}
                    }
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef):
                            docs['classes'][node.name]['methods'][method.name] = {
                                'docstring': ast.get_docstring(method)
                            }
                            
                elif isinstance(node, ast.FunctionDef):
                    docs['functions'][node.name] = {
                        'docstring': ast.get_docstring(node)
                    }
                    
            # Calculate coverage and quality
            docs.update(self._analyze_python_doc_quality(docs))
            return docs
            
        except Exception as e:
            logger.error(f"Python documentation parsing failed: {str(e)}")
            raise
            
    def _parse_jsdoc(self, content: str) -> Dict[str, Any]:
        """Parse JSDoc documentation with enhanced error handling and tag parsing."""
        docs = {
            'module_doc': None,
            'classes': {},
            'functions': {},
            'coverage': 0,
            'quality_score': 0
        }
        
        try:
            # Match JSDoc blocks
            jsdoc_pattern = r'/\*\*\s*(.*?)\s*\*/'
            matches = re.finditer(jsdoc_pattern, content, re.DOTALL)
            
            # Count total elements to calculate coverage
            total_elements = len(re.findall(r'\bfunction\b|\bclass\b|\binterface\b|\btype\b|\bconst\b|\blet\b|\bvar\b', content))
            documented_elements = 0
            
            for match in matches:
                doc_content = match.group(1).strip()
                if not doc_content:
                    continue
                    
                # Parse JSDoc tags
                tags = self._parse_jsdoc_tags(doc_content)
                
                if '@class' in tags or '@interface' in tags:
                    class_name = tags.get('@class', [None])[0] or tags.get('@interface', [None])[0]
                    if class_name:
                        docs['classes'][class_name] = {
                            'docstring': doc_content,
                            'methods': {}
                        }
                        documented_elements += 1
                        
                elif '@function' in tags or '@method' in tags:
                    func_name = tags.get('@function', [None])[0] or tags.get('@method', [None])[0]
                    if func_name:
                        docs['functions'][func_name] = {
                            'docstring': doc_content,
                            'params': tags.get('@param', []),
                            'returns': tags.get('@returns', [None])[0]
                        }
                        documented_elements += 1
                        
                elif not docs['module_doc'] and '@module' in tags:
                    docs['module_doc'] = doc_content
                    documented_elements += 1
                    
            # Calculate coverage and quality metrics
            docs['coverage'] = round((documented_elements / total_elements * 100) if total_elements > 0 else 0, 2)
            docs['quality_score'] = self._calculate_jsdoc_quality(docs)
            
            return docs
            
        except Exception as e:
            logger.error(f"JSDoc parsing failed: {str(e)}")
            return {
                'module_doc': None,
                'classes': {},
                'functions': {},
                'coverage': 0,
                'quality_score': 0,
                'error': str(e)
            }
            
    def _parse_jsdoc_tags(self, content: str) -> Dict[str, List[str]]:
        """Parse JSDoc tags into a structured format."""
        tags = {}
        tag_pattern = r'@(\w+)\s+([^\n@]*)'
        
        for match in re.finditer(tag_pattern, content):
            tag, value = match.groups()
            tag_name = f'@{tag}'
            if tag_name not in tags:
                tags[tag_name] = []
            tags[tag_name].append(value.strip())
            
        return tags
        
    def _calculate_jsdoc_quality(self, docs: Dict) -> float:
        """Calculate documentation quality score for JSDoc."""
        total_score = 0
        total_elements = 0
        
        def score_doc(doc_content: str) -> float:
            if not doc_content:
                return 0
                
            score = 0
            # Check description length
            score += min(len(doc_content.split()) / 10, 1)
            # Check for parameters
            score += 0.5 if '@param' in doc_content else 0
            # Check for return type
            score += 0.5 if '@returns' in doc_content else 0
            # Check for examples
            score += 0.5 if '@example' in doc_content else 0
            # Check for type information
            score += 0.5 if '@type' in doc_content or '@typedef' in doc_content else 0
            
            return min(score, 2.5) * 40  # Scale to 100
        
        if docs['module_doc']:
            total_score += score_doc(docs['module_doc'])
            total_elements += 1
            
        for class_info in docs['classes'].values():
            total_score += score_doc(class_info['docstring'])
            total_elements += 1
            
        for func_info in docs['functions'].values():
            total_score += score_doc(func_info['docstring'])
            total_elements += 1
            
        return round(total_score / total_elements if total_elements > 0 else 0, 2)
            
    def _analyze_python_doc_quality(self, docs: Dict) -> Dict[str, float]:
        """Analyze Python documentation quality."""
        total_elements = 1  # Module
        documented_elements = 1 if docs['module_doc'] else 0
        
        # Check classes and methods
        for class_info in docs['classes'].values():
            total_elements += 1  # Class
            if class_info['docstring']:
                documented_elements += 1
                
            for method_info in class_info['methods'].values():
                total_elements += 1
                if method_info['docstring']:
                    documented_elements += 1
                    
        # Check standalone functions
        total_elements += len(docs['functions'])
        documented_elements += sum(1 for func in docs['functions'].values() 
                                 if func['docstring'])
                                 
        coverage = (documented_elements / total_elements * 100) if total_elements > 0 else 0
        
        return {
            'coverage': round(coverage, 2),
            'quality_score': self._calculate_doc_quality_score(docs)
        }
        
    def _analyze_jsdoc_quality(self, docs: Dict) -> Dict[str, float]:
        """Analyze JSDoc documentation quality."""
        total_elements = len(docs['functions'])
        documented_elements = sum(1 for func in docs['functions'].values() 
                                if func['docstring'])
                                
        coverage = (documented_elements / total_elements * 100) if total_elements > 0 else 0
        
        return {
            'coverage': round(coverage, 2),
            'quality_score': self._calculate_doc_quality_score(docs)
        }
        
    def _calculate_doc_quality_score(self, docs: Dict) -> float:
        """Calculate documentation quality score."""
        score = 0
        total_docs = 0
        
        def analyze_doc(docstring: Optional[str]) -> float:
            if not docstring:
                return 0
                
            doc_score = 0
            # Check length
            doc_score += min(len(docstring.split()) / 10, 1)
            # Check for parameters
            doc_score += 0.5 if ':param' in docstring or '@param' in docstring else 0
            # Check for return type
            doc_score += 0.5 if ':return' in docstring or '@returns' in docstring else 0
            
            return min(doc_score, 1) * 100
            
        # Analyze module doc
        if docs.get('module_doc'):
            score += analyze_doc(docs['module_doc'])
            total_docs += 1
            
        # Analyze class docs
        for class_info in docs.get('classes', {}).values():
            if class_info.get('docstring'):
                score += analyze_doc(class_info['docstring'])
                total_docs += 1
                
            # Analyze method docs
            for method_info in class_info.get('methods', {}).values():
                if method_info.get('docstring'):
                    score += analyze_doc(method_info['docstring'])
                    total_docs += 1
                    
        # Analyze function docs
        for func_info in docs.get('functions', {}).values():
            if func_info.get('docstring'):
                score += analyze_doc(func_info['docstring'])
                total_docs += 1
                
        return round(score / total_docs if total_docs > 0 else 0, 2)
        
    def _calculate_stats(self, results: Dict) -> Dict[str, Any]:
        """Calculate overall documentation statistics."""
        total_files = len(results)
        total_coverage = 0
        total_quality = 0
        
        for file_docs in results.values():
            if isinstance(file_docs, dict) and 'error' not in file_docs:
                total_coverage += file_docs.get('coverage', 0)
                total_quality += file_docs.get('quality_score', 0)
                
        return {
            'average_coverage': round(total_coverage / total_files if total_files > 0 else 0, 2),
            'average_quality': round(total_quality / total_files if total_files > 0 else 0, 2),
            'total_files_analyzed': total_files
        }
    
