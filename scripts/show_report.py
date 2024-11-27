from pathlib import Path

def print_section(title, content="", level=1):
    """Print a section with proper markdown formatting"""
    print(f"\n{'#' * level} {title}\n")
    if content:
        print(content)

def format_code(code):
    """Format code block with proper markdown"""
    return f"```typescript\n{code}\n```\n"

def main():
    report_path = Path(__file__).parent.parent / "reports" / "typescript_analysis_report.ts"
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Print the report in a formatted way
    print_section("TypeScript PR Analysis Report", level=1)
    
    # Print Interfaces
    print_section("Report Structure", level=2)
    interfaces_section = content[content.find("interface AnalysisReport"):content.find("// Actual Report Data")]
    print(format_code(interfaces_section))
    
    # Print Report Data
    print_section("Analysis Results", level=2)
    report_data = content[content.find("const report: AnalysisReport = {"):]
    print(format_code(report_data))

if __name__ == "__main__":
    main()
