from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

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
class DocumentationMetrics:
    """Documentation analysis metrics"""
    coverage: float = 0.0
    quality_score: float = 0.0
    module_doc: Optional[str] = None
    classes: Dict[str, Dict] = field(default_factory=dict)
    functions: Dict[str, Dict] = field(default_factory=dict)
    error: Optional[str] = None

class CodeAnalyzerBase:
    """Base class for code analyzers"""
    
    def analyze_documentation(self, content: str, filename: str) -> DocumentationMetrics:
        """Analyze documentation quality and coverage.
        
        Args:
            content: Source code content to analyze
            filename: Name of the file being analyzed
            
        Returns:
            DocumentationMetrics object containing analysis results
        """
        raise NotImplementedError
        
    def _empty_doc_metrics(self, error_message: Optional[str] = None) -> DocumentationMetrics:
        """Create empty documentation metrics."""
        return DocumentationMetrics(error=error_message)
