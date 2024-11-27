import os
import json
from pathlib import Path
from datetime import datetime

def generate_html_report(analysis_results):
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>TypeScript Analysis Report</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px; 
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
            }
            .header { 
                background: #f8f9fa; 
                padding: 20px; 
                border-radius: 5px; 
                margin-bottom: 20px; 
            }
            .section { 
                margin-bottom: 30px; 
            }
            .metric { 
                margin: 10px 0; 
            }
            .issue { 
                background: #fff3cd; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 10px 0; 
            }
            .improvement { 
                background: #d4edda; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 10px 0; 
            }
            .score { 
                font-size: 24px; 
                font-weight: bold; 
            }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin: 15px 0; 
            }
            th, td { 
                padding: 12px; 
                text-align: left; 
                border-bottom: 1px solid #ddd; 
            }
            th { 
                background: #f8f9fa; 
            }
            .chart { 
                width: 100%; 
                height: 20px; 
                background: #eee; 
                border-radius: 10px; 
                overflow: hidden; 
            }
            .chart-fill { 
                height: 100%; 
                background: #007bff; 
                transition: width 0.5s ease; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>TypeScript Analysis Report</h1>
                <p>Generated on: {date}</p>
            </div>

            <div class="section">
                <h2>Overall Quality Score</h2>
                <div class="score">{score}/100</div>
                <div class="chart">
                    <div class="chart-fill" style="width: {score}%;"></div>
                </div>
            </div>

            <div class="section">
                <h2>Type Analysis</h2>
                <div class="metric">
                    <h3>Type Coverage: {type_coverage}%</h3>
                    <div class="chart">
                        <div class="chart-fill" style="width: {type_coverage}%;"></div>
                    </div>
                </div>
                <h3>Type Patterns Found:</h3>
                <table>
                    <tr>
                        <th>Pattern</th>
                        <th>Occurrences</th>
                    </tr>
                    {type_patterns}
                </table>
            </div>

            <div class="section">
                <h2>Documentation Analysis</h2>
                <div class="metric">
                    <h3>Overall Documentation Coverage: {doc_coverage}%</h3>
                    <div class="chart">
                        <div class="chart-fill" style="width: {doc_coverage}%;"></div>
                    </div>
                </div>
                <div class="metric">
                    <h3>JSDoc Coverage: {jsdoc_coverage}%</h3>
                    <div class="chart">
                        <div class="chart-fill" style="width: {jsdoc_coverage}%;"></div>
                    </div>
                </div>
                <div class="metric">
                    <h3>TSDoc Coverage: {tsdoc_coverage}%</h3>
                    <div class="chart">
                        <div class="chart-fill" style="width: {tsdoc_coverage}%;"></div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>Critical Issues</h2>
                {critical_issues}
            </div>

            <div class="section">
                <h2>Quality Improvements</h2>
                {quality_improvements}
            </div>
        </div>
    </body>
    </html>
    '''.format(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        score=analysis_results.get("Overall Quality Score", "0").split('/')[0],
        type_coverage=analysis_results.get("Type Analysis", {}).get("Type Coverage", "0").rstrip('%'),
        doc_coverage=analysis_results.get("Documentation Analysis", {}).get("Documentation Coverage", "0").rstrip('%'),
        jsdoc_coverage=analysis_results.get("Documentation Analysis", {}).get("JSDoc Coverage", "0").rstrip('%'),
        tsdoc_coverage=analysis_results.get("Documentation Analysis", {}).get("TSDoc Coverage", "0").rstrip('%'),
        type_patterns="\n".join(
            f'<tr><td>{pattern}</td><td>{count}</td></tr>'
            for pattern, count in analysis_results.get("Type Analysis", {}).get("Type Patterns Found", {}).items()
        ),
        critical_issues="\n".join(
            f'<div class="issue"><h3>{issue}</h3><p>Line {line}: {details}</p><p>Suggestion: {suggestion}</p></div>'
            for issue, line, details, suggestion in [
                issue.split('\n') for issue in analysis_results.get("Critical Issues", [])
                if isinstance(issue, str) and '\n' in issue
            ]
        ),
        quality_improvements="\n".join(
            f'<div class="improvement"><p>{improvement}</p></div>'
            for improvement in analysis_results.get("Quality Improvements", [])
        )
    )

    # Write the HTML report
    report_path = Path(__file__).parent.parent / "reports" / "typescript_analysis_report.html"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(html)
    
    return str(report_path)

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
    
    # Generate the HTML report
    report_path = generate_html_report(analysis_results)
    print(f"\nHTML report generated at: {report_path}")
    
    # Try to open the report in the default browser
    import webbrowser
    webbrowser.open(f'file://{report_path}')
