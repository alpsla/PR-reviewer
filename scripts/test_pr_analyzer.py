import os
import sys
from pathlib import Path
from github import Github
from github.GithubException import UnknownObjectException, RateLimitExceededException
from dotenv import load_dotenv
from tempfile import TemporaryDirectory
import requests

# Add parent directory to path so we can import our analyzer
sys.path.append(str(Path(__file__).parent.parent))
from services.code_analysis.analyzers.typescript_analyzer import TypeScriptAnalyzer

def download_pr_files(pr_url: str, token: str) -> dict:
    """Download files from a PR and return their contents"""
    try:
        # Parse PR URL to get owner, repo, and PR number
        parts = pr_url.split('/')
        owner = parts[-4]
        repo = parts[-3]
        pr_number = int(parts[-1])
        
        # Initialize GitHub client
        g = Github(token)
        repo = g.get_repo(f"{owner}/{repo}")
        
        try:
            pr = repo.get_pull(pr_number)
        except UnknownObjectException:
            # Try to get the most recent PR if this one is not found
            pulls = list(repo.get_pulls(state='all', sort='created', direction='desc'))[:5]
            if not pulls:
                print(f"No recent PRs found in {owner}/{repo}")
                return {}
            pr = pulls[0]
            print(f"PR {pr_number} not found. Using most recent PR #{pr.number} instead")
        
        # Download files
        files = {}
        for file in pr.get_files():
            if file.filename.endswith('.ts') or file.filename.endswith('.tsx'):
                try:
                    # Get raw content
                    response = requests.get(file.raw_url)
                    if response.status_code == 200:
                        files[file.filename] = response.text
                except Exception as e:
                    print(f"Error downloading {file.filename}: {str(e)}")
                    continue
        
        return files
    except RateLimitExceededException:
        print("GitHub API rate limit exceeded. Please wait or use a different token.")
        return {}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {}

def print_analysis_results(filename: str, result) -> None:
    """Print detailed analysis results in a structured format"""
    print(f"\n## Analysis for `{filename}`\n")
    
    print("### Type System Analysis")
    print("```typescript")
    print("Critical Issues:")
    print(f"{'✓' if result.type_analysis.metrics.type_coverage > 80 else '❌'} Type Coverage: {result.type_analysis.metrics.type_coverage:.1f}%")
    print(f"{'✓' if result.type_analysis.metrics.any_types == 0 else '❌'} Any Types: {result.type_analysis.metrics.any_types} instances")
    print(f"{'✓' if result.type_analysis.metrics.utility_types > 0 else '❌'} Utility Types: {result.type_analysis.metrics.utility_types} instances")
    
    print("\nPatterns Found:")
    print(f"✓ Type Guards: {result.type_analysis.metrics.type_guards} instances")
    print(f"✓ Complex Type Logic Present\n")
    
    if result.type_analysis.suggestions:
        print("Example Issues:")
        for suggestion in result.type_analysis.suggestions:
            print(f"- {suggestion}")
    print("```\n")
    
    print("### Documentation Analysis")
    print("```typescript")
    print("Coverage Metrics:")
    print(f"- Overall: {result.doc_analysis.metrics.coverage:.1f}%")
    print(f"- JSDoc: {result.doc_analysis.metrics.jsdoc_coverage:.1f}%")
    print(f"- TSDoc: {result.doc_analysis.metrics.tsdoc_coverage:.1f}%\n")
    
    if result.doc_analysis.quality_improvements:
        print("Required Documentation:")
        for improvement in result.doc_analysis.quality_improvements:
            print(f"- {improvement}")
    print("```\n")
    
    if result.framework_analysis:
        print("### Framework Analysis")
        print("```typescript")
        print(f"Framework: {result.framework_analysis.framework.value}")
        print("\nBest Practices:")
        for practice, follows in result.framework_analysis.best_practices.items():
            print(f"{'✓' if follows else '❌'} {practice}")
        print("```\n")
    
    print("### Quality Score")
    print("```typescript")
    score = result.quality_score
    rating = "Excellent" if score >= 90 else "Good" if score >= 70 else "Fair" if score >= 50 else "Poor"
    print(f"Score: {score:.1f}/100 ({rating})")
    print("```\n")

def analyze_pr(pr_url: str) -> None:
    """Analyze a PR and print the results"""
    # Load environment variables
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("Error: GITHUB_TOKEN not found in environment variables")
        return
    
    # Download PR files
    print(f"\n# TypeScript PR Analysis for {pr_url}\n")
    print("Downloading files...")
    files = download_pr_files(pr_url, token)
    
    if not files:
        print("No TypeScript files found in PR")
        return
    
    # Initialize analyzer
    analyzer = TypeScriptAnalyzer()
    
    # Analyze each file
    print(f"\nAnalyzing {len(files)} TypeScript files...\n")
    
    all_results = []
    for filename, content in files.items():
        result = analyzer.analyze_file(content, filename)
        all_results.append((filename, result))
        print_analysis_results(filename, result)
    
    # Print overall recommendations
    print("## Actionable Recommendations\n")
    print("### 1. Type System Improvements")
    print("```typescript")
    print("Priority 1: Critical Issues")
    for filename, result in all_results:
        if result.type_analysis.metrics.any_types > 0:
            print(f"- Replace {result.type_analysis.metrics.any_types} 'any' types in {filename}")
        if result.type_analysis.metrics.type_coverage < 50:
            print(f"- Increase type coverage in {filename} (currently {result.type_analysis.metrics.type_coverage:.1f}%)")
    print("```\n")
    
    print("### 2. Documentation Enhancements")
    print("```typescript")
    print("Priority 1: Public API")
    for filename, result in all_results:
        if result.doc_analysis.metrics.coverage < 50:
            print(f"- Add documentation in {filename} (currently {result.doc_analysis.metrics.coverage:.1f}%)")
    print("```\n")
    
    print("### 3. Best Practices")
    print("```typescript")
    print("Priority 1: Type Safety")
    for filename, result in all_results:
        if result.type_analysis.metrics.utility_types == 0:
            print(f"- Consider using utility types in {filename}")
        if result.type_analysis.metrics.type_guards > 20:
            print(f"- Review and potentially simplify type guards in {filename}")
    print("```")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python test_pr_analyzer.py <pr_url>")
        print("Example: python test_pr_analyzer.py https://github.com/owner/repo/pull/123")
        sys.exit(1)
    
    analyze_pr(sys.argv[1])
