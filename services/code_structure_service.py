import ast
import logging
import math
import re
from typing import Dict, List, Optional, TypedDict, Union, Sequence
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CodeSmell(TypedDict):
    """Code smell information"""
    type: str  # Type of code smell
    description: str  # Description of the issue
    severity: str  # 'low', 'medium', 'high'
    location: str  # Where the smell was found

class APIStabilityInfo(TypedDict):
    """API stability tracking"""
    is_public: bool
    has_breaking_changes: bool
    version_info: Optional[str]

class ComplexityMetrics(TypedDict):
    """Complexity metrics for code structures"""
    cyclomatic_complexity: int
    cognitive_complexity: int
    nesting_depth: int
    maintainability_index: float

class StructureInfo(TypedDict):
    """Information about code structures"""
    name: str
    type: str  # 'class' or 'function'
    start_line: int
    end_line: int
    complexity: ComplexityMetrics
    dependencies: List[str]
    docstring: Optional[str]
    api_stability: APIStabilityInfo
    code_smells: Sequence[CodeSmell]

@dataclass
class CodeAnalysis:
    """Results of code structure analysis"""
    structures: List[StructureInfo]
    imports: List[str]
    total_complexity: ComplexityMetrics

class CodeStructureService:
    """Service for analyzing code structure and complexity"""
    
    def analyze_code(self, content: str, filename: str) -> CodeAnalysis:
        """Analyze code structure and complexity"""
        logger.info(f"Analyzing code structure for {filename}")
        try:
            tree = ast.parse(content)
            structures: List[StructureInfo] = []
            total_complexity = {
                'cyclomatic_complexity': 0,
                'cognitive_complexity': 0,
                'nesting_depth': 0,
                'maintainability_index': 0.0
            }
            
            # Find imports
            imports = self._find_imports(tree)
            
            # Analyze each class and function
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    try:
                        structure_info = self._analyze_node(node)
                        structures.append(structure_info)
                        
                        # Update total complexity
                        for metric in ['cyclomatic_complexity', 'cognitive_complexity', 'nesting_depth']:
                            total_complexity[metric] += structure_info['complexity'][metric]
                            
                    except Exception as e:
                        logger.error(f"Error analyzing node {getattr(node, 'name', 'unknown')}: {str(e)}")
            
            # Calculate average maintainability index
            if structures:
                total_complexity['maintainability_index'] = sum(
                    s['complexity']['maintainability_index'] for s in structures
                ) / len(structures)
            
            return CodeAnalysis(
                structures=structures,
                imports=imports,
                total_complexity=total_complexity
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze code: {str(e)}")
            raise ValueError(f"Code analysis failed: {str(e)}")
    
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
    
    def _analyze_node(self, node: Union[ast.ClassDef, ast.FunctionDef]) -> StructureInfo:
        """Analyze a class or function node"""
        name = node.name
        node_type = 'class' if isinstance(node, ast.ClassDef) else 'function'
        start_line = node.lineno
        end_line = self._get_end_line(node)
        
        # Calculate complexity metrics
        complexity = self._calculate_complexity(node)
        
        # Get dependencies (calls and attributes)
        dependencies = self._find_dependencies(node)
        
        # Get docstring and analyze documentation
        docstring = ast.get_docstring(node)
        
        # Check API stability
        api_stability = self._check_api_stability(node)
        
        # Detect code smells
        code_smells = self._detect_code_smells(node)
        
        logger.debug(f"Analyzed {node_type} {name}: complexity={complexity}")
        
        return {
            'name': name,
            'type': node_type,
            'start_line': start_line,
            'end_line': end_line,
            'complexity': complexity,
            'dependencies': dependencies,
            'docstring': docstring,
            'api_stability': api_stability,
            'code_smells': code_smells
        }
    
    def _calculate_complexity(self, node: Union[ast.ClassDef, ast.FunctionDef]) -> ComplexityMetrics:
        """Calculate complexity metrics for a node"""
        cyclomatic = 1  # Base complexity
        cognitive = 0
        current_depth = 0
        max_depth = 0
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try, ast.ExceptHandler)):
                cyclomatic += 1
                cognitive += (1 + current_depth)
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif isinstance(child, ast.Break):
                cognitive += current_depth
            else:
                current_depth = max(0, current_depth - 1)
        
        # Calculate maintainability index
        maintainability = self._calculate_maintainability_index(node, {
            'cyclomatic_complexity': cyclomatic,
            'cognitive_complexity': cognitive,
            'nesting_depth': max_depth,
            'maintainability_index': 0.0  # Temporary value
        })
        
        return {
            'cyclomatic_complexity': cyclomatic,
            'cognitive_complexity': cognitive,
            'nesting_depth': max_depth,
            'maintainability_index': maintainability
        }
    
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
    
    def _calculate_maintainability_index(self, node: Union[ast.ClassDef, ast.FunctionDef], complexity: ComplexityMetrics) -> float:
        """Calculate maintainability index based on complexity metrics"""
        loc = self._get_end_line(node) - node.lineno + 1
        cc = complexity['cyclomatic_complexity']
        hv = complexity['cognitive_complexity']
        
        if loc == 0 or hv == 0:
            return 100.0
            
        try:
            mi = 171 - 5.2 * math.log(hv) - 0.23 * cc - 16.2 * math.log(loc)
            mi = max(0, mi) * 100 / 171
            return round(mi, 2)
        except (ValueError, TypeError):
            return 50.0  # Default moderate maintainability
            
    def _check_api_stability(self, node: Union[ast.ClassDef, ast.FunctionDef]) -> APIStabilityInfo:
        """Check API stability indicators"""
        is_public = not node.name.startswith('_')
        has_breaking_changes = False
        version_info = None
        
        # Check docstring for version info
        docstring = ast.get_docstring(node)
        if docstring:
            if ':deprecated:' in docstring.lower():
                has_breaking_changes = True
            version_match = re.search(r':version:\s*(\d+\.\d+\.\d+)', docstring)
            if version_match:
                version_info = version_match.group(1)
        
        return {
            'is_public': is_public,
            'has_breaking_changes': has_breaking_changes,
            'version_info': version_info
        }
        
    def _detect_code_smells(self, node: Union[ast.ClassDef, ast.FunctionDef]) -> Sequence[CodeSmell]:
        """Detect various code smells in the node"""
        smells: List[CodeSmell] = []
        
        # Check function/method length
        loc = self._get_end_line(node) - node.lineno + 1
        if loc > 50:
            smells.append({
                'type': 'long_function',
                'description': f'Function is too long ({loc} lines)',
                'severity': 'medium',
                'location': f'Line {node.lineno}'
            })
            
        # Check parameter count for functions
        if isinstance(node, ast.FunctionDef) and len(node.args.args) > 5:
            smells.append({
                'type': 'too_many_parameters',
                'description': f'Function has too many parameters ({len(node.args.args)})',
                'severity': 'medium',
                'location': f'Line {node.lineno}'
            })
            
        # Check for missing docstring
        if not ast.get_docstring(node) and not node.name.startswith('_'):
            smells.append({
                'type': 'missing_documentation',
                'description': 'Public function/class missing docstring',
                'severity': 'low',
                'location': f'Line {node.lineno}'
            })
            
        # Check for complex conditions
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                condition_complexity = self._calculate_condition_complexity(child.test)
                if condition_complexity > 3:
                    smells.append({
                        'type': 'complex_condition',
                        'description': f'Complex condition (complexity: {condition_complexity})',
                        'severity': 'medium',
                        'location': f'Line {child.lineno}'
                    })
                    
        return smells
        
    def _calculate_condition_complexity(self, condition: ast.AST) -> int:
        """Calculate the complexity of a conditional expression"""
        complexity = 1
        for node in ast.walk(condition):
            if isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        return complexity
    
    def _get_end_line(self, node: ast.AST) -> int:
        """Get the end line number of a node"""
        return max(
            getattr(node, 'lineno', 0),
            *(self._get_end_line(child) for child in ast.iter_child_nodes(node))
        )
