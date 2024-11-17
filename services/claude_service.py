import anthropic
from typing import Dict
import re
import json

class ClaudeService:
    def __init__(self, api_key: str):
        if not api_key:
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
            self.use_mock = True
    
    def analyze_pr(self, context: Dict) -> Dict:
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
        files_count = context['pr_data']['changed_files']
        additions = context['pr_data']['additions']
        deletions = context['pr_data']['deletions']
        
        file_extensions = set()
        primary_language = "code"
        if 'files' in context:
            for file in context['files']:
                ext = file['filename'].split('.')[-1] if '.' in file['filename'] else ''
                if ext:
                    file_extensions.add(ext)
            if file_extensions:
                primary_language = max(file_extensions, key=list(file_extensions).count)

        mock_response = f"""
<div class="review-section">
    <h3>Summary of Changes</h3>
    <div class="card mb-3">
        <div class="card-body">
            <ul class="list-unstyled mb-0">
                <li><i class="bi bi-file-earmark-text"></i> Files Modified: {files_count} ({', '.join(file_extensions) if file_extensions else 'various types'})</li>
                <li><i class="bi bi-plus-circle"></i> Lines Added: {additions}</li>
                <li><i class="bi bi-dash-circle"></i> Lines Removed: {deletions}</li>
                <li><i class="bi bi-code-square"></i> Primary Language: {primary_language}</li>
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Code Quality Analysis</h3>
    <div class="card mb-3">
        <div class="card-body">
            <h4>Best Practices</h4>
            <ul class="list-unstyled mb-3">
                <li><i class="bi bi-check-circle text-success"></i> Code follows standard formatting conventions</li>
                <li><i class="bi bi-exclamation-triangle text-warning"></i> Consider adding more documentation for complex logic</li>
                <li><i class="bi bi-check-circle text-success"></i> Variable naming is consistent</li>
                <li><i class="bi bi-exclamation-triangle text-warning"></i> File organization could be improved</li>
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Potential Issues</h3>
    <div class="card mb-3">
        <div class="card-body">
            <ul class="list-unstyled mb-0">
                <li><i class="bi bi-info-circle text-info"></i> No major issues identified</li>
                <li><i class="bi bi-exclamation-circle text-warning"></i> Consider adding error handling for edge cases</li>
                <li><i class="bi bi-exclamation-circle text-warning"></i> Unit tests could be expanded</li>
                <li><i class="bi bi-exclamation-circle text-warning"></i> Review error handling patterns</li>
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Security Considerations</h3>
    <div class="card mb-3">
        <div class="card-body">
            <ul class="list-unstyled mb-0">
                <li><i class="bi bi-check-circle text-success"></i> No obvious security vulnerabilities</li>
                <li><i class="bi bi-shield-exclamation text-warning"></i> Consider adding input validation where applicable</li>
                <li><i class="bi bi-shield-exclamation text-warning"></i> Review authentication handling if present</li>
                <li><i class="bi bi-shield-exclamation text-warning"></i> Verify data sanitization practices</li>
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Performance Implications</h3>
    <div class="card mb-3">
        <div class="card-body">
            <ul class="list-unstyled mb-0">
                <li><i class="bi bi-speedometer2"></i> Changes appear to have minimal performance impact</li>
                <li><i class="bi bi-lightning-charge"></i> Consider caching for repeated operations</li>
                <li><i class="bi bi-graph-up"></i> Monitor resource usage in production</li>
                <li><i class="bi bi-database-check"></i> Review database query optimization</li>
            </ul>
        </div>
    </div>
</div>

<div class="review-section">
    <h3>Suggested Improvements</h3>
    <div class="card mb-3">
        <div class="card-body">
            <ul class="list-unstyled mb-0">
                <li><i class="bi bi-pencil"></i> Add more inline documentation</li>
                <li><i class="bi bi-diagram-2"></i> Consider breaking down complex functions</li>
                <li><i class="bi bi-exclamation-diamond"></i> Add comprehensive error handling</li>
                <li><i class="bi bi-journal-text"></i> Implement logging for better debugging</li>
            </ul>
        </div>
    </div>
</div>

<div class="alert alert-warning mt-3">
    <i class="bi bi-info-circle"></i> Note: This is a mock review generated for testing purposes.
</div>"""

        return {
            'summary': mock_response,
            'structured': True,
            'is_mock': True,
            'mock_reason': 'APIUnavailable'
        }
    
    def _build_analysis_prompt(self, context: Dict) -> str:
        pr_data = context['pr_data']
        files = context.get('files', [])
        comments = context.get('comments', [])

        prompt = f"""Please review this pull request and provide detailed feedback using HTML formatting with Bootstrap classes:

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

Please analyze and format your response with proper HTML structure using Bootstrap classes and icons:
1. Code quality and best practices (use bi-check-circle for good practices, bi-exclamation-triangle for warnings)
2. Potential issues or bugs (use bi-exclamation-circle for issues)
3. Security considerations (use bi-shield-exclamation for security warnings)
4. Performance implications (use bi-speedometer2 and related icons)
5. Suggested improvements (use appropriate icons for each suggestion)

Format each section using Bootstrap cards and proper semantic HTML."""
        
        return prompt
    
    def _format_files(self, files: list) -> str:
        if not files:
            return "No file information available"
            
        return "\n".join([
            f"- {f['filename']}:\n"
            f"  • Changes: +{f['additions']}, -{f['deletions']}\n"
            f"  • Status: {f['status']}"
            for f in files
        ])
    
    def _format_comments(self, comments: list) -> str:
        if not comments:
            return "No previous discussion found"
            
        return "Previous Discussion:\n" + "\n".join([
            f"- {comment['user']}: {comment['body'][:200]}..."
            if len(comment['body']) > 200 else
            f"- {comment['user']}: {comment['body']}"
            for comment in comments[:5]
        ])
    
    def _parse_claude_response(self, response: str) -> Dict:
        if not response or not isinstance(response, str):
            raise ValueError("Invalid response from Claude")
            
        return {
            'summary': response,
            'structured': True,
            'is_mock': False
        }
