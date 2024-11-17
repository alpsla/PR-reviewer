from urllib.parse import urlparse, parse_qs
import re

def parse_pr_url(url: str) -> dict:
    """
    Parses GitHub PR URL to extract owner, repo, and PR number
    Example URL: https://github.com/owner/repo/pull/123
    """
    try:
        # Parse URL
        parsed = urlparse(url)
        
        # Verify it's a GitHub URL
        if parsed.netloc != 'github.com':
            raise ValueError("Not a GitHub URL")
        
        # Extract path components
        path_parts = parsed.path.strip('/').split('/')
        
        # Verify it's a PR URL
        if len(path_parts) != 4 or path_parts[2] != 'pull':
            raise ValueError("Not a valid PR URL")
        
        return {
            'owner': path_parts[0],
            'repo': path_parts[1],
            'number': int(path_parts[3])
        }
        
    except Exception as e:
        raise ValueError(f"Failed to parse PR URL: {str(e)}")
