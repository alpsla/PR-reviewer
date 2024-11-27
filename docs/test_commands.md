# Test Commands Reference

This document contains commands for running various test suites in the PR-reviewer project.

## TypeScript Tests

Run all TypeScript-related tests:
```bash
# Run TypeScript analyzer tests
pytest tests/code_analysis/test_typescript_analyzer.py -v

# Run TypeScript collector tests
pytest tests/code_analysis/test_typescript_collector.py -v

# Run TypeScript React logging tests
pytest tests/code_analysis/test_typescript_react_logging.py -v
```

Run all TypeScript tests at once:
```bash
python3 -m pytest tests/code_analysis/test_typescript_analyzer.py tests/code_analysis/test_typescript_collector.py tests/code_analysis/test_typescript_react_logging.py -v
```

### Test Descriptions:
- `test_typescript_analyzer.py`: Tests for TypeScript code analysis functionality
- `test_typescript_collector.py`: Tests for TypeScript code collection and parsing
- `test_typescript_react_logging.py`: Tests for React component analysis and logging

## Options
- `-v`: Verbose output
- `-s`: Show print statements (don't capture stdout/stderr)
- `-k "test_name"`: Run specific test by name
- `--pdb`: Drop into debugger on failures
