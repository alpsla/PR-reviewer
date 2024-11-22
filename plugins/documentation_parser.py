"""Documentation parser plugin for analyzing code documentation."""

import re
import ast
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .base_plugin import BasePlugin
from core.exceptions import DocumentationError

logger = logging.getLogger(__name__)

class DocumentationParser(BasePlugin):
    """Plugin for parsing and analyzing code documentation."""
    
    def __init__(self):
        """Initialize the documentation parser plugin."""
        self.supported_languages = {
            '.py': self._parse_python_docs,
            '.js': self._parse_jsdoc,
            '.ts': self._parse_jsdoc,
            '.jsx': self._parse_jsdoc,
            '.tsx': self._parse_jsdoc
        }
        self._cache = {}
        # Event bus will be initialized in initialize() method
        self._event_bus = None
        self.initialized = False
        
    @property
    def name(self) -> str:
        return "documentation_parser"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    def initialize(self) -> None:
        """Initialize parser resources and event bus."""
        try:
            from core.event_bus import EventBus
            self._event_bus = EventBus()
            self.initialized = True
            logger.info("Documentation parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize documentation parser: {str(e)}")
            raise DocumentationError(f"Parser initialization failed: {str(e)}")
        
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
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
            
        if not self._event_bus:
            raise DocumentationError("Event bus not available")
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
                    
                # Report progress
                progress = (index + 1) / total_files * 100
                await self._event_bus.publish('doc_parsing_progress', {
                    'file': filename,
                    'progress': progress
                })
                
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
        """Parse JSDoc documentation."""
        docs = {
            'module_doc': '',
            'classes': {},
            'functions': {},
            'coverage': 0,
            'quality_score': 0
        }
        
        # JSDoc comment pattern
        jsdoc_pattern = r'/\*\*\s*(.*?)\s*\*/'
        
        try:
            # Extract JSDoc comments
            matches = re.finditer(jsdoc_pattern, content, re.DOTALL)
            for match in matches:
                doc_content = match.group(1)
                # Parse JSDoc tags and content
                docs['functions'][f"func_{len(docs['functions'])}"] = {
                    'docstring': doc_content.strip()
                }
                
            # Calculate coverage and quality
            docs.update(self._analyze_jsdoc_quality(docs))
            return docs
            
        except Exception as e:
            logger.error(f"JSDoc parsing failed: {str(e)}")
            raise
            
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
    def execute_sync(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous version of execute method for documentation parsing.
        
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
                        
            return {
                'documentation': results,
                'stats': self._calculate_stats(results)
            }
            
        except Exception as e:
            logger.error(f"Documentation parsing failed: {str(e)}")
            raise DocumentationError(f"Documentation parsing failed: {str(e)}")
