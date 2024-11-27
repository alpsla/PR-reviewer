#!/usr/bin/env python3

import json
import glob
import os
from datetime import datetime
import argparse
from typing import Dict, List
import re

def get_latest_log_file(log_pattern: str) -> str:
    """Get the most recent log file matching the pattern."""
    files = glob.glob(log_pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def parse_log_file(log_file: str) -> List[Dict]:
    """Parse JSON log file and return list of log entries."""
    entries = []
    with open(log_file, 'r') as f:
        for line in f:
            try:
                # Try parsing as JSON first
                entry = json.loads(line.strip())
                entries.append({
                    'type': 'json',
                    'content': entry
                })
            except json.JSONDecodeError:
                # If not JSON, check if it's a pytest failure
                if any(marker in line for marker in ['FAILED', 'AssertionError:', 'Error:', 'FAILURES']):
                    entries.append({
                        'type': 'pytest',
                        'content': line.strip(),
                        'timestamp': datetime.now().isoformat(),
                        'component': 'pytest'
                    })
    return entries

def filter_test_failures(entries: List[Dict]) -> List[Dict]:
    """Filter log entries for test failures and assertion errors."""
    failures = []
    current_failure = None
    
    for entry in entries:
        if entry['type'] == 'json':
            message = entry['content'].get('message', '').lower()
            if any(keyword in message for keyword in ['assertionerror', 'fail', 'error']):
                failures.append(entry)
        else:  # pytest entry
            line = entry['content']
            if 'FAILED' in line or 'AssertionError:' in line:
                if current_failure:
                    failures.append(current_failure)
                current_failure = entry
            elif current_failure and line.strip():
                current_failure['content'] += '\n' + line
    
    if current_failure:
        failures.append(current_failure)
    
    return failures

def format_failure(entry: Dict) -> str:
    """Format a failure entry for display."""
    if entry['type'] == 'json':
        timestamp = entry['content']['timestamp']
        return f"""
Time: {timestamp}
Component: {entry['content'].get('component', 'N/A')}
Message: {entry['content'].get('message', 'N/A')}
Context: {json.dumps(entry['content'].get('context', {}), indent=2)}
{'=' * 80}
"""
    else:  # pytest entry
        return f"""
Time: {entry['timestamp']}
Component: {entry['component']}
Failure:
{entry['content']}
{'=' * 80}
"""

def write_failures_to_file(failures: List[Dict], output_file: str):
    """Write failures to a dedicated file."""
    with open(output_file, 'w') as f:
        f.write(f"Test Failures Report - Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Failures Found: {len(failures)}\n")
        f.write("=" * 80 + "\n\n")
        
        for failure in failures:
            f.write(format_failure(failure))

def main():
    parser = argparse.ArgumentParser(description='Filter test failures from log files')
    parser.add_argument('--log-dir', default='logs', help='Directory containing log files')
    parser.add_argument('--output', help='Output file for failures (optional)')
    args = parser.parse_args()

    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), args.log_dir)
    
    # Get the latest log files
    analyzer_log = get_latest_log_file(os.path.join(log_dir, 'typescript_analyzer_*.log'))
    error_log = get_latest_log_file(os.path.join(log_dir, 'typescript_analyzer_error_*.log'))
    pytest_log = get_latest_log_file(os.path.join(log_dir, '.pytest_cache/v/cache/nodeids'))
    
    if not any([analyzer_log, error_log, pytest_log]):
        print("No log files found!")
        return

    all_entries = []
    
    # Parse logs
    for log_file in [analyzer_log, error_log]:
        if log_file:
            all_entries.extend(parse_log_file(log_file))

    # Filter failures
    failures = filter_test_failures(all_entries)
    
    if not failures:
        print("No test failures found in the logs!")
        return

    # Generate output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = os.path.join(log_dir, f'test_failures_{timestamp}.log')

    # Write failures to file
    write_failures_to_file(failures, args.output)
    
    print(f"Found {len(failures)} test failures.")
    print(f"Failures have been written to: {args.output}")
    print("\nFailure details:")
    for failure in failures:
        print(format_failure(failure))

if __name__ == '__main__':
    main()
