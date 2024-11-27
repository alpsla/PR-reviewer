import re
import sys
import os
from pathlib import Path
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional
from dotenv import load_dotenv
import json
from dataclasses import dataclass
from github import Github
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from services.github_service import GitHubService
from github.GithubException import RateLimitExceededException

# Load environment variables
load_dotenv()

class FrameworkType(Enum):
    """Supported framework types"""
    REACT = auto()
    ANGULAR = auto()
    VUE = auto()
    NONE = auto()

class TypeMetrics:
    """Class to store TypeScript code metrics"""
    def __init__(self):
        # Type coverage metrics
        self.type_coverage = 0.0
        self.type_safety_score = 0.0
        self.quality_score = 0.0
        
        # Type structure metrics
        self.classes = 0
        self.interfaces = 0
        self.type_aliases = 0
        self.generic_types = 0
        
        # Type safety metrics
        self.type_guards = 0
        self.type_assertions = 0
        self.any_types = 0
        self.untyped_functions = 0
        self.implicit_returns = 0
        
        # Advanced type features
        self.mapped_types = 0
        self.utility_types = 0
        self.branded_types = 0
        self.type_predicates = 0
        
        # Documentation metrics
        self.doc_coverage = 0.0
        self.jsdoc_coverage = 0.0
        self.param_doc_coverage = 0.0
        self.return_doc_coverage = 0.0

    def calculate_quality_score(self) -> float:
        """Calculate overall quality score based on various metrics"""
        type_score = (
            (self.type_coverage * 0.4) +
            ((100 - self.any_types * 2) * 0.3) +
            (min(100, self.type_guards / 5) * 0.3)
        )
        
        doc_score = (
            (self.doc_coverage * 0.4) +
            (self.jsdoc_coverage * 0.3) +
            (self.param_doc_coverage * 0.3)
        )
        
        safety_score = (
            ((100 - self.type_assertions / 10) * 0.4) +
            (min(100, self.type_guards * 2) * 0.3) +
            ((100 - self.untyped_functions * 2) * 0.3)
        )
        
        advanced_score = (
            (min(100, self.utility_types * 5) * 0.4) +
            (min(100, self.branded_types * 10) * 0.3) +
            (min(100, self.mapped_types * 5) * 0.3)
        )
        
        self.quality_score = (
            type_score * 0.4 +
            doc_score * 0.3 +
            safety_score * 0.2 +
            advanced_score * 0.1
        )
        
        return self.quality_score

class TypeAnalysis:
    """Analysis results for TypeScript code"""
    def __init__(self):
        self.metrics = TypeMetrics()
        self.issues = []
        self.suggestions = []

class FrameworkAnalysis:
    """Analysis results for framework-specific patterns"""
    def __init__(self):
        self.framework_type = FrameworkType.NONE
        self.component_patterns = []
        self.hook_usage = []
        self.prop_patterns = []

class Analysis:
    """Complete analysis results"""
    def __init__(self):
        self.type_analysis = TypeAnalysis()
        self.framework_analysis = None

def calculate_doc_coverage(code):
    """Calculate documentation coverage percentage"""
    total_items = len(re.findall(r'\b(function|class|interface|type)\b', code))
    documented_items = len(re.findall(r'/\*\*[\s\S]*?\*/\s*\b(function|class|interface|type)\b', code))
    return (documented_items / max(1, total_items)) * 100

def analyze_typescript_code(code: str) -> TypeMetrics:
    """Analyze TypeScript code and return metrics"""
    metrics = TypeMetrics()
    
    # Count explicit types
    metrics.explicit_types = code.count(': ') + code.count('as ') + code.count('type ') + code.count('interface ')
    
    # Count generic types
    metrics.generic_types = code.count('<') - code.count('<=') - code.count('>=')
    if metrics.generic_types < 0:
        metrics.generic_types = 0
    
    # Count interfaces
    metrics.interfaces = code.count('interface ')
    
    # Count type guards
    metrics.type_guards = code.count(' is ') + code.count('instanceof ')
    
    # Count any types
    metrics.any_types = code.count(': any') + code.count('as any')
    
    # Count type assertions
    metrics.type_assertions = code.count('as ') + code.count('<') - code.count('<=') - code.count('>=')
    if metrics.type_assertions < 0:
        metrics.type_assertions = 0
    
    # Count type aliases
    metrics.type_aliases = code.count('type ')
    
    # Count classes and functions
    metrics.classes = code.count('class ')
    metrics.functions = code.count('function ') + code.count('=>')
    
    # Count variables and parameters
    metrics.variables = len(re.findall(r'\b(const|let|var)\s+\w+', code))
    metrics.parameters = len(re.findall(r'\([^)]*\)', code))
    
    # Count type annotations
    metrics.type_annotations = len(re.findall(r':\s*[A-Za-z][\w<>]*', code))
    
    # Count branded and utility types
    metrics.branded_types = len(re.findall(r'&\s*{\s*readonly\s+[^:]+:\s*[^;]+}', code))
    metrics.utility_types = len(re.findall(r'\b(Partial|Readonly|Record|Pick|Omit|Exclude|Extract|NonNullable|ReturnType|Parameters|InstanceType)<', code))
    
    # Count untyped functions and implicit returns
    metrics.untyped_functions = len(re.findall(r'function\s+\w+\s*\([^:)]*\)', code))
    metrics.implicit_returns = len(re.findall(r'=>\s*[^{]', code))
    
    # Count null checks
    metrics.null_checks = len(re.findall(r'(===?\s*null|!==?\s*null|===?\s*undefined|!==?\s*undefined)', code))
    
    # Calculate type coverage
    total_types = metrics.explicit_types + metrics.any_types
    metrics.type_coverage = (metrics.explicit_types / total_types * 100) if total_types > 0 else 0
    
    # Calculate documentation coverage
    total_lines = len(code.splitlines())
    doc_lines = len([line for line in code.splitlines() if '/**' in line or '*/' in line or ' * ' in line])
    metrics.doc_coverage = (doc_lines / total_lines * 100) if total_lines > 0 else 0
    
    # Calculate JSDoc coverage for functions, classes, and interfaces
    jsdoc_blocks = len(re.findall(r'/\*\*[\s\S]*?\*/', code))
    total_documentable = metrics.functions + metrics.classes + metrics.interfaces
    metrics.jsdoc_coverage = (jsdoc_blocks / total_documentable * 100) if total_documentable > 0 else 0
    
    # Calculate parameter documentation coverage
    param_doc_count = code.count('@param')
    metrics.param_doc_coverage = (param_doc_count / metrics.parameters * 100) if metrics.parameters > 0 else 0
    
    # Calculate return type documentation coverage
    return_doc_count = code.count('@returns') + code.count('@return')
    metrics.return_doc_coverage = (return_doc_count / metrics.functions * 100) if metrics.functions > 0 else 0
    
    # Calculate overall type safety score
    type_safety_score = (
        metrics.type_coverage * 0.3 +  # Type coverage is important
        (100 - (metrics.any_types * 5)) * 0.15 +  # Penalize 'any' types
        (metrics.type_guards * 2) * 0.1 +  # Reward type guards
        (100 - (metrics.type_assertions * 2)) * 0.1 +  # Penalize type assertions
        metrics.doc_coverage * 0.1 +  # Documentation is important for type safety
        metrics.jsdoc_coverage * 0.1 +  # JSDoc helps with type inference
        (metrics.branded_types * 5) * 0.05 +  # Reward branded types
        (metrics.utility_types * 2) * 0.05 +  # Reward utility types
        (100 - (metrics.untyped_functions * 2)) * 0.05  # Penalize untyped functions
    )
    metrics.type_safety_score = max(0, min(100, type_safety_score))  # Clamp between 0 and 100
    
    metrics.calculate_quality_score()
    
    return metrics

def extract_examples(code: str) -> Dict[str, List[str]]:
    """Extract code examples from TypeScript code"""
    examples = {
        'interfaces': [],
        'type_guards': [],
        'generics': [],
        'type_aliases': [],
        'classes': [],
        'functions': []
    }
    
    lines = code.splitlines()
    current_block = []
    current_type = None
    
    for line in lines:
        # Interface examples
        if 'interface ' in line:
            current_type = 'interfaces'
            current_block = [line]
        # Type guard examples
        elif ' is ' in line or 'instanceof' in line:
            current_type = 'type_guards'
            current_block = [line]
        # Generic examples
        elif '<' in line and '>' in line and ('type ' in line or 'interface ' in line or 'function ' in line):
            current_type = 'generics'
            current_block = [line]
        # Type alias examples
        elif 'type ' in line:
            current_type = 'type_aliases'
            current_block = [line]
        # Class examples
        elif 'class ' in line:
            current_type = 'classes'
            current_block = [line]
        # Function examples
        elif 'function ' in line or '=>' in line:
            current_type = 'functions'
            current_block = [line]
        # Continue collecting block
        elif current_block and (line.strip().startswith('}') or line.strip() == ''):
            current_block.append(line)
            if current_type and len(current_block) > 1:
                examples[current_type].append('\n'.join(current_block))
            current_block = []
            current_type = None
        # Add to current block
        elif current_block:
            current_block.append(line)
    
    return examples

def analyze_typescript_file(content: str) -> TypeMetrics:
    """Analyze TypeScript file content and return metrics"""
    from scripts.analyze_typescript import analyze_typescript_file as analyze_file
    return analyze_file(content)

def wait_for_rate_limit(g: Github):
    """Wait if we hit the rate limit"""
    rate_limit = g.get_rate_limit()
    if rate_limit.core.remaining == 0:
        reset_timestamp = rate_limit.core.reset.timestamp()
        sleep_time = reset_timestamp - time.time() + 1  # Add 1 second buffer
        if sleep_time > 0:
            logger.info(f"Rate limit hit. Waiting {sleep_time:.0f} seconds...")
            time.sleep(sleep_time)

def analyze_pr(g: Github, repo_name: str, pr_number: int):
    """Analyze a single PR"""
    try:
        logger.info(f"Attempting to access repository: {repo_name}")
        repo = g.get_repo(repo_name)
        
        logger.info(f"Checking rate limits...")
        wait_for_rate_limit(g)
        
        logger.info(f"Fetching PR #{pr_number}")
        pr = repo.get_pull(pr_number)
        
        logger.info(f"Analyzing PR #{pr_number} from {repo_name}")
        logger.info(f"Title: {pr.title}")
        logger.info(f"Files changed: {pr.changed_files}")
        
        # Create analyzer
        analyzer = GitHubService()
        results = {
            'pr_info': {
                'number': pr_number,
                'title': pr.title,
                'url': pr.html_url,
                'changed_files': pr.changed_files
            },
            'analysis_results': []
        }
        
        # Analyze each TypeScript file
        for file in pr.get_files():
            if not file.filename.endswith(('.ts', '.tsx')):
                continue
                
            logger.info(f"Analyzing file: {file.filename}")
            
            try:
                file_content = repo.get_contents(file.filename, ref=pr.head.sha).decoded_content.decode('utf-8')
                analysis = analyzer.analyze_file(file_content, file.filename)
                results['analysis_results'].append({
                    'file': file.filename,
                    'metrics': analysis
                })
            except Exception as e:
                logger.error(f"Error analyzing file {file.filename}: {str(e)}")
                results['analysis_results'].append({
                    'file': file.filename,
                    'error': str(e)
                })
        
        return results
        
    except GithubException as e:
        if e.status == 404:
            logger.error(f"PR or repository not found: {repo_name}#{pr_number}")
        elif e.status == 403:
            logger.error("Rate limit exceeded or authentication issue")
            rate_limit = g.get_rate_limit()
            logger.info(f"Current rate limit status: {rate_limit.core}")
        else:
            logger.error(f"GitHub API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

def analyze_multiple_prs(pr_list):
    """Analyze multiple PRs and save results"""
    # Initialize GitHub client
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GitHub token not found in environment variables")
    
    g = Github(github_token)
    all_results = {}
    
    for repo_name, pr_number in pr_list:
        try:
            wait_for_rate_limit(g)
            results = analyze_pr(g, repo_name, pr_number)
            
            if results:
                # Save individual PR results
                output_file = Path('analysis_results') / f"{repo_name.replace('/', '_')}_pr{pr_number}.json"
                output_file.parent.mkdir(exist_ok=True)
                
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2)
                
                logger.info(f"\nAnalysis results saved to {output_file}")
                
                # Add to combined results
                all_results[f"{repo_name}#{pr_number}"] = results
                
        except RateLimitExceededException:
            wait_for_rate_limit(g)
            # Retry this PR
            results = analyze_pr(g, repo_name, pr_number)
            if results:
                all_results[f"{repo_name}#{pr_number}"] = results
    
    # Save combined results
    combined_output = Path('analysis_results') / 'combined_analysis.json'
    with open(combined_output, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"\nCombined analysis results saved to {combined_output}")

def generate_type_system_overview(metrics: TypeMetrics, file_metrics: list) -> str:
    """Generate a comprehensive type system overview with detailed metrics."""
    # Calculate overall health score
    type_coverage = (metrics.explicit_types / (metrics.explicit_types + metrics.any_types)) * 100 if metrics.explicit_types > 0 else 0
    
    overview = f"""# TypeScript System Analysis Report

## 1. Core Type System Metrics
```typescript
Overall Health: {type_coverage:.1f}%

Type Structure Statistics:
Interfaces: {metrics.interfaces:,} total
- src/compiler/types.ts: {file_metrics[0]['metrics'].interfaces}
- typescript.d.ts: {file_metrics[1]['metrics'].interfaces}

Generic Types: {metrics.generic_types:,} instances

Type Aliases: {metrics.type_alias:,} total
- src/compiler/types.ts: {file_metrics[0]['metrics'].type_alias}
- typescript.d.ts: {file_metrics[1]['metrics'].type_alias}

Type Guards: {metrics.type_guards:,} total
- src/compiler/types.ts: {file_metrics[0]['metrics'].type_guards}
- typescript.d.ts: {file_metrics[1]['metrics'].type_guards}

Safety Metrics:
Strict Mode: {'Enabled' if type_coverage > 90 else 'Disabled'}
Type Assertions: {metrics.type_assertions} total
Type Guard Coverage: {'High' if metrics.type_guards > 1000 else 'Medium' if metrics.type_guards > 500 else 'Low'}
```

## 2. Documentation Analysis
```typescript
Documentation Coverage:
JSDoc Coverage: {min(100, metrics.jsdoc_coverage):.1f}%
Parameter Docs: {metrics.param_doc_coverage:.1f}%
Return Types: {metrics.return_doc_coverage:.1f}%

Files Breakdown:

1. src/compiler/types.ts:
   - {'Good Documentation' if file_metrics[0]['metrics'].doc_coverage > 80 else 'Documentation Needs Improvement'}
   - {'Critical Types Well Documented' if file_metrics[0]['metrics'].jsdoc_coverage > 80 else 'Critical Types Lacking Docs'}
   - {'Complex Generics Well Documented' if file_metrics[0]['metrics'].param_doc_coverage > 80 else 'Complex Generics Undocumented'}

2. typescript.d.ts:
   - {'Good Documentation' if file_metrics[1]['metrics'].doc_coverage > 80 else 'Better Documentation Coverage'}
   - {'API Types Well Documented' if file_metrics[1]['metrics'].jsdoc_coverage > 80 else 'API Types Need Better Docs'}
   - {'Complex Types Well Documented' if file_metrics[1]['metrics'].param_doc_coverage > 80 else 'Some Complex Types Need Docs'}
```

## 3. File-Specific Analysis

### A. src/compiler/types.ts
```typescript
Metrics:
Type Coverage: {file_metrics[0]['metrics'].type_coverage:.1f}%
Type Distribution:
- {file_metrics[0]['metrics'].interfaces:,} Interfaces
- {file_metrics[0]['metrics'].type_alias:,} Type Aliases
- {file_metrics[0]['metrics'].type_guards:,} Type Guards
```

### B. typescript.d.ts
```typescript
Metrics:
Type Coverage: {file_metrics[1]['metrics'].type_coverage:.1f}%
Type Distribution:
- {file_metrics[1]['metrics'].interfaces:,} Interfaces
- {file_metrics[1]['metrics'].type_alias:,} Type Aliases
- {file_metrics[1]['metrics'].type_guards:,} Type Guards
```

## 4. Recommendations

### A. Documentation Priority Matrix
```plaintext
High Priority:
1. Public API Interfaces
2. Generic Type Parameters
3. Type Guard Functions
4. Compiler Options

Medium Priority:
1. Internal Interfaces
2. Type Aliases
3. Utility Types
4. Helper Functions

Low Priority:
1. Private Types
2. Internal Enums
3. Constants
4. Debug Utilities
```"""
    return overview

def generate_report(data: dict, report_path: str):
    """Generate a comprehensive TypeScript analysis report"""
    report = generate_type_system_overview(data['metrics'], data['analysis_results'])
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)

def generate_report_detailed(analysis, report_path, file_content=None, filename=None):
    """Generate a comprehensive TypeScript analysis report with detailed metrics"""
    report_lines = []
    
    # Header
    report_lines.append(f"# TypeScript Analysis - {filename}\n")
    report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Type System Metrics
    report_lines.append("## Type System Analysis\n")
    report_lines.append("```typescript\n")
    report_lines.append(f"Type Coverage: {analysis['metrics'].type_coverage:.1f}%\n")
    report_lines.append(f"Type Safety Score: {analysis['metrics'].type_safety_score:.1f}%\n\n")
    
    report_lines.append("Type Structure:\n")
    report_lines.append(f"Classes: {analysis['metrics'].classes}\n")
    report_lines.append(f"Interfaces: {analysis['metrics'].interfaces}\n")
    report_lines.append(f"Type Aliases: {analysis['metrics'].type_aliases}\n")
    report_lines.append(f"Generic Types: {analysis['metrics'].generic_types}\n\n")
    
    report_lines.append("Type Safety:\n")
    report_lines.append(f"Type Guards: {analysis['metrics'].type_guards}\n")
    report_lines.append(f"Type Assertions: {analysis['metrics'].type_assertions}\n")
    report_lines.append(f"Any Types: {analysis['metrics'].any_types}\n")
    report_lines.append("```\n\n")
    
    # Documentation Metrics
    report_lines.append("## Documentation Analysis\n")
    report_lines.append("```typescript\n")
    report_lines.append(f"Overall Coverage: {analysis['metrics'].doc_coverage:.1f}%\n")
    report_lines.append(f"JSDoc Coverage: {min(100, analysis['metrics'].jsdoc_coverage):.1f}%\n")
    report_lines.append(f"Parameter Docs: {analysis['metrics'].param_doc_coverage:.1f}%\n")
    report_lines.append(f"Return Type Docs: {analysis['metrics'].return_doc_coverage:.1f}%\n")
    report_lines.append("```\n\n")
    
    # Code Examples
    if file_content:
        report_lines.append("## Code Examples\n")
        examples = extract_examples(file_content)
        for category, category_examples in examples.items():
            if category_examples:
                report_lines.append(f"### {category}\n")
                report_lines.append("```typescript\n")
                for example in category_examples.split('\n'):  # Split example into lines
                    report_lines.append(example + "\n")
                report_lines.append("```\n\n")
    
    # Write report to file
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(''.join(report_lines))

def analyze_github_pr(repo_name: str, pr_number: int):
    """Analyze a GitHub PR directly without local storage"""
    try:
        logger.info(f"Analyzing PR #{pr_number} from {repo_name}")
        
        # Create reports directory
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Initialize GitHub client
        g = Github(os.getenv('GITHUB_TOKEN'))
        
        # Get repository
        logger.info("Fetching repository...")
        repo = g.get_repo(repo_name)
        
        # Get PR
        logger.info("Fetching PR...")
        pr = repo.get_pull(pr_number)
        logger.info(f"Found PR: {pr.title}")
        
        # Get PR files
        logger.info("Fetching PR files...")
        files = pr.get_files()
        file_list = list(files)
        logger.info(f"Found {len(file_list)} files")
        
        # Initialize combined metrics
        combined_metrics = TypeMetrics()
        analysis_results = []
        
        # Analyze each file
        for file in file_list:
            logger.info(f"Checking file: {file.filename}")
            
            if file.filename.endswith(('.ts', '.tsx')):
                logger.info(f"Analyzing TypeScript file: {file.filename}")
                
                # Fetch file content
                logger.info("Fetching file content...")
                file_content = repo.get_contents(file.filename, ref=pr.head.sha).decoded_content.decode('utf-8')
                logger.info("File content fetched successfully")
                
                # Analyze TypeScript code
                logger.info("Analyzing TypeScript code...")
                metrics = analyze_typescript_code(file_content)
                
                # Update combined metrics
                combined_metrics.type_coverage += metrics.type_coverage
                combined_metrics.explicit_types += metrics.explicit_types
                combined_metrics.generic_types += metrics.generic_types
                combined_metrics.interfaces += metrics.interfaces
                combined_metrics.type_guards += metrics.type_guards
                combined_metrics.any_types += metrics.any_types
                combined_metrics.type_assertions += metrics.type_assertions
                combined_metrics.type_alias += metrics.type_alias
                combined_metrics.doc_coverage += metrics.doc_coverage
                combined_metrics.jsdoc_coverage += metrics.jsdoc_coverage
                combined_metrics.param_doc_coverage += metrics.param_doc_coverage
                combined_metrics.return_doc_coverage += metrics.return_doc_coverage
                combined_metrics.type_safety_score += metrics.type_safety_score
                combined_metrics.classes += metrics.classes
                combined_metrics.functions += metrics.functions
                combined_metrics.variables += metrics.variables
                combined_metrics.parameters += metrics.parameters
                combined_metrics.type_annotations += metrics.type_annotations
                combined_metrics.branded_types += metrics.branded_types
                combined_metrics.utility_types += metrics.utility_types
                combined_metrics.untyped_functions += metrics.untyped_functions
                combined_metrics.implicit_returns += metrics.implicit_returns
                combined_metrics.null_checks += metrics.null_checks
                
                # Extract code examples
                examples = extract_examples(file_content)
                
                # Generate detailed report
                report_path = os.path.join(reports_dir, f"typescript_analysis_{pr_number}_{Path(file.filename).stem}.md")
                logger.info(f"Generating detailed report: {report_path}")
                generate_report_detailed({
                    'metrics': metrics,
                    'examples': examples,
                    'filename': file.filename
                }, report_path)
                logger.info("Analysis complete for this file")
                
                analysis_results.append({
                    'file': file.filename,
                    'metrics': metrics,
                    'examples': examples
                })
            else:
                logger.info("Skipping non-TypeScript file")
        
        # Average the metrics if we analyzed any files
        num_ts_files = len([r for r in analysis_results if 'metrics' in r])
        if num_ts_files > 0:
            combined_metrics.type_coverage /= num_ts_files
            combined_metrics.doc_coverage /= num_ts_files
            combined_metrics.jsdoc_coverage /= num_ts_files
            combined_metrics.param_doc_coverage /= num_ts_files
            combined_metrics.return_doc_coverage /= num_ts_files
            combined_metrics.type_safety_score /= num_ts_files
        
        # Generate summary report
        summary_path = os.path.join(reports_dir, f"typescript_analysis_{pr_number}_summary.md")
        logger.info(f"Generating summary report: {summary_path}")
        generate_report({
            'pr': {
                'number': pr_number,
                'title': pr.title,
                'url': pr.html_url,
                'changed_files': len(file_list)
            },
            'metrics': combined_metrics,
            'analysis_results': analysis_results
        }, summary_path)
        logger.info("Analysis complete!")
        
    except Exception as e:
        logger.error(f"Error analyzing PR: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--pr":
        if len(sys.argv) != 4:
            print("Usage: python test_typescript_analyzer.py --pr <repo_name> <pr_number>")
            sys.exit(1)
        repo_name = sys.argv[2]
        pr_number = int(sys.argv[3])
        analyze_github_pr(repo_name, pr_number)
    else:
        test_typescript_analyzer()

def test_typescript_analyzer(pr_name=None):
    """Test the TypeScript analyzer with sample files"""
    try:
        # Sample files for analysis
        sample_files = [
            {
                "name": "User Management System",
                "files": [
                    {
                        "filename": "sample/example.ts",
                        "status": "modified",
                        "additions": 124,
                        "deletions": 0,
                        "changes": 124
                    }
                ]
            }
        ]
        
        analyses = []
        
        # Analyze each project
        for project in sample_files:
            try:
                print(f"\nAnalyzing {project['name']}")
                
                # Initialize project analysis
                project_analysis = {
                    'name': project['name'],
                    'metrics': {},
                    'examples': {},
                    'framework': None
                }
                
                # Get files
                ts_files = [f for f in project['files'] if f['filename'].endswith(('.ts', '.tsx'))]
                
                if not ts_files:
                    print(f"No TypeScript files found in {project['name']}")
                    continue
                
                # Analyze each TypeScript file
                for file in ts_files:
                    print(f"Analyzing file: {file['filename']}")
                    
                    try:
                        # Read local file content
                        with open(file['filename'], 'r') as f:
                            file_content = f.read()
                            
                        print(f"Successfully read content for {file['filename']}")
                        
                        # Analyze the file
                        metrics = analyze_typescript_file(file_content)
                        
                        # Convert metrics to dict
                        metrics_dict = metrics.__dict__
                        
                        # Extract code examples
                        examples = extract_examples(file_content)
                        if 'examples' not in project_analysis:
                            project_analysis['examples'] = {}
                        for category, example in examples.items():
                            if category not in project_analysis['examples']:
                                project_analysis['examples'][category] = example
                        
                        # Update project metrics
                        project_analysis['metrics'].update(metrics_dict)
                                
                        print(f"Successfully analyzed {file['filename']}")
                    
                    except Exception as e:
                        print(f"Error analyzing file {file['filename']}: {str(e)}")
                        continue
                
                analyses.append(project_analysis)
                
            except Exception as e:
                print(f"Error analyzing {project['name']}: {str(e)}")
                continue
        
        # Generate comprehensive report
        report = generate_full_report(analyses)
        
        # Save report
        os.makedirs('reports', exist_ok=True)
        report_path = 'reports/typescript_analysis_report.md'
        with open(report_path, 'w') as f:
            f.write(report)
            
        print(f"\nAnalysis report generated: {report_path}")
        
    except Exception as e:
        print(f"Error in test_typescript_analyzer: {str(e)}")
        raise

def generate_file_report(analysis: dict, filename: str) -> str:
    """Generate a detailed report for a single file."""
    now = datetime.datetime.now()
    report_lines = []
    
    # Header
    report_lines.append(f"\n# TypeScript Analysis - {filename}")
    report_lines.append(f"Generated on: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Type System Analysis
    report_lines.append("## Type System Analysis")
    report_lines.append("```typescript\n")
    report_lines.append(f"Type Coverage: {analysis['metrics'].type_coverage:.1f}%\n")
    report_lines.append(f"Type Safety Score: {analysis['metrics'].type_safety_score:.1f}%\n\n")
    
    report_lines.append("Type Structure:\n")
    report_lines.append(f"Classes: {analysis['metrics'].classes}\n")
    report_lines.append(f"Interfaces: {analysis['metrics'].interfaces}\n")
    report_lines.append(f"Type Aliases: {analysis['metrics'].type_aliases}\n")
    report_lines.append(f"Generic Types: {analysis['metrics'].generic_types}\n\n")
    
    report_lines.append("Type Safety:\n")
    report_lines.append(f"Type Guards: {analysis['metrics'].type_guards}\n")
    report_lines.append(f"Type Assertions: {analysis['metrics'].type_assertions}\n")
    report_lines.append(f"Any Types: {analysis['metrics'].any_types}\n")
    report_lines.append("```\n\n")
    
    # Documentation Metrics
    report_lines.append("## Documentation Analysis")
    report_lines.append("```typescript\n")
    report_lines.append(f"Overall Coverage: {analysis['metrics'].doc_coverage:.1f}%\n")
    report_lines.append(f"JSDoc Coverage: {min(100, analysis['metrics'].jsdoc_coverage):.1f}%\n")
    report_lines.append(f"Parameter Docs: {analysis['metrics'].param_doc_coverage:.1f}%\n")
    report_lines.append(f"Return Type Docs: {analysis['metrics'].return_doc_coverage:.1f}%\n")
    report_lines.append("```\n\n")
    
    return "".join(report_lines)

def generate_enhanced_report(analysis_results: List[Dict], summary: bool = False) -> str:
    """Generate enhanced analysis report with better visualization and insights"""
    if summary:
        return generate_summary_report(analysis_results)
    return generate_detailed_report(analysis_results[0])

def generate_detailed_report(analysis: Dict) -> str:
    """Generate detailed file analysis report"""
    metrics = analysis['metrics']
    return f"""# TypeScript Analysis - {analysis.get('file', 'Unknown')}
Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. Quality Overview
```typescript
Overall Score: {metrics.quality_score:.1f}/100

Strengths:
{'✓' if metrics.type_coverage > 90 else '⚠'} Type Coverage: {metrics.type_coverage:.1f}%
{'✓' if metrics.type_guards > 100 else '⚠'} Type Guards: {metrics.type_guards}
{'✓' if metrics.any_types < 10 else '⚠'} Any Types: {metrics.any_types}

Areas for Improvement:
{'✓' if metrics.doc_coverage > 80 else '❌'} Documentation: {metrics.doc_coverage:.1f}%
{'✓' if metrics.param_doc_coverage > 80 else '❌'} Parameter Docs: {metrics.param_doc_coverage:.1f}%
{'✓' if metrics.return_doc_coverage > 80 else '❌'} Return Docs: {metrics.return_doc_coverage:.1f}%
```

## 2. Type System Details
```typescript
Type Structure:
├── Classes: {metrics.classes}
├── Interfaces: {metrics.interfaces}
├── Type Aliases: {metrics.type_aliases}
└── Generic Types: {metrics.generic_types}

Type Safety:
├── Type Guards: {metrics.type_guards}
├── Type Assertions: {metrics.type_assertions}
└── Any Types: {metrics.any_types}

Advanced Features:
├── Mapped Types: {metrics.mapped_types}
├── Utility Types: {metrics.utility_types}
├── Branded Types: {metrics.branded_types}
└── Type Predicates: {metrics.type_predicates}
```

## 3. Critical Issues
```typescript
{generate_critical_issues(metrics)}
```

## 4. Recommendations
```typescript
{generate_recommendations(metrics)}
```
"""

def generate_summary_report(analyses: List[Dict]) -> str:
    """Generate comprehensive summary report"""
    if not analyses:
        return "No TypeScript files analyzed."
        
    combined_metrics = combine_metrics(analyses)
    return f"""# TypeScript Codebase Analysis Summary

## 1. Overall Health
```typescript
Project Quality: {calculate_project_quality(combined_metrics):.1f}/100

Core Metrics:
├── Type Safety: {calculate_type_safety(combined_metrics):.1f}%
├── Documentation: {calculate_doc_coverage(combined_metrics):.1f}%
└── Best Practices: {calculate_best_practices(combined_metrics):.1f}%

File Analysis:
{generate_file_breakdown(analyses)}
```

## 2. Key Findings
```typescript
Strengths:
{generate_strengths(combined_metrics)}

Areas for Improvement:
{generate_improvements(combined_metrics)}

Critical Issues:
{generate_critical_issues_summary(analyses)}
```

## 3. Recommendations
{generate_prioritized_recommendations(analyses)}
"""

def generate_file_breakdown(analyses: List[Dict]) -> str:
    """Generate per-file metrics breakdown"""
    breakdown = []
    for analysis in analyses:
        metrics = analysis['metrics']
        breakdown.append(f"""
File: {analysis.get('file', 'Unknown')}
├── Quality Score: {metrics.quality_score:.1f}/100
├── Type Coverage: {metrics.type_coverage:.1f}%
└── Documentation: {metrics.doc_coverage:.1f}%""")
    return '\n'.join(breakdown)

def generate_critical_issues(metrics: TypeMetrics) -> str:
    """Generate formatted critical issues section"""
    issues = []
    
    if metrics.any_types > 0:
        issues.append(f"❌ Found {metrics.any_types} uses of 'any' type")
    if metrics.type_assertions > 100:
        issues.append(f"⚠️ High number of type assertions ({metrics.type_assertions})")
    if metrics.doc_coverage < 50:
        issues.append(f"❌ Low documentation coverage ({metrics.doc_coverage:.1f}%)")
    if metrics.untyped_functions > 0:
        issues.append(f"⚠️ Found {metrics.untyped_functions} functions without type annotations")
    if metrics.implicit_returns > 0:
        issues.append(f"⚠️ Found {metrics.implicit_returns} functions with implicit returns")
        
    return '\n'.join(issues) if issues else "✓ No critical issues found"

def generate_recommendations(metrics: TypeMetrics) -> str:
    """Generate prioritized recommendations"""
    recommendations = {
        'High Priority': [],
        'Medium Priority': [],
        'Low Priority': []
    }
    
    # Add recommendations based on metrics
    if metrics.any_types > 0:
        recommendations['High Priority'].append(
            f"Replace {metrics.any_types} 'any' types with specific types"
        )
    if metrics.doc_coverage < 50:
        recommendations['High Priority'].append(
            f"Increase documentation coverage (currently {metrics.doc_coverage:.1f}%)"
        )
    if metrics.type_guards < 50:
        recommendations['Medium Priority'].append(
            "Add more type guards for better type safety"
        )
    if metrics.implicit_returns > 0:
        recommendations['Medium Priority'].append(
            f"Add explicit return types to functions"
        )
    if metrics.utility_types < 10:
        recommendations['Low Priority'].append(
            "Consider using more utility types"
        )
        
    # Format recommendations
    output = []
    for priority, items in recommendations.items():
        if items:
            output.append(f"\n{priority}:")
            output.extend([f"- {item}" for item in sorted(items)])
            
    return '\n'.join(output) if output else "✓ No immediate recommendations"

def analyze_typescript_pr(owner: str, repo: str, pr_number: int) -> None:
    """Analyze TypeScript files in a GitHub PR"""
    try:
        print(f"Analyzing PR #{pr_number} from {owner}/{repo}")
        
        # Initialize GitHub client
        g = Github(os.getenv('GITHUB_TOKEN'))
        
        # Get repository
        print("Fetching repository...")
        repository = g.get_repo(f"{owner}/{repo}")
        
        # Get PR
        print("Fetching PR...")
        pr = repository.get_pull(pr_number)
        print(f"Found PR: {pr.title}")
        
        # Get PR files
        print("Fetching PR files...")
        files = list(pr.get_files())
        typescript_files = [f for f in files if f.filename.endswith('.ts')]
        print(f"Found {len(typescript_files)} files")
        
        # Initialize analysis results
        analysis_results = []
        
        # Analyze each TypeScript file
        for ts_file in typescript_files:
            print(f"Checking file: {ts_file.filename}")
            
            if ts_file.filename.endswith('.d.ts'):
                framework = Framework.NONE
            elif 'react' in ts_file.filename.lower():
                framework = Framework.REACT
            elif 'angular' in ts_file.filename.lower():
                framework = Framework.ANGULAR
            elif 'vue' in ts_file.filename.lower():
                framework = Framework.VUE
            else:
                framework = Framework.NONE
                
            print(f"Analyzing TypeScript file: {ts_file.filename}")
            
            # Get file content
            print("Fetching file content...")
            try:
                content = repository.get_contents(ts_file.filename, ref=pr.head.sha).decoded_content.decode('utf-8')
                print("File content fetched successfully")
            except Exception as e:
                print(f"Error fetching file content: {str(e)}")
                continue
                
            # Analyze code
            print("Analyzing TypeScript code...")
            metrics = analyze_typescript_code(content)
            
            # Create analysis result
            analysis = {
                'file': ts_file.filename,
                'metrics': metrics,
                'framework': framework,
                'content': content
            }
            analysis_results.append(analysis)
            
            # Generate detailed report
            report_name = os.path.basename(ts_file.filename).replace('.', '_')
            report_path = os.path.join('reports', f'typescript_analysis_{pr_number}_{report_name}.md')
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            with open(report_path, 'w') as f:
                f.write(generate_detailed_report(analysis))
            print(f"Generating detailed report: {report_path}")
            print("Analysis complete for this file")
            
        # Generate summary report
        summary_path = os.path.join('reports', f'typescript_analysis_{pr_number}_summary.md')
        with open(summary_path, 'w') as f:
            f.write(generate_summary_report(analysis_results))
        print(f"Generating summary report: {summary_path}")
        
        print("Analysis complete!")
        
    except Exception as e:
        print(f"Error in analyze_typescript_pr: {str(e)}")
        raise

def generate_strengths(metrics: TypeMetrics) -> str:
    """Generate strengths section for summary report"""
    strengths = []
    
    if metrics.type_coverage > 90:
        strengths.append(f"✓ Strong type coverage ({metrics.type_coverage:.1f}%)")
    if metrics.doc_coverage > 80:
        strengths.append(f"✓ Good documentation coverage ({metrics.doc_coverage:.1f}%)")
    if metrics.type_guards > 100:
        strengths.append(f"✓ Extensive use of type guards ({metrics.type_guards} total)")
    if metrics.any_types < 10:
        strengths.append(f"✓ Limited use of 'any' type ({metrics.any_types} occurrences)")
    if metrics.utility_types > 20:
        strengths.append(f"✓ Good utilization of utility types ({metrics.utility_types} uses)")
        
    return '\n'.join(strengths) if strengths else "No notable strengths identified"

def generate_improvements(metrics: TypeMetrics) -> str:
    """Generate improvements section for summary report"""
    improvements = []
    
    if metrics.type_coverage < 90:
        improvements.append(f"⚠️ Improve type coverage ({metrics.type_coverage:.1f}%)")
    if metrics.doc_coverage < 80:
        improvements.append(f"❌ Increase documentation coverage ({metrics.doc_coverage:.1f}%)")
    if metrics.any_types > 10:
        improvements.append(f"❌ Reduce use of 'any' type ({metrics.any_types} occurrences)")
    if metrics.type_assertions > 100:
        improvements.append(f"⚠️ High number of type assertions ({metrics.type_assertions})")
    if metrics.utility_types < 10:
        improvements.append("⚠️ Consider using more utility types")
        
    return '\n'.join(improvements) if improvements else "No immediate improvements needed"

def generate_file_breakdown(analyses: List[Dict]) -> str:
    """Generate file breakdown section"""
    breakdown = []
    
    for analysis in analyses:
        metrics = analysis['metrics']
        file_name = analysis['file']
        
        breakdown.append(f"\n{file_name}:")
        breakdown.append(f"├── Quality Score: {metrics.quality_score:.1f}/100")
        breakdown.append(f"├── Type Coverage: {metrics.type_coverage:.1f}%")
        breakdown.append(f"└── Documentation: {metrics.doc_coverage:.1f}%")
        
    return '\n'.join(breakdown)

def generate_critical_issues_summary(analyses: List[Dict]) -> str:
    """Generate summary of critical issues across all files"""
    total_issues = []
    
    for analysis in analyses:
        metrics = analysis['metrics']
        file_name = analysis['file']
        
        if metrics.any_types > 0:
            total_issues.append(f"❌ {file_name}: {metrics.any_types} uses of 'any' type")
        if metrics.type_assertions > 100:
            total_issues.append(f"⚠️ {file_name}: High number of type assertions ({metrics.type_assertions})")
        if metrics.doc_coverage < 50:
            total_issues.append(f"❌ {file_name}: Low documentation coverage ({metrics.doc_coverage:.1f}%)")
            
    return '\n'.join(total_issues) if total_issues else "✓ No critical issues found"

def generate_prioritized_recommendations(analyses: List[Dict]) -> str:
    """Generate prioritized recommendations for all files"""
    all_recommendations = {
        'High Priority': set(),
        'Medium Priority': set(),
        'Low Priority': set()
    }
    
    for analysis in analyses:
        metrics = analysis['metrics']
        file_name = analysis['file']
        
        # High priority
        if metrics.any_types > 0:
            all_recommendations['High Priority'].add(
                f"Replace 'any' types with specific types in {file_name}"
            )
        if metrics.doc_coverage < 50:
            all_recommendations['High Priority'].add(
                f"Improve documentation coverage in {file_name}"
            )
            
        # Medium priority
        if metrics.type_guards < 50:
            all_recommendations['Medium Priority'].add(
                f"Add more type guards in {file_name}"
            )
        if metrics.implicit_returns > 0:
            all_recommendations['Medium Priority'].add(
                f"Add explicit return types in {file_name}"
            )
            
        # Low priority
        if metrics.utility_types < 10:
            all_recommendations['Low Priority'].add(
                f"Consider using more utility types in {file_name}"
            )
            
    # Format recommendations
    output = []
    for priority, items in all_recommendations.items():
        if items:
            output.append(f"\n### {priority}")
            output.extend([f"- {item}" for item in sorted(items)])
            
    return '\n'.join(output) if output else "✓ No immediate recommendations"

def generate_detailed_report(analysis: Dict) -> str:
    """Generate detailed file analysis report"""
    metrics = analysis['metrics']
    return f"""# TypeScript Analysis - {analysis['file']}
Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. Quality Overview
```typescript
Overall Score: {metrics.quality_score:.1f}/100

Strengths:
{'✓' if metrics.type_coverage > 90 else '⚠'} Type Coverage: {metrics.type_coverage:.1f}%
{'✓' if metrics.type_guards > 100 else '⚠'} Type Guards: {metrics.type_guards}
{'✓' if metrics.any_types < 10 else '⚠'} Any Types: {metrics.any_types}

Areas for Improvement:
{'✓' if metrics.doc_coverage > 80 else '❌'} Documentation: {metrics.doc_coverage:.1f}%
{'✓' if metrics.param_doc_coverage > 80 else '❌'} Parameter Docs: {metrics.param_doc_coverage:.1f}%
{'✓' if metrics.return_doc_coverage > 80 else '❌'} Return Docs: {metrics.return_doc_coverage:.1f}%
```

## 2. Type System Details
```typescript
Type Structure:
├── Classes: {metrics.classes}
├── Interfaces: {metrics.interfaces}
├── Type Aliases: {metrics.type_aliases}
└── Generic Types: {metrics.generic_types}

Type Safety:
├── Type Guards: {metrics.type_guards}
├── Type Assertions: {metrics.type_assertions}
└── Any Types: {metrics.any_types}

Advanced Features:
├── Mapped Types: {metrics.mapped_types}
├── Utility Types: {metrics.utility_types}
├── Branded Types: {metrics.branded_types}
└── Type Predicates: {metrics.type_predicates}
```

## 3. Critical Issues
```typescript
{generate_critical_issues(metrics)}
```

## 4. Recommendations
```typescript
{generate_recommendations(metrics)}
```
"""

def generate_summary_report(analyses: List[Dict]) -> str:
    """Generate comprehensive summary report"""
    if not analyses:
        return "No TypeScript files analyzed."
        
    combined_metrics = combine_metrics(analyses)
    return f"""# TypeScript Codebase Analysis Summary

## 1. Overall Health
```typescript
Project Quality: {calculate_project_quality(combined_metrics):.1f}/100

Core Metrics:
├── Type Safety: {calculate_type_safety(combined_metrics):.1f}%
├── Documentation: {calculate_doc_coverage(combined_metrics):.1f}%
└── Best Practices: {calculate_best_practices(combined_metrics):.1f}%

File Analysis:
{generate_file_breakdown(analyses)}
```

## 2. Key Findings
```typescript
Strengths:
{generate_strengths(combined_metrics)}

Areas for Improvement:
{generate_improvements(combined_metrics)}

Critical Issues:
{generate_critical_issues_summary(analyses)}
```

## 3. Recommendations
{generate_prioritized_recommendations(analyses)}
"""

def combine_metrics(analyses: List[Dict]) -> TypeMetrics:
    """Combine metrics from multiple files"""
    combined = TypeMetrics()
    
    if not analyses:
        return combined
        
    # Sum up countable metrics
    for analysis in analyses:
        metrics = analysis['metrics']
        combined.classes += metrics.classes
        combined.interfaces += metrics.interfaces
        combined.type_aliases += metrics.type_aliases
        combined.generic_types += metrics.generic_types
        combined.type_guards += metrics.type_guards
        combined.type_assertions += metrics.type_assertions
        combined.any_types += metrics.any_types
        combined.functions += metrics.functions
        combined.untyped_functions += metrics.untyped_functions
        combined.implicit_returns += metrics.implicit_returns
        
    # Average percentage metrics
    n = len(analyses)
    combined.type_coverage = sum(a['metrics'].type_coverage for a in analyses) / n
    combined.doc_coverage = sum(a['metrics'].doc_coverage for a in analyses) / n
    combined.jsdoc_coverage = sum(a['metrics'].jsdoc_coverage for a in analyses) / n
    combined.param_doc_coverage = sum(a['metrics'].param_doc_coverage for a in analyses) / n
    combined.return_doc_coverage = sum(a['metrics'].return_doc_coverage for a in analyses) / n
    
    # Calculate combined quality score
    combined.calculate_quality_score()
    
    return combined

def calculate_project_quality(metrics: TypeMetrics) -> float:
    """Calculate overall project quality score"""
    weights = {
        'type_coverage': 0.3,
        'type_safety': 0.3,
        'documentation': 0.2,
        'best_practices': 0.2
    }
    
    type_coverage_score = metrics.type_coverage
    type_safety_score = calculate_type_safety(metrics)
    documentation_score = calculate_doc_coverage(metrics)
    best_practices_score = calculate_best_practices(metrics)
    
    return (
        weights['type_coverage'] * type_coverage_score +
        weights['type_safety'] * type_safety_score +
        weights['documentation'] * documentation_score +
        weights['best_practices'] * best_practices_score
    )

def calculate_type_safety(metrics: TypeMetrics) -> float:
    """Calculate type safety score"""
    base_score = 100.0
    
    # Deduct points for type safety issues
    if metrics.any_types > 0:
        base_score -= min(30, metrics.any_types * 2)
    if metrics.type_assertions > 100:
        base_score -= min(20, (metrics.type_assertions - 100) * 0.1)
    if metrics.untyped_functions > 0:
        base_score -= min(30, metrics.untyped_functions * 2)
    if metrics.implicit_returns > 0:
        base_score -= min(20, metrics.implicit_returns)
        
    return max(0.0, base_score)

def calculate_doc_coverage(metrics: TypeMetrics) -> float:
    """Calculate documentation coverage score"""
    weights = {
        'jsdoc': 0.4,
        'params': 0.3,
        'returns': 0.3
    }
    
    return (
        weights['jsdoc'] * metrics.jsdoc_coverage +
        weights['params'] * metrics.param_doc_coverage +
        weights['returns'] * metrics.return_doc_coverage
    )

def calculate_best_practices(metrics: TypeMetrics) -> float:
    """Calculate best practices score"""
    base_score = 100.0
    
    # Add points for good practices
    if metrics.type_guards > 100:
        base_score += min(10, metrics.type_guards * 0.1)
    if metrics.utility_types > 20:
        base_score += min(10, metrics.utility_types * 0.5)
    if metrics.mapped_types > 10:
        base_score += min(10, metrics.mapped_types)
    if metrics.branded_types > 0:
        base_score += min(10, metrics.branded_types * 2)
    if metrics.type_predicates > 10:
        base_score += min(10, metrics.type_predicates)
        
    return min(100.0, base_score)

def generate_strengths(metrics: TypeMetrics) -> str:
    """Generate strengths section"""
    strengths = []
    
    if metrics.type_coverage > 90:
        strengths.append(f"✓ Excellent type coverage ({metrics.type_coverage:.1f}%)")
    if metrics.type_guards > 100:
        strengths.append(f"✓ Strong type guard usage ({metrics.type_guards} guards)")
    if metrics.any_types < 10:
        strengths.append(f"✓ Minimal use of 'any' type ({metrics.any_types} occurrences)")
    if metrics.doc_coverage > 80:
        strengths.append(f"✓ Good documentation coverage ({metrics.doc_coverage:.1f}%)")
        
    return '\n'.join(strengths) if strengths else "No notable strengths identified"

def generate_improvements(metrics: TypeMetrics) -> str:
    """Generate improvements section"""
    improvements = []
    
    if metrics.type_coverage < 90:
        improvements.append(f"⚠️ Improve type coverage ({metrics.type_coverage:.1f}%)")
    if metrics.any_types > 10:
        improvements.append(f"❌ Reduce use of 'any' type ({metrics.any_types} occurrences)")
    if metrics.doc_coverage < 80:
        improvements.append(f"❌ Increase documentation coverage ({metrics.doc_coverage:.1f}%)")
    if metrics.untyped_functions > 0:
        improvements.append(f"⚠️ Add types to {metrics.untyped_functions} functions")
        
    return '\n'.join(improvements) if improvements else "No major areas for improvement"

def generate_critical_issues_summary(analyses: List[Dict]) -> str:
    """Generate summary of critical issues across all files"""
    total_issues = []
    
    for analysis in analyses:
        metrics = analysis['metrics']
        file_name = analysis['file']
        
        if metrics.any_types > 0:
            total_issues.append(f"❌ {file_name}: {metrics.any_types} uses of 'any' type")
        if metrics.untyped_functions > 0:
            total_issues.append(f"⚠️ {file_name}: {metrics.untyped_functions} functions without type annotations")
        if metrics.doc_coverage < 50:
            total_issues.append(f"❌ {file_name}: {metrics.doc_coverage:.1f}% documentation coverage")
            
    return '\n'.join(total_issues) if total_issues else "✓ No critical issues found"

def generate_prioritized_recommendations(analyses: List[Dict]) -> str:
    """Generate prioritized recommendations across all files"""
    all_recommendations = {
        'High Priority': set(),
        'Medium Priority': set(),
        'Low Priority': set()
    }
    
    for analysis in analyses:
        metrics = analysis['metrics']
        file_name = analysis['file']
        
        # High priority
        if metrics.any_types > 0:
            all_recommendations['High Priority'].add(
                f"Replace 'any' types with specific types in {file_name}"
            )
        if metrics.doc_coverage < 50:
            all_recommendations['High Priority'].add(
                f"Improve documentation coverage in {file_name}"
            )
            
        # Medium priority
        if metrics.type_guards < 50:
            all_recommendations['Medium Priority'].add(
                f"Add more type guards in {file_name}"
            )
        if metrics.implicit_returns > 0:
            all_recommendations['Medium Priority'].add(
                f"Add explicit return types in {file_name}"
            )
            
        # Low priority
        if metrics.utility_types < 10:
            all_recommendations['Low Priority'].add(
                f"Consider using more utility types in {file_name}"
            )
            
    # Format recommendations
    output = []
    for priority, items in all_recommendations.items():
        if items:
            output.append(f"\n### {priority}")
            output.extend([f"- {item}" for item in sorted(items)])
            
    return '\n'.join(output) if output else "✓ No immediate recommendations"

def analyze_typescript_pr(owner: str, repo: str, pr_number: int) -> None:
    """Analyze TypeScript files in a GitHub PR"""
    try:
        print(f"Analyzing PR #{pr_number} from {owner}/{repo}")
        
        # Initialize GitHub client
        g = Github(os.getenv('GITHUB_TOKEN'))
        
        # Get repository
        print("Fetching repository...")
        repository = g.get_repo(f"{owner}/{repo}")
        
        # Get PR
        print("Fetching PR...")
        pr = repository.get_pull(pr_number)
        print(f"Found PR: {pr.title}")
        
        # Get PR files
        print("Fetching PR files...")
        files = list(pr.get_files())
        typescript_files = [f for f in files if f.filename.endswith('.ts')]
        print(f"Found {len(typescript_files)} files")
        
        # Initialize analysis results
        analysis_results = []
        
        # Analyze each TypeScript file
        for ts_file in typescript_files:
            print(f"Checking file: {ts_file.filename}")
            
            if ts_file.filename.endswith('.d.ts'):
                framework = Framework.NONE
            elif 'react' in ts_file.filename.lower():
                framework = Framework.REACT
            elif 'angular' in ts_file.filename.lower():
                framework = Framework.ANGULAR
            elif 'vue' in ts_file.filename.lower():
                framework = Framework.VUE
            else:
                framework = Framework.NONE
                
            print(f"Analyzing TypeScript file: {ts_file.filename}")
            
            # Get file content
            print("Fetching file content...")
            try:
                content = repository.get_contents(ts_file.filename, ref=pr.head.sha).decoded_content.decode('utf-8')
                print("File content fetched successfully")
            except Exception as e:
                print(f"Error fetching file content: {str(e)}")
                continue
                
            # Analyze code
            print("Analyzing TypeScript code...")
            metrics = analyze_typescript_code(content)
            
            # Create analysis result
            analysis = {
                'file': ts_file.filename,
                'metrics': metrics,
                'framework': framework,
                'content': content
            }
            analysis_results.append(analysis)
            
            # Generate detailed report
            report_name = os.path.basename(ts_file.filename).replace('.', '_')
            report_path = os.path.join('reports', f'typescript_analysis_{pr_number}_{report_name}.md')
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            with open(report_path, 'w') as f:
                f.write(generate_detailed_report(analysis))
            print(f"Generating detailed report: {report_path}")
            print("Analysis complete for this file")
            
        # Generate summary report
        summary_path = os.path.join('reports', f'typescript_analysis_{pr_number}_summary.md')
        with open(summary_path, 'w') as f:
            f.write(generate_summary_report(analysis_results))
        print(f"Generating summary report: {summary_path}")
        
        print("Analysis complete!")
        
    except Exception as e:
        print(f"Error in analyze_typescript_pr: {str(e)}")
        raise

def generate_critical_issues(metrics: TypeMetrics) -> str:
    """Generate formatted critical issues section"""
    issues = []
    
    if metrics.any_types > 0:
        issues.append(f"❌ Found {metrics.any_types} uses of 'any' type")
    if metrics.type_assertions > 100:
        issues.append(f"⚠️ High number of type assertions ({metrics.type_assertions})")
    if metrics.doc_coverage < 50:
        issues.append(f"❌ Low documentation coverage ({metrics.doc_coverage:.1f}%)")
    if metrics.untyped_functions > 0:
        issues.append(f"⚠️ Found {metrics.untyped_functions} functions without type annotations")
    if metrics.implicit_returns > 0:
        issues.append(f"⚠️ Found {metrics.implicit_returns} functions with implicit returns")
        
    return '\n'.join(issues) if issues else "✓ No critical issues found"

def generate_recommendations(metrics: TypeMetrics) -> str:
    """Generate prioritized recommendations"""
    recommendations = {
        'High Priority': [],
        'Medium Priority': [],
        'Low Priority': []
    }
    
    # Add recommendations based on metrics
    if metrics.any_types > 0:
        recommendations['High Priority'].append(
            f"Replace {metrics.any_types} 'any' types with specific types"
        )
    if metrics.doc_coverage < 50:
        recommendations['High Priority'].append(
            f"Increase documentation coverage (currently {metrics.doc_coverage:.1f}%)"
        )
    if metrics.type_guards < 50:
        recommendations['Medium Priority'].append(
            "Add more type guards for better type safety"
        )
    if metrics.implicit_returns > 0:
        recommendations['Medium Priority'].append(
            f"Add explicit return types to functions"
        )
    if metrics.utility_types < 10:
        recommendations['Low Priority'].append(
            "Consider using more utility types"
        )
        
    # Format recommendations
    output = []
    for priority, items in recommendations.items():
        if items:
            output.append(f"\n{priority}:")
            output.extend([f"- {item}" for item in sorted(items)])
            
    return '\n'.join(output) if output else "✓ No immediate recommendations"

def generate_detailed_report(analysis: Dict) -> str:
    """Generate detailed file analysis report"""
    metrics = analysis['metrics']
    return f"""# TypeScript Analysis - {analysis['file']}
Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. Quality Overview
```typescript
Overall Score: {metrics.quality_score:.1f}/100

Strengths:
{'✓' if metrics.type_coverage > 90 else '⚠'} Type Coverage: {metrics.type_coverage:.1f}%
{'✓' if metrics.type_guards > 100 else '⚠'} Type Guards: {metrics.type_guards}
{'✓' if metrics.any_types < 10 else '⚠'} Any Types: {metrics.any_types}

Areas for Improvement:
{'✓' if metrics.doc_coverage > 80 else '❌'} Documentation: {metrics.doc_coverage:.1f}%
{'✓' if metrics.param_doc_coverage > 80 else '❌'} Parameter Docs: {metrics.param_doc_coverage:.1f}%
{'✓' if metrics.return_doc_coverage > 80 else '❌'} Return Docs: {metrics.return_doc_coverage:.1f}%
```

## 2. Type System Details
```typescript
Type Structure:
├── Classes: {metrics.classes}
├── Interfaces: {metrics.interfaces}
├── Type Aliases: {metrics.type_aliases}
└── Generic Types: {metrics.generic_types}

Type Safety:
├── Type Guards: {metrics.type_guards}
├── Type Assertions: {metrics.type_assertions}
└── Any Types: {metrics.any_types}

Advanced Features:
├── Mapped Types: {metrics.mapped_types}
├── Utility Types: {metrics.utility_types}
├── Branded Types: {metrics.branded_types}
└── Type Predicates: {metrics.type_predicates}
```

## 3. Critical Issues
```typescript
{generate_critical_issues(metrics)}
```

## 4. Recommendations
```typescript
{generate_recommendations(metrics)}
```
"""

def generate_summary_report(analyses: List[Dict]) -> str:
    """Generate comprehensive summary report"""
    if not analyses:
        return "No TypeScript files analyzed."
        
    combined_metrics = combine_metrics(analyses)
    return f"""# TypeScript Codebase Analysis Summary

## 1. Overall Health
```typescript
Project Quality: {calculate_project_quality(combined_metrics):.1f}/100

Core Metrics:
├── Type Safety: {calculate_type_safety(combined_metrics):.1f}%
├── Documentation: {calculate_doc_coverage(combined_metrics):.1f}%
└── Best Practices: {calculate_best_practices(combined_metrics):.1f}%

File Analysis:
{generate_file_breakdown(analyses)}
```

## 2. Key Findings
```typescript
Strengths:
{generate_strengths(combined_metrics)}

Areas for Improvement:
{generate_improvements(combined_metrics)}

Critical Issues:
{generate_critical_issues_summary(analyses)}
```

## 3. Recommendations
{generate_prioritized_recommendations(analyses)}
"""

def analyze_typescript_pr(owner: str, repo: str, pr_number: int) -> None:
    """Analyze TypeScript files in a GitHub PR"""
    try:
        print(f"Analyzing PR #{pr_number} from {owner}/{repo}")
        
        # Initialize GitHub client
        g = Github(os.getenv('GITHUB_TOKEN'))
        
        # Get repository
        print("Fetching repository...")
        repository = g.get_repo(f"{owner}/{repo}")
        
        # Get PR
        print("Fetching PR...")
        pr = repository.get_pull(pr_number)
        print(f"Found PR: {pr.title}")
        
        # Get PR files
        print("Fetching PR files...")
        files = list(pr.get_files())
        typescript_files = [f for f in files if f.filename.endswith('.ts')]
        print(f"Found {len(typescript_files)} files")
        
        # Initialize analysis results
        analysis_results = []
        
        # Analyze each TypeScript file
        for ts_file in typescript_files:
            print(f"Checking file: {ts_file.filename}")
            
            if ts_file.filename.endswith('.d.ts'):
                framework = Framework.NONE
            elif 'react' in ts_file.filename.lower():
                framework = Framework.REACT
            elif 'angular' in ts_file.filename.lower():
                framework = Framework.ANGULAR
            elif 'vue' in ts_file.filename.lower():
                framework = Framework.VUE
            else:
                framework = Framework.NONE
                
            print(f"Analyzing TypeScript file: {ts_file.filename}")
            
            # Get file content
            print("Fetching file content...")
            try:
                content = repository.get_contents(ts_file.filename, ref=pr.head.sha).decoded_content.decode('utf-8')
                print("File content fetched successfully")
            except Exception as e:
                print(f"Error fetching file content: {str(e)}")
                continue
                
            # Analyze code
            print("Analyzing TypeScript code...")
            metrics = analyze_typescript_code(content)
            
            # Create analysis result
            analysis = {
                'file': ts_file.filename,
                'metrics': metrics,
                'framework': framework,
                'content': content
            }
            analysis_results.append(analysis)
            
            # Generate detailed report
            report_name = os.path.basename(ts_file.filename).replace('.', '_')
            report_path = os.path.join('reports', f'typescript_analysis_{pr_number}_{report_name}.md')
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            with open(report_path, 'w') as f:
                f.write(generate_detailed_report(analysis))
            print(f"Generating detailed report: {report_path}")
            print("Analysis complete for this file")
            
        # Generate summary report
        summary_path = os.path.join('reports', f'typescript_analysis_{pr_number}_summary.md')
        with open(summary_path, 'w') as f:
            f.write(generate_summary_report(analysis_results))
        print(f"Generating summary report: {summary_path}")
        
        print("Analysis complete!")
        
    except Exception as e:
        print(f"Error in analyze_typescript_pr: {str(e)}")
        raise
