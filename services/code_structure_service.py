import ast
import logging
from typing import Dict, List, Optional, TypedDict
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComplexityMetrics(TypedDict):
    """Complexity metrics for code structures"""
    cyclomatic_complexity: int
    cognitive_complexity: int
    nesting_depth: int

class StructureInfo(TypedDict):
    """Information about code structures"""
    name: str
    type: str  # 'class', 'function', 'method'
    start_line: int
    end_line: int
    complexity: ComplexityMetrics
    dependencies: List[str]
    docstring: Optional[str]

@dataclass
class CodeStructure:
    """Code structure analysis results"""
    structures: List[StructureInfo]
    imports: List[str]
    total_complexity: ComplexityMetrics
    file_path: str

class CodeStructureService:
    """Service for analyzing code structure and complexity"""
    
    def __init__(self):
        """Initialize the code structure analysis service"""
        logger.info("Initializing code structure analysis service")
    
    def analyze_code(self, content: str, file_path: str) -> CodeStructure:
        """Analyze code structure and complexity"""
        try:
            logger.info(f"Starting code structure analysis for {file_path}")
            tree = ast.parse(content)
            
            structures = []
            imports = []
            total_complexity = {
                'cyclomatic_complexity': 0,
                'cognitive_complexity': 0,
                'nesting_depth': 0
            }
            
            # Analyze imports
            imports = self._analyze_imports(tree)
            logger.info(f"Found {len(imports)} imports")
            
            # Analyze classes and functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    structure = self._analyze_node(node)
                    structures.append(structure)
                    
                    # Update total complexity
                    for metric, value in structure['complexity'].items():
                        total_complexity[metric] += value
            
            logger.info(f"Analysis complete - Found {len(structures)} code structures")
            return CodeStructure(
                structures=structures,
                imports=imports,
                total_complexity=total_complexity,
                file_path=file_path
            )
            
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error analyzing code structure: {str(e)}")
            raise
    
    def _analyze_imports(self, tree: ast.AST) -> List[str]:
        """Analyze import statements"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                imports.extend(f"{module}.{alias.name}" for alias in node.names)
        return imports
    
    def _analyze_node(self, node: ast.AST) -> StructureInfo:
        """Analyze a class or function node"""
        name = node.name
        node_type = 'class' if isinstance(node, ast.ClassDef) else 'function'
        
        # Get line numbers
        start_line = node.lineno
        end_line = self._get_end_line(node)
        
        # Calculate complexity metrics
        complexity = self._calculate_complexity(node)
        
        # Get dependencies (calls and attributes)
        dependencies = self._find_dependencies(node)
        
        # Get docstring
        docstring = ast.get_docstring(node)
        
        logger.debug(f"Analyzed {node_type} {name}: complexity={complexity}")
        
        return {
            'name': name,
            'type': node_type,
            'start_line': start_line,
            'end_line': end_line,
            'complexity': complexity,
            'dependencies': dependencies,
            'docstring': docstring
        }
    
    def _calculate_complexity(self, node: ast.AST) -> ComplexityMetrics:
        """Calculate complexity metrics for a node"""
        cyclomatic = 1  # Base complexity
        cognitive = 0
        max_depth = 0
        current_depth = 0
        
        for child in ast.walk(node):
            # Increase cyclomatic complexity for control flow statements
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                cyclomatic += 1
            
            # Calculate cognitive complexity
            if isinstance(child, (ast.If, ast.For, ast.While)):
                cognitive += (1 + current_depth)
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            else:
                current_depth = max(0, current_depth - 1)
        
        return {
            'cyclomatic_complexity': cyclomatic,
            'cognitive_complexity': cognitive,
            'nesting_depth': max_depth
        }
    
    def _find_dependencies(self, node: ast.AST) -> List[str]:
        """Find dependencies (function calls and attribute access)"""
        dependencies = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    dependencies.add(f"{self._get_attribute_chain(child.func)}")
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
    
    def _get_end_line(self, node: ast.AST) -> int:
        """Get the end line number of a node"""
        return max(
            getattr(node, 'lineno', 0),
            *(self._get_end_line(child) for child in ast.iter_child_nodes(node))
        )
