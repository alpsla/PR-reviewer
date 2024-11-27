"""GitHub configuration and authentication handling."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_github_token() -> Optional[str]:
    """
    Get GitHub token from environment variables.
    Returns None if not configured.
    """
    return os.getenv('GITHUB_TOKEN')

def validate_github_token(token: str) -> bool:
    """
    Validate GitHub token format.
    Basic validation - does not check if token is actually valid with GitHub.
    """
    if not token:
        return False
    
    # GitHub tokens are 40 characters long
    if len(token) != 40:
        return False
        
    # Should only contain hexadecimal characters
    try:
        int(token, 16)
        return True
    except ValueError:
        return False

def get_github_config() -> dict:
    """
    Get GitHub configuration including rate limiting settings.
    """
    return {
        'rate_limit': {
            'max_retries': int(os.getenv('GITHUB_MAX_RETRIES', '3')),
            'retry_delay': int(os.getenv('GITHUB_RETRY_DELAY', '5')),
        },
        'timeout': int(os.getenv('GITHUB_TIMEOUT', '30')),
        'verify_ssl': os.getenv('GITHUB_VERIFY_SSL', 'true').lower() == 'true'
    }
