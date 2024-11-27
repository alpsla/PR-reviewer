"""TypeScript React Analyzer for analyzing React-specific patterns and best practices."""

from typing import Dict, Any, Optional, List
import re
from .typescript_analyzer import TypeScriptAnalyzer, AnalysisOutput, CodeSample
from logging_config import get_logger

# Configure React-specific logger
logger = get_logger(__name__, "typescript_react")

class TypeScriptReactAnalyzer(TypeScriptAnalyzer):
    """Analyzer for TypeScript React code with React-specific patterns and metrics."""
    
    def __init__(self, github_token: Optional[str] = None):
        super().__init__(github_token)
        self.logger = logger
        self.logger.info("Initializing TypeScript React analyzer", 
                        extra={
                            "analyzer": "typescript_react",
                            "framework": "react",
                            "language": "typescript"
                        })
        # Initialize React-specific patterns
        self.react_patterns = self._compile_react_patterns()
        
    def _compile_react_patterns(self) -> Dict[str, re.Pattern]:
        """Compile React-specific regex patterns."""
        try:
            return {
                'hooks': {
                    'useState': re.compile(r'(?:React\.)?useState\s*\('),  # Make React. optional
                    'useEffect': re.compile(r'(?:React\.)?useEffect\s*\('),  # Make React. optional
                    'useCallback': re.compile(r'(?:React\.)?useCallback\s*\('),
                    'useMemo': re.compile(r'(?:React\.)?useMemo\s*\('),
                    'useRef': re.compile(r'(?:React\.)?useRef\s*\('),
                    'useContext': re.compile(r'(?:React\.)?useContext\s*\('),
                },
                'components': {
                    'functional': re.compile(r'(?:export\s+)?(?:const|function)\s+([A-Z]\w+)\s*(?::\s*(?:React\.)?FC\s*<.*?>)?\s*='),
                    'class': re.compile(r'class\s+([A-Z]\w+)\s+extends\s+(?:React\.)?Component'),
                },
                'props': {
                    'interface': re.compile(r'interface\s+(\w+Props)\s*{([^}]+)}'),
                    'type': re.compile(r'type\s+(\w+Props)\s*=\s*{([^}]+)}'),
                },
                'jsx': {
                    'element': re.compile(r'<(?!\/|\s*>)(?:div|span|p|button|h[1-6]|input|form|img|a)[^>]*>'),  # Improved JSX detection
                    'fragment': re.compile(r'<>|<React\.Fragment>'),
                }
            }
        except Exception as e:
            self.logger.error("Error compiling React patterns", 
                            extra={
                                "error": str(e)
                            })
            return {}

    def analyze_react_patterns(self, content: str) -> Dict[str, Any]:
        """Analyze React-specific patterns in the code."""
        try:
            hooks_usage = {hook: len(pattern.findall(content)) 
                         for hook, pattern in self.react_patterns['hooks'].items()}
            
            components = {
                'functional': len(self.react_patterns['components']['functional'].findall(content)),
                'class': len(self.react_patterns['components']['class'].findall(content))
            }
            
            props_interfaces = len(self.react_patterns['props']['interface'].findall(content))
            props_types = len(self.react_patterns['props']['type'].findall(content))
            
            jsx_elements = len(self.react_patterns['jsx']['element'].findall(content))
            fragments = len(self.react_patterns['jsx']['fragment'].findall(content))
            
            return {
                'hooks_usage': hooks_usage,
                'components': components,
                'props_definitions': {
                    'interfaces': props_interfaces,
                    'types': props_types
                },
                'jsx_usage': {
                    'elements': jsx_elements,
                    'fragments': fragments
                }
            }
        except Exception as e:
            self.logger.error("Error analyzing React patterns", 
                            extra={
                                "error": str(e)
                            })
            return {}

    def analyze_file(self, content: str, file_path: str) -> AnalysisOutput:
        """Override analyze_file to include React-specific analysis."""
        try:
            # Get base TypeScript analysis
            base_analysis = super().analyze_file(content, file_path)
            
            # Add React-specific analysis
            react_analysis = self.analyze_react_patterns(content)
            
            # Log analysis results
            self.logger.info("React analysis completed", 
                           extra={
                               "file_path": file_path,
                               "hooks_count": sum(react_analysis.get('hooks_usage', {}).values()),
                               "components_count": sum(react_analysis.get('components', {}).values())
                           })
            
            # Update framework analysis
            base_analysis.framework_analysis.framework = "react"
            base_analysis.framework_analysis.patterns = react_analysis
            
            return base_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing React file {file_path}", 
                            extra={
                                "error": str(e),
                                "file_path": file_path
                            })
            return self._create_empty_analysis()
