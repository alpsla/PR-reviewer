import anthropic
from typing import Dict
import re

class ClaudeService:
    def __init__(self, api_key: str):
        """Initialize Claude service with API key validation"""
        if not api_key:
            raise ValueError("Claude API key is required")
            
        # Verify API key format (should start with 'sk-ant-')
        if not re.match(r'^sk-ant-', api_key):
            raise ValueError("Invalid Claude API key format. Key should start with 'sk-ant-'")
            
        try:
            self.client = anthropic.Anthropic(
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com",  # Set referer for API tracking
                    "X-API-Lang": "python"  # Indicate API client language
                }
            )
            # Verify client initialization by accessing a property
            _ = self.client.api_key
        except anthropic.AuthenticationError as e:
            raise ValueError(f"Claude API authentication failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to initialize Claude client: {str(e)}")

    def mock_review(self, context: Dict) -> Dict:
        """Generate a mock review response for testing or when API credits are insufficient"""
        files_count = context['pr_data']['changed_files']
        additions = context['pr_data']['additions']
        deletions = context['pr_data']['deletions']
        
        mock_response = f"""[MOCK REVIEW - FOR TESTING PURPOSES]

Summary of Changes:
- Files Modified: {files_count}
- Lines Added: {additions}
- Lines Removed: {deletions}

Code Quality Analysis:
1. Best Practices
- ✓ Code follows standard formatting conventions
- ⚠ Consider adding more documentation for complex logic
- ✓ Variable naming is consistent

2. Potential Issues
- No major issues identified
- Consider adding error handling for edge cases
- Unit tests could be expanded

3. Security Considerations
- ✓ No obvious security vulnerabilities
- Consider adding input validation where applicable
- Review authentication handling if present

4. Performance Implications
- Changes appear to have minimal performance impact
- Consider caching for repeated operations
- Monitor resource usage in production

5. Suggested Improvements
- Add more inline documentation
- Consider breaking down complex functions
- Add comprehensive error handling

Note: This is a mock review generated due to API credit limitations. Please check back later for a full AI-powered review."""

        return {
            'summary': mock_response,
            'structured': True,
            'is_mock': True
        }
    
    def analyze_pr(self, context: Dict) -> Dict:
        """Analyzes PR using Claude API with improved error handling and mock fallback"""
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
                system="You are a code review expert. Analyze pull requests thoroughly and provide constructive feedback."
            )
            
            return self._parse_claude_response(message.content)
            
        except anthropic.RateLimitError:
            return self.mock_review(context)
        except anthropic.InsufficientCreditsError:
            return self.mock_review(context)
        except anthropic.AuthenticationError:
            raise Exception("Authentication failed. Please check your API key.")
        except anthropic.BadRequestError as e:
            raise Exception(f"Invalid request: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to analyze PR with Claude: {str(e)}")
    
    def _build_analysis_prompt(self, context: Dict) -> str:
        """Builds the analysis prompt for Claude"""
        return f"""Please review this pull request and provide detailed feedback:

PR Details:
Title: {context['pr_data']['title']}
Description: {context['pr_data']['body']}

Changes:
- Files changed: {context['pr_data']['changed_files']}
- Additions: {context['pr_data']['additions']}
- Deletions: {context['pr_data']['deletions']}

Files Modified:
{self._format_files(context['files'])}

Please analyze:
1. Code quality and best practices
2. Potential issues or bugs
3. Security considerations
4. Performance implications
5. Suggested improvements

Provide your review in a structured format with clear sections."""
    
    def _format_files(self, files: list) -> str:
        """Formats the files list for the prompt"""
        return "\n".join([
            f"- {f['filename']}: {f['additions']} additions, {f['deletions']} deletions"
            for f in files
        ])
    
    def _parse_claude_response(self, response: str) -> Dict:
        """Parses Claude's response into structured format"""
        if not response:
            raise ValueError("Empty response from Claude")
            
        return {
            'summary': response,
            'structured': True,
            'is_mock': False
        }
