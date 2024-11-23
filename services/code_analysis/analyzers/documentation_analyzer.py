from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass, field
from pathlib import Path

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
        """Analyze documentation quality and coverage.
        
        Args:
            content: Source code content to analyze
            filename: Name of the file being analyzed
            
        Returns:
            DocumentationMetrics containing analysis results
        """
        try:
            if not self.initialized:
                self.initialize()
                
            if not self.doc_parser:
                return self._empty_doc_metrics("Documentation parser not initialized")
                
            # Execute documentation analysis
            doc_analysis = self.doc_parser.execute_sync({
                'files': [{
                    'filename': filename,
                    'content': content
                }]
            })
            
            # Extract documentation info for this specific file
            doc_info = doc_analysis.get('documentation', {}).get(filename, {})
            if not doc_info:
                return self._empty_doc_metrics('No documentation found')
                
            # Convert to DocumentationMetrics format
            metrics = DocumentationMetrics(
                coverage=doc_info.get('coverage', 0.0),
                quality_score=doc_info.get('quality_score', 0.0),
                module_doc=doc_info.get('module_doc'),
                classes=doc_info.get('classes', {}),
                functions=doc_info.get('functions', {})
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Documentation analysis failed: {str(e)}")
            return self._empty_doc_metrics(str(e))
            
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
