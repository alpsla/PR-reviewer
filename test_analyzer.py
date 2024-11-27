from services.code_analysis.analyzers.typescript_analyzer import TypeScriptAnalyzer

def main():
    analyzer = TypeScriptAnalyzer()
    
    # Read the test file
    with open('test_analysis.ts', 'r') as f:
        content = f.read()
    
    # Analyze the file
    result = analyzer.analyze_file(content, 'test_analysis.ts')
    
    # Print analysis results
    print("\n=== Type Analysis ===")
    print(f"Type Coverage: {result.type_analysis.metrics.type_coverage:.1f}%")
    print(f"Explicit Types: {result.type_analysis.metrics.explicit_types}")
    print(f"Generic Types: {result.type_analysis.metrics.generic_types}")
    print(f"Interfaces: {result.type_analysis.metrics.interfaces}")
    print(f"Utility Types: {result.type_analysis.metrics.utility_types}")
    print(f"Type Guards: {result.type_analysis.metrics.type_guards}")
    print(f"Any Types: {result.type_analysis.metrics.any_types}")
    
    print("\n=== Code Samples ===")
    for sample in result.type_analysis.code_samples:
        print(f"\nLine {sample['line']}:")
        print(f"Code: {sample['code']}")
        print(f"Suggestion: {sample['suggestion']}")
    
    print("\n=== Suggestions ===")
    for suggestion in result.type_analysis.suggestions:
        print(f"- {suggestion}")
    
    print("\n=== Documentation Analysis ===")
    print(f"Documentation Coverage: {result.doc_analysis.metrics.coverage:.1f}%")
    print(f"JSDoc Coverage: {result.doc_analysis.metrics.jsdoc_coverage:.1f}%")
    
    print("\n=== Framework Analysis ===")
    if result.framework_analysis.framework:
        print(f"Framework: {result.framework_analysis.framework}")
        print(f"Patterns: {result.framework_analysis.patterns}")
    else:
        print("No framework detected")
    
    print(f"\nOverall Quality Score: {result.quality_score:.1f}")

if __name__ == '__main__':
    main()
