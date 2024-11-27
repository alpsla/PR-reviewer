import json
import sys
from pathlib import Path
from typing import Any, Dict
import ast

def print_header(text: str, level: int = 1) -> None:
    """Print a formatted header"""
    prefix = "#" * level
    print(f"\n{prefix} {text}\n")

def print_code_block(code: str, language: str = "typescript") -> None:
    """Print a formatted code block"""
    print(f"```{language}")
    print(code.strip())
    print("```\n")

def print_metrics(metrics: Dict[str, Any], indent: str = "") -> None:
    """Print metrics in a readable format"""
    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"{indent}{key}:")
            print_metrics(value, indent + "  ")
        else:
            if isinstance(value, float):
                print(f"{indent}{key}: {value:.1f}")
            else:
                print(f"{indent}{key}: {value}")

def print_recommendations(recs: Dict[str, Any]) -> None:
    """Print recommendations in a structured format"""
    for category, priorities in recs.items():
        print_header(category.replace("_", " ").title(), 3)
        for priority, items in priorities.items():
            print(f"**{priority.title()}:**")
            for item in items:
                print(f"- {item}")
        print()

def display_report(report_data: Dict[str, Any]) -> None:
    """Display the TypeScript analysis report in a readable format"""
    # Metadata and Summary
    print_header(f"TypeScript PR Analysis Report - {report_data['metadata']['repository']} #{report_data['metadata']['prNumber']}")
    
    print("## Executive Summary\n")
    print(report_data['summary']['description'])
    
    print("\n**Critical Issues:**")
    for issue in report_data['summary']['criticalIssues']:
        print(f"- {issue}")
    
    print("\n**Strengths:**")
    for strength in report_data['summary']['strengths']:
        print(f"- {strength}")

    # File Analyses
    print_header("File Analyses", 2)
    for file_analysis in report_data['fileAnalyses']:
        print_header(f"Analysis of `{file_analysis['path']}`", 3)
        
        # Type Analysis
        print("### Type System Analysis")
        print_code_block(f"""
Critical Metrics:
- Type Coverage: {file_analysis['typeAnalysis']['metrics']['coverage']}%
- Any Types: {file_analysis['typeAnalysis']['metrics']['anyTypes']}
- Utility Types: {file_analysis['typeAnalysis']['metrics']['utilityTypes']}
- Type Guards: {file_analysis['typeAnalysis']['metrics']['typeGuards']}

Issues Found:""")
        
        for issue in file_analysis['typeAnalysis']['issues']:
            print_code_block(f"""
// Issue: {issue['description']} (Severity: {issue['severity']})

// Current Implementation:
{issue['currentCode']}

// Recommended Fix:
{issue['recommendedFix']}
""")

        # Documentation Analysis
        print("### Documentation Analysis")
        print_code_block(f"""
Coverage Metrics:
- Overall: {file_analysis['documentationAnalysis']['coverage']['overall']}%
- JSDoc: {file_analysis['documentationAnalysis']['coverage']['jsDoc']}%
- TSDoc: {file_analysis['documentationAnalysis']['coverage']['tsDoc']}%
""")

        for rec in file_analysis['documentationAnalysis']['recommendations']:
            print_code_block(rec['example'])

        # Code Quality
        print("### Code Quality Analysis")
        print_code_block(f"""
Complexity Metrics:
- Cognitive Complexity: {file_analysis['codeQuality']['complexity']['cognitive']}
- Cyclomatic Complexity: {file_analysis['codeQuality']['complexity']['cyclomatic']}
- Maintainability Index: {file_analysis['codeQuality']['complexity']['maintainability']}

Good Practices:
{chr(10).join(f'- {practice}' for practice in file_analysis['codeQuality']['patterns']['goodPractices'])}

Areas for Improvement:
{chr(10).join(f'- {improvement}' for improvement in file_analysis['codeQuality']['patterns']['improvements'])}
""")

        print(f"\n**Quality Score:** {file_analysis['score']}/100\n")

    # Recommendations
    print_header("Actionable Recommendations", 2)
    print_recommendations(report_data['recommendations'])

    # Implementation Plan
    print_header("Implementation Plan", 2)
    for phase in report_data['implementationPlan']['phases']:
        print(f"### Phase: {phase['name']} ({phase['duration']})")
        print("\n**Tasks:**")
        for task in phase['tasks']:
            print(f"- {task}")
        print(f"\n**Expected Outcome:** {phase['expectedOutcome']}\n")

    # Quality Metrics
    print_header("Quality Metrics", 2)
    print("### Current vs Target Metrics")
    print_code_block(f"""
Type Safety:
Current:
  - Coverage: {report_data['qualityMetrics']['current']['typeSafety']['coverage']}%
  - Any Types: {report_data['qualityMetrics']['current']['typeSafety']['anyTypes']}
  - Utility Types: {report_data['qualityMetrics']['current']['typeSafety']['utilityTypes']}
Target:
  - Coverage: {report_data['qualityMetrics']['target']['typeSafety']['coverage']}%
  - Any Types: {report_data['qualityMetrics']['target']['typeSafety']['anyTypes']}
  - Utility Types: {report_data['qualityMetrics']['target']['typeSafety']['utilityTypes']}

Documentation:
Current:
  - Overall: {report_data['qualityMetrics']['current']['documentation']['overall']}%
  - JSDoc: {report_data['qualityMetrics']['current']['documentation']['jsDoc']}%
  - TSDoc: {report_data['qualityMetrics']['current']['documentation']['tsDoc']}%
Target:
  - Overall: {report_data['qualityMetrics']['target']['documentation']['overall']}%
  - JSDoc: {report_data['qualityMetrics']['target']['documentation']['jsDoc']}%
  - TSDoc: {report_data['qualityMetrics']['target']['documentation']['tsDoc']}%

Quality Score:
  - Current: {report_data['qualityMetrics']['current']['qualityScore']}/100
  - Target: {report_data['qualityMetrics']['target']['qualityScore']}/100
""")

if __name__ == "__main__":
    report_path = Path(__file__).parent.parent / "reports" / "typescript_analysis_report.ts"
    
    # Read and parse the TypeScript file
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the report object
    start_idx = content.find('const report: AnalysisReport = {')
    end_idx = content.rfind('};')
    
    if start_idx == -1 or end_idx == -1:
        print("Error: Could not find report data in the TypeScript file")
        sys.exit(1)
    
    # Get just the JSON-like object
    report_str = content[start_idx + len('const report: AnalysisReport = '):end_idx + 1]
    
    # Convert TypeScript to valid JSON
    report_str = report_str.replace("'", '"')  # Replace single quotes with double quotes
    report_str = report_str.replace("True", "true")  # Fix boolean values
    report_str = report_str.replace("False", "false")
    
    try:
        # Parse the JSON data
        report_data = json.loads(report_str)
        
        # Display the report
        display_report(report_data)
    except json.JSONDecodeError as e:
        print(f"Error parsing report data: {e}")
        sys.exit(1)
