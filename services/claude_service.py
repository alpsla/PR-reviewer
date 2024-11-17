import anthropic
from typing import Dict
import re
import json

class ClaudeService:
    def __init__(self, api_key: str):
        """Initialize Claude service with API key validation"""
        if not api_key:
            # Use mock service if no API key is provided
            self.use_mock = True
            return
            
        try:
            self.use_mock = False
            self.client = anthropic.Anthropic(
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com",
                    "X-API-Lang": "python",
                    "X-Client-Version": "1.0.0"
                }
            )
        except Exception as e:
            # Fall back to mock service on initialization error
            self.use_mock = True
    
    def analyze_pr(self, context: Dict) -> Dict:
        """Analyzes PR using Claude API with fallback to mock review"""
        if self.use_mock:
            return self.mock_review(context)
            
        try:
            prompt = self._build_analysis_prompt(context)
            
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7,
                system="You are a code review expert. Analyze pull requests thoroughly and provide constructive feedback focusing on code quality, security, and best practices."
            )
            
            return self._parse_claude_response(message.content)
            
        except Exception as e:
            context['error'] = e
            return self.mock_review(context)
    
    def mock_review(self, context: Dict) -> Dict:
        """Generate a detailed mock review response with PR-specific context"""
        files_count = context['pr_data']['changed_files']
        additions = context['pr_data']['additions']
        deletions = context['pr_data']['deletions']
        
        # Get file types for more specific feedback
        file_extensions = set()
        primary_language = "code"
        if 'files' in context:
            for file in context['files']:
                ext = file['filename'].split('.')[-1] if '.' in file['filename'] else ''
                if ext:
                    file_extensions.add(ext)
            if file_extensions:
                primary_language = max(file_extensions, key=list(file_extensions).count)

        mock_response = f"""[MOCK REVIEW - FOR TESTING PURPOSES]

Summary of Changes:
- Files Modified: {files_count} ({', '.join(file_extensions) if file_extensions else 'various types'})
- Lines Added: {additions}
- Lines Removed: {deletions}
- Primary Language: {primary_language}

Code Quality Analysis:
1. Best Practices
- ✓ Code follows standard formatting conventions
- ⚠ Consider adding more documentation for complex logic
- ✓ Variable naming is consistent
- ⚠ File organization could be improved

2. Potential Issues
- No major issues identified
- Consider adding error handling for edge cases
- Unit tests could be expanded
- Review error handling patterns

3. Security Considerations
- ✓ No obvious security vulnerabilities
- Consider adding input validation where applicable
- Review authentication handling if present
- Verify data sanitization practices

4. Performance Implications
- Changes appear to have minimal performance impact
- Consider caching for repeated operations
- Monitor resource usage in production
- Review database query optimization

5. Suggested Improvements
- Add more inline documentation
- Consider breaking down complex functions
- Add comprehensive error handling
- Implement logging for better debugging

Note: This is a mock review generated for testing purposes."""

        return {
            'summary': mock_response,
            'structured': True,
            'is_mock': True,
            'mock_reason': 'APIUnavailable'
        }
    
    def _build_analysis_prompt(self, context: Dict) -> str:
        """Builds a comprehensive analysis prompt for Claude"""
        pr_data = context['pr_data']
        files = context.get('files', [])
        comments = context.get('comments', [])

        prompt = f"""Please review this pull request and provide detailed feedback:

PR Details:
Title: {pr_data['title']}
Description: {pr_data['body'] or 'No description provided'}

Changes Overview:
- Files changed: {pr_data['changed_files']}
- Additions: {pr_data['additions']}
- Deletions: {pr_data['deletions']}

Modified Files:
{self._format_files(files)}

Discussion Context:
{self._format_comments(comments)}

Please analyze:
1. Code quality and best practices
   - Code structure and organization
   - Naming conventions
   - Documentation completeness

2. Potential issues or bugs
   - Logic errors
   - Edge cases
   - Error handling

3. Security considerations
   - Input validation
   - Authentication/authorization
   - Data protection

4. Performance implications
   - Resource usage
   - Optimization opportunities
   - Scalability concerns

5. Suggested improvements
   - Code organization
   - Testing coverage
   - Documentation

Provide your review in a structured format with clear sections and specific examples where applicable."""
        
        return prompt
    
    def _format_files(self, files: list) -> str:
        """Formats the files list with detailed changes"""
        if not files:
            return "No file information available"
            
        return "\n".join([
            f"- {f['filename']}:\n"
            f"  • Changes: +{f['additions']}, -{f['deletions']}\n"
            f"  • Status: {f['status']}"
            for f in files
        ])
    
    def _format_comments(self, comments: list) -> str:
        """Formats PR comments for context"""
        if not comments:
            return "No previous discussion found"
            
        return "Previous Discussion:\n" + "\n".join([
            f"- {comment['user']}: {comment['body'][:200]}..."
            if len(comment['body']) > 200 else
            f"- {comment['user']}: {comment['body']}"
            for comment in comments[:5]  # Limit to last 5 comments
        ])
    
    def _parse_claude_response(self, response: str) -> Dict:
        """Parses Claude's response with validation"""
        if not response:
            raise ValueError("Empty response from Claude")
            
        return {
            'summary': response,
            'structured': True,
            'is_mock': False
        }