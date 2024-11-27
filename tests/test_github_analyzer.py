"""Tests for GitHub repository analysis functionality."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from github import Github, GithubException, RateLimitExceededException
from services.code_analysis.analyzers.typescript_analyzer import TypeScriptAnalyzer

@pytest.fixture
def mock_github(monkeypatch):
    mock = MagicMock()
    with patch('github.Github', return_value=mock):
        yield mock

@pytest.fixture
def mock_repo():
    mock = Mock()
    mock.get_contents.return_value = []
    return mock

@pytest.fixture
def mock_content_file():
    mock = Mock()
    mock.type = "file"
    mock.name = "test.ts"
    mock.path = "src/test.ts"
    mock.decoded_content = b"const test: string = 'test';"
    return mock

def test_github_initialization():
    """Test GitHub client initialization"""
    # Test with valid token
    with patch('services.code_analysis.analyzers.typescript_analyzer.Github') as mock_github:
        mock_user = Mock()
        mock_user.login = 'test_user'
        mock_github.return_value.get_user.return_value = mock_user
        
        with patch('config.github_config.get_github_token', return_value='a' * 40):
            analyzer = TypeScriptAnalyzer()
            assert analyzer.github is not None
            assert analyzer.github.get_user().login == 'test_user'
        
    # Test with invalid token
    with patch('services.code_analysis.analyzers.typescript_analyzer.Github') as mock_github:
        mock_github.return_value.get_user.side_effect = Exception("Invalid token")
        
        with patch('config.github_config.get_github_token', return_value='invalid'):
            analyzer = TypeScriptAnalyzer()
            assert analyzer.github is None

def test_parse_github_url():
    """Test GitHub URL parsing"""
    analyzer = TypeScriptAnalyzer()
    
    # Test HTTPS URL
    owner, repo = analyzer._parse_github_url('https://github.com/owner/repo.git')
    assert owner == 'owner'
    assert repo == 'repo'
    
    # Test SSH URL
    owner, repo = analyzer._parse_github_url('git@github.com:owner/repo.git')
    assert owner == 'owner'
    assert repo == 'repo'
    
    # Test web URL
    owner, repo = analyzer._parse_github_url('https://github.com/owner/repo')
    assert owner == 'owner'
    assert repo == 'repo'
    
    # Test invalid URL
    with pytest.raises(ValueError):
        analyzer._parse_github_url('invalid_url')

def test_analyze_github_repo(mock_github, mock_repo, mock_content_file):
    """Test GitHub repository analysis"""
    # Setup mocks
    mock_github.get_repo.return_value = mock_repo
    mock_repo.get_contents.return_value = [mock_content_file]
    mock_content_file.decoded_content = b"const test: string = 'test';"
    
    with patch('config.github_config.get_github_token', return_value='a' * 40):
        analyzer = TypeScriptAnalyzer()
        analyzer.github = mock_github
        
        # Test successful analysis
        result = analyzer.analyze_github_repo('https://github.com/owner/repo')
        assert result is not None
        assert isinstance(result, dict)

def test_rate_limit_handling(mock_github, mock_repo):
    """Test GitHub rate limit handling"""
    # Setup rate limit exception
    mock_github.get_repo.side_effect = [
        RateLimitExceededException(Mock(), Mock()),  # First call fails
        mock_repo  # Second call succeeds
    ]
    mock_github.rate_limiting_resettime = 0  # Immediate retry
    
    with patch('config.github_config.get_github_token', return_value='a' * 40):
        analyzer = TypeScriptAnalyzer()
        analyzer.github = mock_github
        analyzer.github_config = {
            'rate_limit': {
                'max_retries': 2,
                'retry_delay': 0
            }
        }
        
        # Should succeed after retry
        repo = analyzer._get_repo_with_retry('owner/repo')
        assert repo == mock_repo
        assert mock_github.get_repo.call_count == 2

def test_file_content_handling(mock_github, mock_content_file):
    """Test file content handling"""
    with patch('config.github_config.get_github_token', return_value='a' * 40):
        analyzer = TypeScriptAnalyzer()
        analyzer.github = mock_github
        analyzer.github_config = {
            'rate_limit': {
                'max_retries': 2,
                'retry_delay': 0
            }
        }
        
        # Test successful content retrieval
        mock_content_file.decoded_content = b"const test: string = 'test';"
        content = analyzer._get_file_content_with_retry(mock_content_file)
        assert content == "const test: string = 'test';"
        
        # Test failed content retrieval
        mock_content_file.decoded_content = None
        content = analyzer._get_file_content_with_retry(mock_content_file)
        assert content is None
