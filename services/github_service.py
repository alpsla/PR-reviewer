from github import Github
from github.GithubException import GithubException
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self, token: str):
        """Initialize GitHub service with optional token validation"""
        if not token:
            logger.warning("No GitHub token provided")
            self.github = None
            self.token_valid = False
            return
            
        try:
            self.github = Github(token)
            self.token_valid = False  # Will be set to True after successful validation
            # Perform basic validation without requiring write access
            self._basic_validation()
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {str(e)}")
            self.github = None
            self.token_valid = False
    
    def _basic_validation(self) -> None:
        """Basic validation that only tests read access"""
        try:
            # Test basic access and authentication
            user = self.github.get_user()
            logger.info(f"Authenticated as GitHub user: {user.login}")
            self.token_valid = True
            
        except GithubException as e:
            status_code = getattr(e, 'status', None)
            if status_code == 401:
                logger.error("Invalid GitHub token - authentication failed")
            elif status_code == 403:
                logger.error(f"Token permission denied: {self._get_scope_message(e)}")
            else:
                logger.error(f"GitHub token validation failed: {str(e)}")
            self.token_valid = False
            
        except Exception as e:
            logger.error(f"Failed to validate GitHub token: {str(e)}")
            self.token_valid = False
    
    def _verify_write_access(self, repo_owner: str, repo_name: str) -> None:
        """Verify write access for specific repository"""
        if not self.github or not self.token_valid:
            raise ValueError("GitHub token not configured or invalid")
            
        try:
            # Get specific repository
            repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            
            # Test permissions on the specific repository
            try:
                # Try to create and delete a test comment on an existing issue
                issues = list(repo.get_issues()[:1])
                if issues:
                    test_comment = issues[0].create_comment("Testing write permissions - please ignore")
                    test_comment.delete()
                    logger.info(f"Successfully verified write access for repository {repo_owner}/{repo_name}")
                else:
                    logger.info(f"No issues available for testing in {repo_owner}/{repo_name}, assuming write access granted")
            except GithubException as e:
                if e.status == 403:
                    raise ValueError(f"Token lacks write permissions for repository {repo_owner}/{repo_name}")
                raise
                
        except GithubException as e:
            status_code = getattr(e, 'status', None)
            if status_code == 403:
                scope_message = self._get_scope_message(e)
                raise ValueError(f"Token permission denied for repository {repo_owner}/{repo_name}: {scope_message}")
            elif status_code == 404:
                raise ValueError(f"Repository {repo_owner}/{repo_name} not found or access denied")
            else:
                raise ValueError(f"GitHub token validation failed: {str(e)}")
    
    def _get_scope_message(self, error: GithubException) -> str:
        """Extract detailed scope information from GitHub error messages"""
        error_message = str(error)
        if 'scope' in error_message.lower():
            if 'repo' in error_message:
                return "Token requires 'repo' scope for private repositories"
            elif 'public_repo' in error_message:
                return "Token requires 'public_repo' scope for public repositories"
            return f"Token lacks required scopes: {error_message}"
        return "Token lacks required permissions"

    def fetch_pr_data(self, pr_details: Dict) -> Dict:
        """Fetches PR data using GitHub API with enhanced error handling"""
        if not self.github or not self.token_valid:
            raise ValueError("GitHub token not configured or invalid")
            
        try:
            repo = self.github.get_repo(f"{pr_details['owner']}/{pr_details['repo']}")
            pr = repo.get_pull(pr_details['number'])
            
            return {
                'title': pr.title,
                'body': pr.body,
                'state': pr.state,
                'commits': pr.commits,
                'changed_files': pr.changed_files,
                'additions': pr.additions,
                'deletions': pr.deletions
            }
        except GithubException as e:
            if e.status == 404:
                raise ValueError("Pull request not found. Please verify the PR URL is correct")
            elif e.status == 403:
                raise ValueError("Access denied. Please check repository permissions and ensure token has required access")
            else:
                raise ValueError(f"Failed to fetch PR data: {str(e)}")
    
    async def fetch_pr_files(self, pr_details: Dict) -> List[Dict]:
        """Fetches files changed in the PR with enhanced error handling"""
        if not self.github or not self.token_valid:
            raise ValueError("GitHub token not configured or invalid")
            
        try:
            repo = self.github.get_repo(f"{pr_details['owner']}/{pr_details['repo']}")
            pr = repo.get_pull(pr_details['number'])
            
            files_data = []
            for f in pr.get_files():
                files_data.append({
                    'filename': f.filename,
                    'status': f.status,
                    'additions': f.additions,
                    'deletions': f.deletions,
                    'changes': f.changes,
                    'patch': f.patch
                })
            return files_data
        except GithubException as e:
            if e.status == 403:
                raise ValueError("Access denied. Please check repository permissions for file access")
            else:
                raise ValueError(f"Failed to fetch PR files: {str(e)}")
    
    async def fetch_pr_comments(self, pr_details: Dict) -> List[Dict]:
        """Fetches PR comments with enhanced error handling"""
        if not self.github or not self.token_valid:
            raise ValueError("GitHub token not configured or invalid")
            
        try:
            repo = self.github.get_repo(f"{pr_details['owner']}/{pr_details['repo']}")
            pr = repo.get_pull(pr_details['number'])
            
            comments_data = []
            for comment in pr.get_comments():
                comments_data.append({
                    'user': comment.user.login,
                    'body': comment.body,
                    'created_at': comment.created_at
                })
            return comments_data
        except GithubException as e:
            if e.status == 403:
                raise ValueError("Access denied. Please check permissions for viewing comments")
            else:
                raise ValueError(f"Failed to fetch PR comments: {str(e)}")
            
    def post_pr_comment(self, pr_details: Dict, comment_text: str) -> Dict:
        """Posts a comment on the PR with enhanced error handling"""
        if not self.github or not self.token_valid:
            raise ValueError("GitHub token not configured or invalid")
            
        # Verify write access for specific repository
        self._verify_write_access(pr_details['owner'], pr_details['repo'])
        
        try:
            repo = self.github.get_repo(f"{pr_details['owner']}/{pr_details['repo']}")
            pr = repo.get_pull(pr_details['number'])
            
            comment = pr.create_issue_comment(comment_text)
            
            return {
                'id': str(comment.id),
                'url': comment.html_url
            }
        except GithubException as e:
            if e.status == 403:
                raise ValueError(
                    f"Cannot post comment to {pr_details['owner']}/{pr_details['repo']}. "
                    "Please ensure the token has proper write access for this repository."
                )
            elif e.status == 404:
                raise ValueError("Repository or PR not found. Please verify the URL and permissions")
            else:
                raise ValueError(f"Failed to post PR comment: {str(e)}")
