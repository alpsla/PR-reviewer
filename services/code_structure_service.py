from typing import Dict, List, Optional, TypedDict, Union, Sequence
import ast
import math
import re
import logging
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComplexityMetrics(TypedDict):
    """Complexity metrics for code analysis"""
    cyclomatic_complexity: int
    cognitive_complexity: int
    nesting_depth: int
    maintainability_index: float

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
class StructureInfo:
    """Information about code structure elements"""
    name: str
    type: str  # 'class', 'function', 'method'
    complexity: ComplexityMetrics
    dependencies: List[str]
    code_smells: Sequence[CodeSmell]
    api_stability: APIStabilityInfo

@dataclass
class AnalysisResult:
    """Result of code structure analysis"""
    structures: List[StructureInfo]
    imports: List[str]
    total_complexity: ComplexityMetrics

class CodeStructureService:
    """Service for analyzing code structure and complexity"""
    
    # File extensions to analyze
    SUPPORTED_EXTENSIONS = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript React',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript React'
    }
    
    # Skip patterns for files
    SKIP_PATTERNS = [
        '.test.', '.spec.',  # Test files
        '.min.', '.bundle.',  # Minified/bundled files
        '__init__',  # Python init files
        'setup.', 'config.'  # Setup/config files
    ]
    
    def analyze_code(self, content: str, filename: str) -> AnalysisResult:
        """Analyze code structure and complexity with enhanced validation"""
        try:
            # Validate file type
            ext = Path(filename).suffix.lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                logger.info(f"Skipping unsupported file type: {filename}")
                return self._empty_result()
                
            # Check skip patterns
            if any(pattern in filename for pattern in self.SKIP_PATTERNS):
                logger.info(f"Skipping pattern-matched file: {filename}")
                return self._empty_result()
                
            # Validate content size
            content_size = len(content.encode('utf-8'))
            if content_size > 1_000_000:  # Skip files larger than 1MB
                logger.warning(f"File too large to analyze: {filename} ({content_size} bytes)")
                return self._empty_result()
                
            logger.info(f"Analyzing code structure for {filename}")
            tree = ast.parse(content)
            
            # Collect imports
            imports = self._find_imports(tree)
            
            # Analyze structure elements
            structures = []
            total_complexity = {
                'cyclomatic_complexity': 0,
                'cognitive_complexity': 0,
                'nesting_depth': 0,
                'maintainability_index': 100.0
            }
            
            # Analyze each class and function
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    # Calculate complexity metrics
                    complexity = self._calculate_complexity(node)
                    
                    # Analyze dependencies
                    dependencies = self._find_dependencies(node)
                    
                    # Detect code smells
                    code_smells = self._detect_code_smells(node)
                    advanced_smells = self._detect_advanced_code_smells(node)
                    all_smells = list(code_smells)
                    all_smells.extend(advanced_smells)
                    
                    # Check API stability
                    api_stability = self._check_api_stability(node)
                    
                    # Create structure info
                    structure_info = StructureInfo(
                        name=node.name,
                        type='class' if isinstance(node, ast.ClassDef) else 'function',
                        complexity=complexity,
                        dependencies=dependencies,
                        code_smells=all_smells,
                        api_stability=api_stability
                    )
                    structures.append(structure_info)
                    
                    # Update total complexity
                    total_complexity['cyclomatic_complexity'] += complexity['cyclomatic_complexity']
                    total_complexity['cognitive_complexity'] += complexity['cognitive_complexity']
                    total_complexity['nesting_depth'] = max(
                        total_complexity['nesting_depth'],
                        complexity['nesting_depth']
                    )
            
            # Calculate average maintainability index
            if structures:
                total_complexity['maintainability_index'] = sum(
                    s.complexity['maintainability_index'] for s in structures
                ) / len(structures)
            
            return AnalysisResult(
                structures=structures,
                imports=imports,
                total_complexity=total_complexity
            )
            
        except SyntaxError as e:
            logger.error(f"Syntax error in {filename}: {str(e)}")
            return AnalysisResult(
                structures=[],
                imports=[],
                total_complexity={
                    'cyclomatic_complexity': 0,
                    'cognitive_complexity': 0,
                    'nesting_depth': 0,
                    'maintainability_index': 0.0
                }
            )
        except Exception as e:
            logger.error(f"Error analyzing {filename}: {str(e)}")
            raise
    
    def _find_imports(self, tree: ast.AST) -> List[str]:
        """Find all imports in the code"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                imports.extend(f"{module}.{alias.name}" for alias in node.names)
        return imports
    
    def _calculate_complexity(self, node: Union[ast.ClassDef, ast.FunctionDef]) -> ComplexityMetrics:
        """Calculate complexity metrics for a node"""
        cyclomatic = 1  # Base complexity
        cognitive = 0
        current_depth = 0
        max_depth = 0
        
        # Define complexity weights for different node types
        operator_weights = {
            ast.And: 1,
            ast.Or: 1,
            ast.If: 1,
            ast.While: 2,
            ast.For: 2,
            ast.AsyncFor: 2,
            ast.Try: 1,
            ast.ExceptHandler: 1,
            ast.Match: 2,
            ast.With: 1,
            ast.AsyncWith: 1,
            ast.Lambda: 1,
            ast.IfExp: 1
        }
        
        for child in ast.walk(node):
            # Calculate cyclomatic complexity
            node_type = type(child)
            if node_type in operator_weights:
                cyclomatic += operator_weights[node_type]
                
            # Calculate cognitive complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try, ast.Match)):
                cognitive += (1 + current_depth)  # Base cost plus nesting
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif isinstance(child, (ast.Break, ast.Continue)):
                cognitive += current_depth  # Control flow breakers
            elif isinstance(child, ast.BoolOp):
                cognitive += len(child.values) - 1  # Complex boolean logic
            elif isinstance(child, ast.Compare) and len(child.ops) > 1:
                cognitive += len(child.ops) - 1  # Multiple comparisons
            else:
                current_depth = max(0, current_depth - 1)
        
        maintainability = self._calculate_maintainability_index(node, cyclomatic, cognitive, max_depth)
        
        return {
            'cyclomatic_complexity': cyclomatic,
            'cognitive_complexity': cognitive,
            'nesting_depth': max_depth,
            'maintainability_index': maintainability
        }
    
    def _calculate_maintainability_index(
        self,
        node: Union[ast.ClassDef, ast.FunctionDef],
        cyclomatic: int,
        cognitive: int,
        depth: int
    ) -> float:
        """Calculate maintainability index"""
        try:
            # Get lines of code
            start_line = node.lineno
            end_line = 0
            for child in ast.walk(node):
                if hasattr(child, 'lineno'):
                    end_line = max(end_line, child.lineno)
            
            loc = max(1, end_line - start_line + 1)
            
            # Calculate maintainability index using enhanced formula
            mi = 171 - 5.2 * math.log(cognitive + 1) - 0.23 * cyclomatic - 16.2 * math.log(loc)
            mi = max(0, mi) * 100 / 171  # Normalize to 0-100 scale
            
            return round(mi, 2)
        except (ValueError, TypeError):
            return 50.0  # Default moderate maintainability
    
    def _find_dependencies(self, node: ast.AST) -> List[str]:
        """Find dependencies (function calls and attribute access)"""
        dependencies = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    chain = self._get_attribute_chain(child.func)
                    if chain:
                        dependencies.add(chain)
        return list(dependencies)
    
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
        """Detect basic code smells"""
        smells = []
        
        # Check function/method length
        start_line = node.lineno
        end_line = 0
        for child in ast.walk(node):
            if hasattr(child, 'lineno'):
                end_line = max(end_line, child.lineno)
        
        length = end_line - start_line + 1
        if length > 50:
            smells.append({
                'type': 'long_function',
                'description': f'Function/method is too long ({length} lines)',
                'severity': 'medium',
                'location': f'Line {start_line}'
            })
        
        return smells
    
    def _detect_advanced_code_smells(self, node: Union[ast.ClassDef, ast.FunctionDef]) -> List[CodeSmell]:
        """Detect advanced code smells"""
        smells = []
        
        # Check for large class (too many methods)
        if isinstance(node, ast.ClassDef):
            method_count = sum(1 for n in ast.walk(node) if isinstance(n, ast.FunctionDef))
            if method_count > 10:
                smells.append({
                    'type': 'large_class',
                    'description': f'Class has too many methods ({method_count})',
                    'severity': 'high',
                    'location': f'Line {node.lineno}'
                })
        
        # Check for long parameter list
    def _empty_result(self) -> AnalysisResult:
        """Create an empty analysis result"""
        return AnalysisResult(
            structures=[],
            imports=[],
            total_complexity={
                'cyclomatic_complexity': 0,
                'cognitive_complexity': 0,
                'nesting_depth': 0,
                'maintainability_index': 0.0
            }
        )
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
    
    def _check_api_stability(self, node: Union[ast.ClassDef, ast.FunctionDef]) -> APIStabilityInfo:
        """Check API stability indicators"""
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