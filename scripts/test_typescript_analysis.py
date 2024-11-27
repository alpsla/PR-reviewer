import os
import sys
import json

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.code_analysis.analyzers.typescript_analyzer import TypeScriptAnalyzer

def test_typescript_analysis():
    """Test the TypeScript analyzer with a sample TypeScript code."""
    
    # Create a sample TypeScript code
    sample_code = """
interface User {
    id: number;
    name: string;
    email?: string;
}

type UserRole = 'admin' | 'user' | 'guest';

class UserService {
    private users: Map<number, User> = new Map();

    constructor() {}

    async getUser<T extends User>(id: number): Promise<T | null> {
        const user = this.users.get(id);
        return user as T;
    }

    addUser(user: User): void {
        if (this.isValidUser(user)) {
            this.users.set(user.id, user);
        }
    }

    private isValidUser(user: unknown): user is User {
        return typeof user === 'object' && user !== null &&
            'id' in user && typeof user.id === 'number' &&
            'name' in user && typeof user.name === 'string';
    }
}

// Utility type example
type Nullable<T> = T | null;

// Mapped type example
type ReadonlyUser = {
    readonly [K in keyof User]: User[K];
};
"""

    # Create an instance of TypeScriptAnalyzer
    analyzer = TypeScriptAnalyzer()
    
    # Analyze the sample code
    analysis = analyzer.analyze_file(sample_code, 'test.ts')
    
    print("\n=== TypeScript Analysis Results ===")
    
    # Access type analysis results
    if hasattr(analysis, 'type_analysis'):
        print("\nType Analysis:")
        type_metrics = analysis.type_analysis.metrics
        print(f"Type Safety Score: {type_metrics.type_safety_score}")
        print(f"Type Coverage: {type_metrics.type_coverage}")
        print(f"Interfaces Count: {type_metrics.interfaces_count}")
        print(f"Type Aliases Count: {type_metrics.type_aliases_count}")
        print(f"Classes Count: {type_metrics.classes_count}")
        print(f"Generic Types Count: {type_metrics.generic_types_count}")
        print(f"Mapped Types Count: {type_metrics.mapped_types_count}")
        print(f"Utility Types Count: {type_metrics.utility_types_count}")
        print(f"Type Guards Count: {type_metrics.type_guards_count}")
        print(f"Type Assertions Count: {type_metrics.type_assertions_count}")

        if hasattr(analysis.type_analysis, 'examples'):
            print("\nType System Examples:")
            for example in analysis.type_analysis.examples:
                print(f"\n{example.title}:")
                print(f"Location: {example.location}")
                print("Code:")
                print(example.code)
                if example.suggestion:
                    print(f"Suggestion: {example.suggestion}")
    
    # Access documentation analysis results
    if hasattr(analysis, 'doc_analysis'):
        print("\nDocumentation Analysis:")
        doc_metrics = analysis.doc_analysis.metrics
        print(f"Documentation Coverage: {doc_metrics.jsdoc_coverage}")
        print(f"Total Functions: {doc_metrics.total_functions}")
        print(f"Documented Functions: {doc_metrics.documented_functions}")
        print(f"Total Classes: {doc_metrics.total_classes}")
        print(f"Documented Classes: {doc_metrics.documented_classes}")
        print(f"Total Interfaces: {doc_metrics.total_interfaces}")
        print(f"Documented Interfaces: {doc_metrics.documented_interfaces}")

        if hasattr(analysis.doc_analysis, 'examples'):
            print("\nMissing Documentation Examples:")
            for example in analysis.doc_analysis.examples:
                print(f"\n{example.title}:")
                print(f"Location: {example.location}")
                print("Code:")
                print(example.code)
                if example.suggestion:
                    print(f"Suggestion: {example.suggestion}")
    
    # Access framework analysis results
    if hasattr(analysis, 'framework_analysis'):
        print("\nFramework Analysis:")
        print(f"Framework Patterns: {analysis.framework_analysis}")

        if hasattr(analysis.framework_analysis, 'examples'):
            print("\nFramework Pattern Examples:")
            for example in analysis.framework_analysis.examples:
                print(f"\n{example.title}:")
                print(f"Location: {example.location}")
                print("Code:")
                print(example.code)
                if example.suggestion:
                    print(f"Suggestion: {example.suggestion}")
    
    # Access complexity and health scores
    if hasattr(analysis, 'complexity_score'):
        print(f"\nComplexity Score: {analysis.complexity_score}")
    if hasattr(analysis, 'health_score'):
        print(f"Health Score: {analysis.health_score}")
    
    # Access quality gates
    if hasattr(analysis, 'quality_gates'):
        print("\nQuality Gates:")
        for gate in analysis.quality_gates:
            print(f"- {gate.name}: {'Passed' if gate.passed else 'Failed'}")
            if not gate.passed:
                print(f"  Reason: {gate.message}")
    
    # Access action items
    if hasattr(analysis, 'action_items'):
        print("\nAction Items:")
        for item in analysis.action_items:
            print(f"- {item}")

if __name__ == "__main__":
    test_typescript_analysis()
