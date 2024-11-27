import os
import json
from pathlib import Path
from datetime import datetime

def generate_markdown_report(analysis_results):
    """Generate a markdown report from the analysis results"""
    report = []
    
    # Header
    report.append("# TypeScript Analysis Report")
    report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Overall Score
    report.append("## Overall Quality Score")
    score = analysis_results.get("Overall Quality Score", "0").split('/')[0]
    report.append(f"**Score:** {score}/100\n")
    
    # Type Analysis
    report.append("## Type Analysis")
    type_coverage = analysis_results.get("Type Analysis", {}).get("Type Coverage", "0").rstrip('%')
    report.append(f"**Type Coverage:** {type_coverage}%\n")
    
    report.append("### Type Patterns Found:")
    patterns = analysis_results.get("Type Analysis", {}).get("Type Patterns Found", {})
    for pattern, count in patterns.items():
        report.append(f"- {pattern}: {count}")
    report.append("")
    
    # Documentation Analysis
    report.append("## Documentation Analysis")
    doc_analysis = analysis_results.get("Documentation Analysis", {})
    report.append(f"**Overall Coverage:** {doc_analysis.get('Documentation Coverage', '0').rstrip('%')}%")
    report.append(f"**JSDoc Coverage:** {doc_analysis.get('JSDoc Coverage', '0').rstrip('%')}%")
    report.append(f"**TSDoc Coverage:** {doc_analysis.get('TSDoc Coverage', '0').rstrip('%')}%\n")
    
    # Critical Issues
    report.append("## Critical Issues")
    critical_issues = analysis_results.get("Critical Issues", [])
    for issue in critical_issues:
        if isinstance(issue, str):
            parts = issue.split('\n')
            if len(parts) >= 3:
                report.append(f"### {parts[0]}")
                report.append(f"**Location:** Line {parts[1]}")
                report.append(f"**Details:** {parts[2]}")
                if len(parts) > 3:
                    report.append(f"**Suggestion:** {parts[3]}")
                report.append("")
    
    # Quality Improvements
    report.append("## Quality Improvements")
    improvements = analysis_results.get("Quality Improvements", [])
    for improvement in improvements:
        report.append(f"- {improvement}")
    
    return "\n".join(report)

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
    
    # Generate the markdown report
    report_content = generate_markdown_report(analysis_results)
    
    # Save the report
    report_path = Path(__file__).parent.parent / "reports" / "typescript_analysis_report.md"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    print(f"\nReport generated at: {report_path}")
    
    # Display the report
    print("\n=== TypeScript Analysis Report ===\n")
    print(report_content)
