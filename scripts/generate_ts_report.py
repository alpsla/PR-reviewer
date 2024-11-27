import os
from datetime import datetime
from typing import List, Dict

def generate_full_report(analyses: List[Dict]) -> str:
    """Generate a comprehensive TypeScript analysis report"""
    report = []
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Report header
    report.append(f"""# TypeScript Code Quality Analysis Report
Generated on: {timestamp}

## Overview

This report provides a comprehensive analysis of TypeScript code quality across projects.
Each section evaluates different aspects of TypeScript usage, best practices, and potential improvements.

### Analysis Scope
- Type System Implementation
- Code Structure and Organization
- TypeScript Best Practices
- Documentation Standards
- Error Handling Patterns
- Framework-Specific Patterns
- Performance Considerations

## Projects Analyzed

{chr(10).join([f"- {analysis['name']}" for analysis in analyses])}
""")

    # Detailed analysis for each project
    for analysis in analyses:
        report.append(f"""
## {analysis['name']}
---

### 1. Type System Analysis
```typescript
Type Coverage Metrics
├── Overall Type Coverage: {analysis['metrics']['type_coverage']:.1f}%
├── Type Safety Score: {analysis['metrics']['type_safety']:.1f}%
└── Type Inference Usage: {analysis['metrics'].get('type_inference', 0):.1f}%

Code Structure Analysis
├── Classes: {analysis['metrics'].get('classes', 0)} definitions
├── Interfaces: {analysis['metrics'].get('interfaces', 0)} definitions
├── Type Aliases: {analysis['metrics'].get('type_aliases', 0)} definitions
├── Enums: {analysis['metrics'].get('enums', 0)} definitions
└── Namespaces: {analysis['metrics'].get('namespaces', 0)} definitions

Type System Features
├── Generic Types: {analysis['metrics'].get('generic_types', 0)} implementations
├── Mapped Types: {analysis['metrics'].get('mapped_types', 0)} uses
├── Conditional Types: {analysis['metrics'].get('conditional_types', 0)} uses
├── Type Guards: {analysis['metrics'].get('type_guards', 0)} implementations
├── Type Assertions: {analysis['metrics'].get('type_assertions', 0)} uses
└── Index Signatures: {analysis['metrics'].get('index_signatures', 0)} uses

Type Safety Measures
├── Strict Null Checks: {'Enabled ✅' if analysis['metrics'].get('strict_null_checks', False) else 'Disabled ❌'}
├── Strict Function Types: {'Enabled ✅' if analysis['metrics'].get('strict_function_types', False) else 'Disabled ❌'}
├── No Implicit Any: {'Enabled ✅' if analysis['metrics'].get('no_implicit_any', False) else 'Disabled ❌'}
└── Strict Property Initialization: {'Enabled ✅' if analysis['metrics'].get('strict_property_init', False) else 'Disabled ❌'}
```

### 2. Code Quality Metrics
```typescript
Function Analysis
├── Total Functions: {analysis['metrics'].get('total_functions', 0)} definitions
├── Async Functions: {analysis['metrics'].get('async_functions', 0)} implementations
├── Generator Functions: {analysis['metrics'].get('generator_functions', 0)} uses
├── Function Complexity: {analysis['metrics'].get('function_complexity', 'Low')}
└── Parameter Count Avg: {analysis['metrics'].get('avg_params', 0):.1f}

Error Handling
├── Try-Catch Blocks: {analysis['metrics'].get('try_catch_blocks', 0)} implementations
├── Error Types: {analysis['metrics'].get('error_types', 0)} custom definitions
├── Error Propagation: {analysis['metrics'].get('error_propagation', 'Standard')}
└── Async Error Handling: {analysis['metrics'].get('async_error_handling', 'Promise-based')}

Code Organization
├── Module Usage: {analysis['metrics'].get('module_usage', 'ES Modules')}
├── Dependency Structure: {analysis['metrics'].get('dependency_structure', 'Hierarchical')}
├── Circular Dependencies: {analysis['metrics'].get('circular_deps', 0)} detected
└── Code Splitting: {analysis['metrics'].get('code_splitting', 'Manual')}
```

### 3. Documentation Analysis
```typescript
Coverage Metrics
├── Overall JSDoc Coverage: {analysis['metrics'].get('jsdoc_coverage', 0):.1f}%
├── Function Documentation: {analysis['metrics'].get('function_docs', 0):.1f}%
├── Interface Documentation: {analysis['metrics'].get('interface_docs', 0):.1f}%
├── Type Documentation: {analysis['metrics'].get('type_docs', 0):.1f}%
└── Example Coverage: {analysis['metrics'].get('example_coverage', 0):.1f}%

Documentation Quality
├── Parameter Descriptions: {analysis['metrics'].get('param_descriptions', 0):.1f}%
├── Return Type Docs: {analysis['metrics'].get('return_docs', 0):.1f}%
├── Type Definitions: {analysis['metrics'].get('type_definitions', 0):.1f}%
└── Code Examples: {analysis['metrics'].get('code_examples', 0):.1f}%

API Documentation
├── Public API Coverage: {analysis['metrics'].get('public_api_docs', 0):.1f}%
├── Method Descriptions: {analysis['metrics'].get('method_docs', 0):.1f}%
├── Property Docs: {analysis['metrics'].get('property_docs', 0):.1f}%
└── Event Documentation: {analysis['metrics'].get('event_docs', 0):.1f}%
```

### 4. Code Examples

{format_code_examples(analysis['examples'])}

### 5. Framework Integration
```typescript
Framework Detection
├── Framework: {analysis.get('framework', 'None detected')}
├── Framework Version: {analysis.get('framework_version', 'N/A')}
└── TypeScript Support: {analysis.get('ts_support', 'Native')}

Framework-Specific Features
├── Component Types: {analysis['metrics'].get('component_types', 0)} implementations
├── State Management: {analysis['metrics'].get('state_management', 'N/A')}
├── Prop Types: {analysis['metrics'].get('prop_types', 0)} definitions
└── Event Handlers: {analysis['metrics'].get('event_handlers', 0)} implementations

Framework Best Practices
├── Component Structure: {analysis.get('component_structure', 'Standard')}
├── Lifecycle Usage: {analysis.get('lifecycle_usage', 'N/A')}
├── Hook Implementation: {analysis.get('hook_implementation', 'N/A')}
└── Performance Patterns: {analysis.get('performance_patterns', 'Standard')}
```

### 6. Performance Analysis
```typescript
Build Metrics
├── Bundle Size Impact: {analysis.get('bundle_size', 'Unknown')}
├── Tree Shaking: {analysis.get('tree_shaking', 'Enabled')}
├── Code Splitting: {analysis.get('code_splitting', 'Manual')}
└── Dynamic Imports: {analysis.get('dynamic_imports', 0)} uses

Runtime Performance
├── Memory Usage: {analysis.get('memory_usage', 'Optimal')}
├── Execution Time: {analysis.get('execution_time', 'Normal')}
├── Lazy Loading: {analysis.get('lazy_loading', 'Implemented')}
└── Cache Strategy: {analysis.get('cache_strategy', 'Standard')}
```

### 7. Security Analysis
```typescript
Type Safety
├── Input Validation: {analysis.get('input_validation', 'Basic')}
├── Sanitization: {analysis.get('sanitization', 'Standard')}
├── Type Assertions: {analysis.get('type_assertions_security', 'Safe')}
└── Null Safety: {analysis.get('null_safety', 'Strict')}

Security Patterns
├── Authentication Types: {analysis.get('auth_types', 'Standard')}
├── Authorization: {analysis.get('authorization', 'Role-based')}
├── Data Validation: {analysis.get('data_validation', 'Schema-based')}
└── Error Handling: {analysis.get('error_handling_security', 'Safe')}
```

### 8. Recommendations

#### Critical Issues
{chr(10).join([f"🔴 {issue}" for issue in [
    "Increase type coverage" if analysis['metrics']['type_coverage'] < 80 else None,
    "Enable strict null checks" if not analysis['metrics'].get('strict_null_checks', False) else None,
    "Add missing type guards" if analysis['metrics'].get('missing_guards', 0) > 0 else None,
    "Remove 'any' types" if analysis['metrics'].get('any_types', 0) > 0 else None
] if issue is not None])}

#### Type System Improvements
{chr(10).join([f"🟡 {improvement}" for improvement in [
    "Implement more generic types" if analysis['metrics'].get('generic_types', 0) < 5 else None,
    "Add type guards for better type narrowing" if analysis['metrics'].get('type_guards', 0) < 3 else None,
    "Use utility types for type manipulation" if analysis['metrics'].get('utility_types', 0) < 3 else None,
    "Implement branded types for IDs" if not analysis.get('branded_types', False) else None
] if improvement is not None])}

#### Best Practices
1. Use TypeScript's built-in utility types
2. Extract common types into shared interfaces
3. Enable strict mode compiler options
4. Implement proper error handling
5. Use discriminated unions for type safety

#### Documentation Improvements
{chr(10).join([f"📝 {doc_improvement}" for doc_improvement in [
    f"Increase JSDoc coverage (currently {analysis['metrics'].get('jsdoc_coverage', 0):.1f}%)",
    f"Document function parameters (currently {analysis['metrics'].get('param_descriptions', 0):.1f}%)",
    f"Add return type documentation (currently {analysis['metrics'].get('return_docs', 0):.1f}%)",
    f"Include code examples (currently {analysis['metrics'].get('example_coverage', 0):.1f}%)"
]])}

#### Framework-Specific
{chr(10).join([f"🔧 {framework_improvement}" for framework_improvement in [
    "Implement proper component typing" if analysis.get('framework', 'None') != 'None' and analysis['metrics'].get('component_types', 0) < 5 else None,
    "Use proper prop typing" if analysis.get('framework', 'None') != 'None' and analysis['metrics'].get('prop_types', 0) < 5 else None,
    "Add proper event handler types" if analysis.get('framework', 'None') != 'None' and analysis['metrics'].get('event_handlers', 0) < 5 else None
] if framework_improvement is not None])}

#### Performance Optimizations
1. Implement code splitting
2. Use lazy loading for large components
3. Optimize bundle size
4. Implement proper caching strategies

---
""")

    return "\n".join(report)

def format_code_examples(examples):
    """Format code examples section."""
    sections = []
    
    # Interface Definitions
    sections.append("#### Interface Definitions\n```typescript")
    if 'Interface Definitions' in examples:
        sections.append(examples['Interface Definitions'])
    else:
        sections.append("No interface examples found.")
    sections.append("```\n")
    
    # Type Guards & Assertions
    sections.append("#### Type Guards & Assertions\n```typescript")
    if 'Type Guards & Assertions' in examples:
        sections.append(examples['Type Guards & Assertions'])
    else:
        sections.append("No type guard examples found.")
    sections.append("```\n")
    
    # Generic Type Usage
    sections.append("#### Generic Type Usage\n```typescript")
    if 'Generic Type Usage' in examples:
        sections.append(examples['Generic Type Usage'])
    else:
        sections.append("No generic type examples found.")
    sections.append("```\n")
    
    # Error Handling Patterns
    sections.append("#### Error Handling Patterns\n```typescript")
    if 'Error Handling Patterns' in examples:
        sections.append(examples['Error Handling Patterns'])
    else:
        sections.append("No error handling examples found.")
    sections.append("```\n")
    
    # Advanced Type Features
    sections.append("#### Advanced Type Features\n```typescript")
    if 'Advanced Type Features' in examples:
        sections.append(examples['Advanced Type Features'])
    else:
        sections.append("No advanced type examples found.")
    sections.append("```\n")
    
    return '\n'.join(sections)

def get_type_safety_recommendation(metrics):
    """Generate type safety recommendations based on metrics"""
    if metrics['type_coverage'] < 80:
        return "Increase type coverage by adding explicit type annotations to functions and variables"
    elif metrics['type_guards'] < 50:
        return "Add more type guards to handle type narrowing and improve runtime type safety"
    elif metrics['null_checks'] < 50:
        return "Implement more null checks to prevent runtime null/undefined errors"
    else:
        return "Consider adding more advanced TypeScript features like conditional types and mapped types"

def get_organization_recommendation(metrics):
    """Generate code organization recommendations based on metrics"""
    if metrics['function_params'] < 50:
        return "Add type annotations to function parameters to improve code clarity"
    elif metrics['return_types'] < 50:
        return "Specify return types for functions to make the code more maintainable"
    elif metrics['generic_usage'] < 30:
        return "Consider using generics to make your code more reusable and type-safe"
    else:
        return "Extract common types into shared interfaces and type aliases"

def get_framework_recommendation(framework):
    """Generate framework-specific recommendations"""
    if framework == "REACT":
        return "Use React.FC type for function components and properly type props and state"
    elif framework == "ANGULAR":
        return "Leverage Angular's strict type checking and properly type inputs/outputs"
    elif framework == "VUE":
        return "Use Vue's TypeScript decorators and properly type component props"
    else:
        return "Consider adopting a framework that provides good TypeScript support"

def get_best_practice_recommendation(metrics):
    """Generate best practice recommendations based on metrics"""
    if metrics['any_types'] > 0:
        return "Replace 'any' types with proper type annotations or unknown"
    elif metrics['untyped_functions'] > 0:
        return "Add type annotations to all function parameters and return types"
    elif metrics['implicit_returns'] > 0:
        return "Add explicit return types to functions to improve code clarity"
    else:
        return "Consider using utility types like Partial<T> and Pick<T> for better type manipulation"

def get_error_handling_recommendation(metrics):
    """Generate error handling recommendations based on metrics"""
    if metrics['null_checks'] < 30:
        return "Implement proper error handling with type-safe error objects"
    elif metrics['type_guards'] < 30:
        return "Use type predicates and type guards for better error handling"
    else:
        return "Consider using Either type or Result type for better error handling"
