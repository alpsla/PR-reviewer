#!/usr/bin/env python3

import os
import sys
from services.code_analysis.analyzers.typescript_analyzer import TypeScriptAnalyzer
from logging_config import setup_logging, get_logger

def main():
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    # PR URL to analyze
    pr_url = "https://github.com/DefinitelyTyped/DefinitelyTyped/pull/67889"
    
    try:
        # Initialize analyzer
        analyzer = TypeScriptAnalyzer()
        
        # Run PR analysis
        logger.info(f"Starting analysis of PR: {pr_url}")
        results = analyzer.analyze_pull_request(pr_url)
        
        # Print results
        print("\nAnalysis Results:")
        print("================")
        print(f"Files Analyzed: {results.get('files_analyzed', 0)}")
        print(f"Type Coverage: {results.get('type_coverage', 0):.2f}%")
        print(f"Documentation Coverage: {results.get('doc_coverage', 0):.2f}%")
        print(f"Quality Score: {results.get('quality_score', 0):.2f}/100")
        
        if results.get('issues'):
            print("\nIssues Found:")
            for issue in results['issues']:
                print(f"- {issue}")
        
        if results.get('suggestions'):
            print("\nSuggestions:")
            for suggestion in results['suggestions']:
                print(f"- {suggestion}")
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
