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
    
    def analyze_pr(self, context: Dict) -> Dict:
        """Analyzes PR using Claude API with improved error handling"""
        try:
            prompt = self._build_analysis_prompt(context)
            
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7,  # Add temperature for consistent output
                system="You are a code review expert. Analyze pull requests thoroughly and provide constructive feedback."
            )
            
            return self._parse_claude_response(message.content)
            
        except anthropic.RateLimitError:
            raise Exception("Rate limit exceeded. Please try again later.")
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
            'structured': True
        }
