import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

@dataclass
class TypeScriptMetrics:
    # Type System Coverage
    type_coverage: float = 0.0
    type_safety: float = 0.0
    type_inference: float = 0.0
    
    # Code Structure
    classes: int = 0
    interfaces: int = 0
    type_aliases: int = 0
    enums: int = 0
    namespaces: int = 0
    
    # Type System Features
    generic_types: int = 0
    mapped_types: int = 0
    conditional_types: int = 0
    type_guards: int = 0
    type_assertions: int = 0
    index_signatures: int = 0
    
    # Type Safety Measures
    strict_null_checks: bool = False
    strict_function_types: bool = False
    no_implicit_any: bool = False
    strict_property_init: bool = False
    
    # Functions
    total_functions: int = 0
    async_functions: int = 0
    generator_functions: int = 0
    function_complexity: str = "Low"
    avg_params: float = 0.0
    
    # Error Handling
    try_catch_blocks: int = 0
    error_types: int = 0
    error_propagation: str = "Standard"
    async_error_handling: str = "Promise-based"
    
    # Documentation
    jsdoc_coverage: float = 0.0
    function_docs: float = 0.0
    interface_docs: float = 0.0
    type_docs: float = 0.0
    example_coverage: float = 0.0
    param_descriptions: float = 0.0
    return_docs: float = 0.0
    type_definitions: float = 0.0
    code_examples: float = 0.0
    public_api_docs: float = 0.0
    method_docs: float = 0.0
    property_docs: float = 0.0
    event_docs: float = 0.0

def analyze_typescript_file(content: str) -> TypeScriptMetrics:
    """Analyze TypeScript file content and return metrics"""
    metrics = TypeScriptMetrics()
    
    # Split content into lines for analysis
    lines = content.split('\n')
    total_lines = len(lines)
    
    # Initialize counters
    typed_elements = 0
    total_elements = 0
    
    # Track unique types and interfaces
    types: Set[str] = set()
    interfaces: Set[str] = set()
    
    # Track functions and their properties
    functions: List[Dict] = []
    
    # Track documentation
    documented_elements = 0
    total_documentable_elements = 0
    
    # Analyze each line
    i = 0
    while i < total_lines:
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
            
        # Track interfaces
        if line.startswith('interface '):
            metrics.interfaces += 1
            interface_name = re.search(r'interface (\w+)', line).group(1)
            interfaces.add(interface_name)
            total_elements += 1
            typed_elements += 1
            
            # Check for documentation
            if i > 0 and '/**' in lines[i-1]:
                documented_elements += 1
            total_documentable_elements += 1
            
        # Track classes
        elif line.startswith('class '):
            metrics.classes += 1
            total_elements += 1
            typed_elements += 1
            
            # Check for documentation
            if i > 0 and '/**' in lines[i-1]:
                documented_elements += 1
            total_documentable_elements += 1
            
        # Track type aliases
        elif line.startswith('type '):
            metrics.type_aliases += 1
            type_name = re.search(r'type (\w+)', line).group(1)
            types.add(type_name)
            total_elements += 1
            typed_elements += 1
            
            # Check for generic types
            if '<' in line and '>' in line:
                metrics.generic_types += 1
                
            # Check for documentation
            if i > 0 and '/**' in lines[i-1]:
                documented_elements += 1
            total_documentable_elements += 1
            
        # Track functions
        elif 'function ' in line or '=>' in line:
            metrics.total_functions += 1
            total_elements += 1
            
            # Check async functions
            if 'async ' in line:
                metrics.async_functions += 1
                
            # Check generator functions
            if '*' in line:
                metrics.generator_functions += 1
                
            # Check return type
            if ':' in line and '=>' not in line.split(':')[0]:
                typed_elements += 1
                
            # Check parameters
            params = re.findall(r'\((.*?)\)', line)
            if params:
                param_count = len(params[0].split(',')) if params[0].strip() else 0
                metrics.avg_params = (metrics.avg_params * (metrics.total_functions - 1) + param_count) / metrics.total_functions
                
            # Check for documentation
            if i > 0 and '/**' in lines[i-1]:
                documented_elements += 1
                
                # Check for param and return documentation
                doc_lines = []
                doc_index = i - 1
                while doc_index >= 0 and '*/' not in lines[doc_index]:
                    doc_lines.append(lines[doc_index])
                    doc_index -= 1
                    
                param_docs = len([l for l in doc_lines if '@param' in l])
                return_docs = len([l for l in doc_lines if '@returns' in l])
                example_docs = len([l for l in doc_lines if '@example' in l])
                
                if param_docs > 0:
                    metrics.param_descriptions += 1
                if return_docs > 0:
                    metrics.return_docs += 1
                if example_docs > 0:
                    metrics.example_coverage += 1
                    
            total_documentable_elements += 1
            
        # Track type guards
        elif 'is ' in line and ': ' in line and ' is ' in line:
            metrics.type_guards += 1
            
        # Track error handling
        elif 'try ' in line:
            metrics.try_catch_blocks += 1
            
        # Track type assertions
        elif ' as ' in line:
            metrics.type_assertions += 1
            
        i += 1
    
    # Calculate final metrics
    if total_elements > 0:
        metrics.type_coverage = (typed_elements / total_elements) * 100
        metrics.type_safety = (typed_elements / total_elements) * 100
        
    if total_documentable_elements > 0:
        metrics.jsdoc_coverage = (documented_elements / total_documentable_elements) * 100
        metrics.function_docs = metrics.param_descriptions / metrics.total_functions * 100 if metrics.total_functions > 0 else 0
        metrics.return_docs = metrics.return_docs / metrics.total_functions * 100 if metrics.total_functions > 0 else 0
        
    # Set type safety measures based on content analysis
    metrics.strict_null_checks = 'strictNullChecks' in content
    metrics.no_implicit_any = 'noImplicitAny' in content
    metrics.strict_function_types = 'strictFunctionTypes' in content
    metrics.strict_property_init = 'strictPropertyInitialization' in content
    
    return metrics

@dataclass
class TypeMetrics:
    # Type System Coverage
    type_coverage: float = 0.0
    type_safety: float = 0.0
    type_inference: float = 0.0
    
    # Code Structure
    classes: int = 0
    interfaces: int = 0
    type_alias: int = 0
    enums: int = 0
    namespaces: int = 0
    
    # Type System Features
    generic_types: int = 0
    mapped_types: int = 0
    conditional_types: int = 0
    type_guards: int = 0
    type_assertions: int = 0
    index_signatures: int = 0
    any_types: int = 0
    
    # Type Safety Measures
    strict_null_checks: bool = False
    strict_function_types: bool = False
    no_implicit_any: bool = False
    strict_property_init: bool = False
    
    # Functions
    total_functions: int = 0
    async_functions: int = 0
    generator_functions: int = 0
    function_complexity: str = "Low"
    avg_params: float = 0.0
    
    # Error Handling
    try_catch_blocks: int = 0
    error_types: int = 0
    error_propagation: str = "Standard"
    async_error_handling: str = "Promise-based"
    
    # Documentation
    doc_coverage: float = 0.0
    jsdoc_coverage: float = 0.0
    param_doc_coverage: float = 0.0
    return_doc_coverage: float = 0.0
    type_definitions: float = 0.0
    code_examples: float = 0.0
    public_api_docs: float = 0.0
    method_docs: float = 0.0
    property_docs: float = 0.0
    event_docs: float = 0.0

def analyze_typescript_code(content: str) -> TypeMetrics:
    """Analyze TypeScript code content and return metrics"""
    metrics = TypeMetrics()
    
    # Split content into lines for analysis
    lines = content.split('\n')
    total_lines = len(lines)
    
    # Initialize counters
    typed_elements = 0
    total_elements = 0
    
    # Track unique types and interfaces
    types: Set[str] = set()
    interfaces: Set[str] = set()
    
    # Track functions and their properties
    functions: List[Dict] = []
    
    # Track documentation
    documented_elements = 0
    total_documentable_elements = 0
    
    # Analyze each line
    i = 0
    while i < total_lines:
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
            
        # Track interfaces
        if line.startswith('interface '):
            metrics.interfaces += 1
            interface_name = re.search(r'interface (\w+)', line).group(1)
            interfaces.add(interface_name)
            total_elements += 1
            typed_elements += 1
            
            # Check for documentation
            if i > 0 and '/**' in lines[i-1]:
                documented_elements += 1
            total_documentable_elements += 1
            
        # Track classes
        elif line.startswith('class '):
            metrics.classes += 1
            total_elements += 1
            typed_elements += 1
            
            # Check for documentation
            if i > 0 and '/**' in lines[i-1]:
                documented_elements += 1
            total_documentable_elements += 1
            
        # Track type aliases
        elif line.startswith('type '):
            metrics.type_alias += 1
            type_name = re.search(r'type (\w+)', line).group(1)
            types.add(type_name)
            total_elements += 1
            typed_elements += 1
            
            # Check for generic types
            if '<' in line and '>' in line:
                metrics.generic_types += 1
                
            # Check for documentation
            if i > 0 and '/**' in lines[i-1]:
                documented_elements += 1
            total_documentable_elements += 1
            
        # Track functions
        elif 'function ' in line or '=>' in line:
            metrics.total_functions += 1
            total_elements += 1
            
            # Check async functions
            if 'async ' in line:
                metrics.async_functions += 1
                
            # Check generator functions
            if '*' in line:
                metrics.generator_functions += 1
                
            # Check return type
            if ':' in line and '=>' not in line.split(':')[0]:
                typed_elements += 1
                
            # Check parameters
            params = re.findall(r'\((.*?)\)', line)
            if params:
                param_count = len(params[0].split(',')) if params[0].strip() else 0
                metrics.avg_params = (metrics.avg_params * (metrics.total_functions - 1) + param_count) / metrics.total_functions
                
            # Check for documentation
            if i > 0 and '/**' in lines[i-1]:
                documented_elements += 1
                
                # Check for param and return documentation
                doc_lines = []
                doc_index = i - 1
                while doc_index >= 0 and '*/' not in lines[doc_index]:
                    doc_lines.append(lines[doc_index])
                    doc_index -= 1
                    
                param_docs = len([l for l in doc_lines if '@param' in l])
                return_docs = len([l for l in doc_lines if '@returns' in l])
                example_docs = len([l for l in doc_lines if '@example' in l])
                
                if param_docs > 0:
                    metrics.param_doc_coverage += 1
                if return_docs > 0:
                    metrics.return_doc_coverage += 1
                if example_docs > 0:
                    metrics.code_examples += 1
                    
            total_documentable_elements += 1
            
        # Track type guards
        elif 'is ' in line and ': ' in line and ' is ' in line:
            metrics.type_guards += 1
            
        # Track error handling
        elif 'try ' in line:
            metrics.try_catch_blocks += 1
            
        # Track type assertions
        elif ' as ' in line:
            metrics.type_assertions += 1
            
        i += 1
    
    # Calculate final metrics
    if total_elements > 0:
        metrics.type_coverage = (typed_elements / total_elements) * 100
        metrics.type_safety = (typed_elements / total_elements) * 100
        
    if total_documentable_elements > 0:
        metrics.doc_coverage = (documented_elements / total_documentable_elements) * 100
        metrics.jsdoc_coverage = (documented_elements / total_documentable_elements) * 100
        
        if metrics.total_functions > 0:
            metrics.param_doc_coverage = (metrics.param_doc_coverage / metrics.total_functions) * 100
            metrics.return_doc_coverage = (metrics.return_doc_coverage / metrics.total_functions) * 100
            metrics.code_examples = (metrics.code_examples / metrics.total_functions) * 100
    
    return metrics

def extract_examples(content: str) -> dict:
    """Extract code examples from TypeScript content."""
    examples = {}
    
    # Split content into lines for easier processing
    lines = content.split('\n')
    
    # Extract interface definitions
    for i, line in enumerate(lines):
        if line.strip().startswith('interface User'):
            interface_def = []
            j = i
            while j < len(lines) and '}' not in lines[j]:
                interface_def.append(lines[j])
                j += 1
            if j < len(lines):
                interface_def.append(lines[j])
            if interface_def:
                examples['Interface Definitions'] = '\n'.join(interface_def)
                break
    
    # Extract type guards
    for i, line in enumerate(lines):
        if 'function isUserPreferences' in line:
            guard_def = []
            j = i
            while j < len(lines) and '}' not in lines[j]:
                guard_def.append(lines[j])
                j += 1
            if j < len(lines):
                guard_def.append(lines[j])
            if guard_def:
                examples['Type Guards & Assertions'] = '\n'.join(guard_def)
                break
    
    # Extract generic type usage
    for i, line in enumerate(lines):
        if 'interface Result<' in line:
            generic_def = []
            j = i
            while j < len(lines) and '}' not in lines[j]:
                generic_def.append(lines[j])
                j += 1
            if j < len(lines):
                generic_def.append(lines[j])
            if generic_def:
                examples['Generic Type Usage'] = '\n'.join(generic_def)
                break
    
    # Extract error handling patterns
    error_patterns = []
    
    # Find Result interface
    for i, line in enumerate(lines):
        if 'interface Result<' in line:
            result_def = []
            j = i
            while j < len(lines) and '}' not in lines[j]:
                result_def.append(lines[j])
                j += 1
            if j < len(lines):
                result_def.append(lines[j])
            if result_def:
                error_patterns.append("// Result type for type-safe error handling\n" + '\n'.join(result_def))
                break
    
    # Find error handling example
    for i, line in enumerate(lines):
        if "return { ok: false, error:" in line:
            error_def = []
            j = i - 1  # Include the if condition
            while j >= 0 and 'if' not in lines[j]:
                j -= 1
            if j >= 0:
                while j <= i + 1:  # Include the closing brace
                    error_def.append(lines[j])
                    j += 1
                if error_def:
                    error_patterns.append("// Error handling with Result type\n" + '\n'.join(error_def))
                    break
    
    if error_patterns:
        examples['Error Handling Patterns'] = '\n\n'.join(error_patterns)
    
    # Extract advanced type features
    advanced_patterns = []
    
    # Find utility types
    for i, line in enumerate(lines):
        if 'type UserResponse = Pick<' in line:
            advanced_patterns.append("// Utility type usage\n" + line)
            break
    
    # Find branded types
    for i, line in enumerate(lines):
        if 'type Brand<' in line:
            advanced_patterns.append("// Branded type for type safety\n" + line)
            break
    
    if advanced_patterns:
        examples['Advanced Type Features'] = '\n\n'.join(advanced_patterns)
    
    return examples
