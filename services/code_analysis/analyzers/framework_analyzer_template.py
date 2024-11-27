"""Template for creating new framework-specific analyzers."""

from typing import Dict, Any, Optional, List
import re
from .typescript_analyzer import TypeScriptAnalyzer, AnalysisOutput
from logging_config import get_logger

class FrameworkAnalyzerTemplate(TypeScriptAnalyzer):
    """Base class for framework-specific analyzers."""
    
    FRAMEWORK_NAME = "framework_name"  # Override this in each framework analyzer
    
    def __init__(self, github_token: Optional[str] = None):
        super().__init__(github_token)
        self.logger = get_logger(__name__, f"typescript_{self.FRAMEWORK_NAME}")
        self.logger.info(f"Initializing TypeScript {self.FRAMEWORK_NAME} analyzer", 
                        extra={
                            "analyzer": f"typescript_{self.FRAMEWORK_NAME}",
                            "framework": self.FRAMEWORK_NAME,
                            "language": "typescript"
                        })
        # Initialize framework-specific patterns
        self.framework_patterns = self._compile_framework_patterns()
    
    def _compile_framework_patterns(self) -> Dict[str, re.Pattern]:
        """Compile framework-specific regex patterns."""
        try:
            # Override this method in each framework analyzer
            return {}
        except Exception as e:
            self.logger.error(f"Error compiling {self.FRAMEWORK_NAME} patterns", 
                            extra={
                                "error": str(e)
                            })
            return {}
    
    def analyze_framework_patterns(self, content: str) -> Dict[str, Any]:
        """Analyze framework-specific patterns in the code."""
        try:
            # Override this method in each framework analyzer
            return {}
        except Exception as e:
            self.logger.error(f"Error analyzing {self.FRAMEWORK_NAME} patterns", 
                            extra={
                                "error": str(e)
                            })
            return {}
    
    def analyze_file(self, content: str, file_path: str) -> AnalysisOutput:
        """Override analyze_file to include framework-specific analysis."""
        try:
            # Get base TypeScript analysis
            base_analysis = super().analyze_file(content, file_path)
            
            # Add framework-specific analysis
            framework_analysis = self.analyze_framework_patterns(content)
            
            # Log analysis results
            self.logger.info(f"{self.FRAMEWORK_NAME} analysis completed", 
                           extra={
                               "file_path": file_path,
                               "framework_metrics": framework_analysis
                           })
            
            # Merge analyses
            merged_analysis = base_analysis.to_dict()
            merged_analysis[f'{self.FRAMEWORK_NAME}_analysis'] = framework_analysis
            
            return AnalysisOutput.from_dict(merged_analysis)
            
        except Exception as e:
            self.logger.error(f"Error analyzing {self.FRAMEWORK_NAME} file {file_path}", 
                            extra={
                                "error": str(e),
                                "file_path": file_path
                            })
            return self._create_empty_analysis()
