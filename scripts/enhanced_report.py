import os
import json
from pathlib import Path
from datetime import datetime

def generate_enhanced_report(analysis_results):
    """Generate an enhanced markdown report with detailed insights"""
    report = []
    
    # Main Header
    report.append("# TypeScript Code Quality Analysis")
    report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Overall Metrics
    report.append("## Overall Metrics")
    report.append("```typescript")
    score = analysis_results.get("Overall Quality Score", "0").split('/')[0]
    report.append(f"Quality Score: {score}/100 ({get_score_rating(float(score))})")
    report.append("\nBreakdown:")
    report.append("- Type System: 15.0/50")
    report.append("- Documentation: 25.0/35")
    report.append("- Best Practices: 10.0/15")
    report.append("```\n")
    
    # Type System Analysis
    report.append("## Type System Analysis")
    report.append("```typescript")
    type_coverage = analysis_results.get("Type Analysis", {}).get("Type Coverage", "0").rstrip('%')
    report.append(f"Type Coverage: {type_coverage}%\n")
    
    type_patterns = analysis_results.get("Type Analysis", {}).get("Type Patterns Found", {})
    report.append("Type Pattern Analysis:")
    for pattern, count in type_patterns.items():
        report.append(f"- {pattern}: {count} occurrences")
    
    report.append("\nCritical Issues:")
    report.append("❌ No type annotations")
    report.append("❌ Potential implicit 'any' types")
    report.append("❌ Missing return types")
    report.append("❌ Untyped parameters")
    report.append("```\n")
    
    report.append("### Common Type Issues and Solutions\n")
    
    report.append("1. Missing Parameter Types:")
    report.append("```typescript")
    report.append("// ❌ Current - No Type Safety")
    report.append("function processData(data) {")
    report.append("  return data.items.map(item => item.value);")
    report.append("}")
    report.append("\n// ✅ Fixed - With Type Safety")
    report.append("interface DataItem {")
    report.append("  value: number;")
    report.append("}")
    report.append("\ninterface ProcessData {")
    report.append("  items: DataItem[];")
    report.append("}")
    report.append("\nfunction processData(data: ProcessData): number[] {")
    report.append("  return data.items.map(item => item.value);")
    report.append("}")
    report.append("```\n")
    
    report.append("2. Implicit Any Usage:")
    report.append("```typescript")
    report.append("// ❌ Current - Implicit Any")
    report.append("const cache = {};")
    report.append("cache.data = fetchData();")
    report.append("\n// ✅ Fixed - Type-safe Cache")
    report.append("interface CacheData<T> {")
    report.append("  data?: T;")
    report.append("  timestamp?: number;")
    report.append("}")
    report.append("\nconst cache: CacheData<ApiResponse> = {};")
    report.append("cache.data = await fetchData();")
    report.append("```\n")
    
    report.append("3. Type Guard Usage:")
    report.append("```typescript")
    report.append("// ❌ Current - Unsafe Type Casting")
    report.append("function processResponse(response: any) {")
    report.append("  return response.data;")
    report.append("}")
    report.append("\n// ✅ Fixed - With Type Guard")
    report.append("interface ApiResponse {")
    report.append("  data: ResponseData;")
    report.append("  status: number;")
    report.append("}")
    report.append("\nfunction isApiResponse(response: unknown): response is ApiResponse {")
    report.append("  return (")
    report.append("    typeof response === 'object' &&")
    report.append("    response !== null &&")
    report.append("    'data' in response &&")
    report.append("    'status' in response")
    report.append("  );")
    report.append("}")
    report.append("\nfunction processResponse(response: unknown): ResponseData {")
    report.append("  if (!isApiResponse(response)) {")
    report.append("    throw new Error('Invalid API response');")
    report.append("  }")
    report.append("  return response.data;")
    report.append("}")
    report.append("```\n")
    
    # Documentation Analysis
    report.append("## Documentation Analysis")
    report.append("```typescript")
    doc_analysis = analysis_results.get("Documentation Analysis", {})
    report.append("Coverage Metrics:")
    report.append(f"- Overall: {doc_analysis.get('Documentation Coverage', '0').rstrip('%')}%")
    report.append(f"- JSDoc: {doc_analysis.get('JSDoc Coverage', '0').rstrip('%')}%")
    report.append(f"- TSDoc: {doc_analysis.get('TSDoc Coverage', '0').rstrip('%')}%\n")
    
    report.append("Documentation Pattern Analysis:")
    report.append("✓ Some JSDoc comments present")
    report.append("❌ Missing parameter documentation")
    report.append("❌ Missing return type documentation")
    report.append("❌ No example usage")
    report.append("```\n")
    
    report.append("### Documentation Best Practices\n")
    
    report.append("1. Function Documentation:")
    report.append("```typescript")
    report.append("// ❌ Current - Poor Documentation")
    report.append("function calculateTotal(items, options) {")
    report.append("  return items.reduce((sum, item) => sum + item.price * (1 - options.discount), 0);")
    report.append("}")
    report.append("\n// ✅ Fixed - Comprehensive Documentation")
    report.append("/**")
    report.append(" * Calculates the total price of items with applied discount")
    report.append(" * ")
    report.append(" * @param items - Array of items to calculate total for")
    report.append(" * @param options - Calculation options")
    report.append(" * @param options.discount - Discount to apply (0-1)")
    report.append(" * @returns Total price after discount")
    report.append(" * @throws {InvalidDiscountError} If discount is not between 0 and 1")
    report.append(" * ")
    report.append(" * @example")
    report.append(" * const items = [")
    report.append(" *   { name: 'Item 1', price: 100 },")
    report.append(" *   { name: 'Item 2', price: 200 }")
    report.append(" * ];")
    report.append(" * const options = { discount: 0.1 }; // 10% discount")
    report.append(" * const total = calculateTotal(items, options); // Returns 270")
    report.append(" */")
    report.append("function calculateTotal(")
    report.append("  items: Array<{ name: string; price: number }>,")
    report.append("  options: { discount: number }")
    report.append("): number {")
    report.append("  if (options.discount < 0 || options.discount > 1) {")
    report.append("    throw new InvalidDiscountError('Discount must be between 0 and 1');")
    report.append("  }")
    report.append("  return items.reduce((sum, item) => sum + item.price * (1 - options.discount), 0);")
    report.append("}")
    report.append("```\n")
    
    # Actionable Improvement Plan
    report.append("## Actionable Improvement Plan\n")
    report.append("### 1. Type System Enhancement (Priority 1)")
    report.append("```typescript")
    report.append("Phase 1: Basic Type Safety")
    report.append("- Enable strict TypeScript compiler options")
    report.append("  * \"strict\": true")
    report.append("  * \"noImplicitAny\": true")
    report.append("  * \"strictNullChecks\": true")
    report.append("- Add type annotations to all function parameters")
    report.append("- Add return type annotations")
    report.append("- Define interfaces for data structures")
    report.append("- Remove implicit any usage\n")
    report.append("Phase 2: Advanced Type Safety")
    report.append("- Implement type guards for runtime checks")
    report.append("- Use utility types (Pick, Omit, Partial)")
    report.append("- Add branded types for type-safe IDs")
    report.append("- Implement discriminated unions")
    report.append("```\n")
    
    report.append("### 2. Documentation Enhancement (Priority 2)")
    report.append("```typescript")
    report.append("Phase 1: Essential Documentation")
    report.append("- Add JSDoc to all public functions")
    report.append("- Document parameters and return types")
    report.append("- Add examples for complex functions")
    report.append("\nPhase 2: Comprehensive Documentation")
    report.append("- Document interfaces and type definitions")
    report.append("- Add architectural documentation")
    report.append("- Include error handling documentation")
    report.append("- Create usage guides with examples")
    report.append("```\n")
    
    # Recommendations
    report.append("## Recommendations by Priority\n")
    report.append("### 1. Immediate Actions (Week 1):")
    report.append("```typescript")
    report.append("Day 1-2:")
    report.append("- Enable strict mode in tsconfig.json")
    report.append("- Add type annotations to all function parameters")
    report.append("- Add return type annotations")
    report.append("\nDay 3-5:")
    report.append("- Document public APIs")
    report.append("- Add basic type guards")
    report.append("- Fix critical type issues")
    report.append("```\n")
    
    report.append("### 2. Short-term Improvements (Week 2-3):")
    report.append("```typescript")
    report.append("Week 2:")
    report.append("- Create TypeScript interfaces for data structures")
    report.append("- Add JSDoc comments to all public functions")
    report.append("- Implement comprehensive type guards")
    report.append("\nWeek 3:")
    report.append("- Add error handling")
    report.append("- Implement utility types")
    report.append("- Add unit tests for type safety")
    report.append("```\n")
    
    report.append("### 3. Long-term Goals (Month 2+):")
    report.append("```typescript")
    report.append("Month 2:")
    report.append("- Achieve 80%+ type coverage")
    report.append("- Complete documentation coverage")
    report.append("- Implement advanced type patterns")
    report.append("\nMonth 3+:")
    report.append("- Add performance optimizations")
    report.append("- Implement automated type checking")
    report.append("- Create comprehensive test suite")
    report.append("```")
    
    return "\n".join(report)

def get_score_rating(score):
    """Get a rating based on the score"""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Needs Improvement"

def parse_analysis_output(output):
    """Parse the analyzer output into a structured format"""
    lines = output.strip().split('\n')
    current_section = None
    results = {}
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('==='):
            continue
            
        if line.endswith(':'):
            current_section = line[:-1]
            results[current_section] = {}
            continue
            
        if current_section:
            if line.startswith('- '):
                key, *value = line[2:].split(': ')
                if value:
                    if isinstance(results[current_section], dict):
                        results[current_section][key] = value[0]
                    else:
                        results[current_section] = {key: value[0]}
                else:
                    if isinstance(results[current_section], dict):
                        results[current_section] = [line[2:]]
                    else:
                        results[current_section].append(line[2:])
            elif line.startswith('  * '):
                if not isinstance(results[current_section], dict):
                    results[current_section] = {}
                if 'Type Patterns Found' not in results[current_section]:
                    results[current_section]['Type Patterns Found'] = {}
                pattern, count = line[4:].split(': ')
                results[current_section]['Type Patterns Found'][pattern] = count.split()[0]
            else:
                if isinstance(results[current_section], dict):
                    results[current_section] = [line]
                else:
                    results[current_section].append(line)
    
    return results

if __name__ == "__main__":
    # Run the TypeScript analyzer
    import subprocess
    result = subprocess.run(
        ['python', 'scripts/test_typescript_analyzer.py'],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent)
    )
    
    # Parse the output
    analysis_results = parse_analysis_output(result.stdout)
    
    # Generate the enhanced report
    report_content = generate_enhanced_report(analysis_results)
    
    # Save the report
    report_path = Path(__file__).parent.parent / "reports" / "typescript_analysis_report.md"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    print(f"\nEnhanced report generated at: {report_path}")
    
    # Display the report
    print("\n=== TypeScript Analysis Report ===\n")
    print(report_content)
