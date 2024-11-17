from github import Github
from github.GithubException import GithubException
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self, token: str):
        """Initialize GitHub service with token validation"""
        if not token:
            raise ValueError("GitHub token is required")
        self.github = Github(token)
        self._validate_token()
    
    def _validate_token(self) -> None:
        """Validate GitHub token permissions"""
        try:
            # Test basic access
            user = self.github.get_user()
            logger.info(f"Authenticated as GitHub user: {user.login}")
            
            # Check token permissions by attempting to list repos
            try:
                repos = user.get_repos()
                # Test if we can access at least one repo
                next(iter(repos), None)
                logger.info("GitHub token validated successfully")
            except StopIteration:
                # No repos found, but access was granted
                logger.info("GitHub token validated (no repositories found)")
                
        except GithubException as e:
            if e.status == 401:
                raise ValueError("Invalid GitHub token")
            elif e.status == 403:
                raise ValueError("Token lacks required permissions")
            else:
                raise ValueError(f"GitHub token validation failed: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to validate GitHub token: {str(e)}")
    
    def fetch_pr_data(self, pr_details: Dict) -> Dict:
        """Fetches PR data using GitHub API with enhanced error handling"""
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
                raise ValueError("Pull request not found")
            elif e.status == 403:
                raise ValueError("Access denied. Please check repository permissions")
            else:
                raise ValueError(f"Failed to fetch PR data: {str(e)}")
    
    def fetch_pr_files(self, pr_details: Dict) -> List[Dict]:
        """Fetches files changed in the PR with enhanced error handling"""
        try:
            repo = self.github.get_repo(f"{pr_details['owner']}/{pr_details['repo']}")
            pr = repo.get_pull(pr_details['number'])
            
            return [{
                'filename': f.filename,
                'status': f.status,
                'additions': f.additions,
                'deletions': f.deletions,
                'changes': f.changes,
                'patch': f.patch
            } for f in pr.get_files()]
        except GithubException as e:
            if e.status == 403:
                raise ValueError("Access denied. Please check repository permissions")
            else:
                raise ValueError(f"Failed to fetch PR files: {str(e)}")
    
    def fetch_pr_comments(self, pr_details: Dict) -> List[Dict]:
        """Fetches PR comments with enhanced error handling"""
        try:
            repo = self.github.get_repo(f"{pr_details['owner']}/{pr_details['repo']}")
            pr = repo.get_pull(pr_details['number'])
            
            return [{
                'user': comment.user.login,
                'body': comment.body,
                'created_at': comment.created_at
            } for comment in pr.get_comments()]
        except GithubException as e:
            if e.status == 403:
                raise ValueError("Access denied. Please check repository permissions")
            else:
                raise ValueError(f"Failed to fetch PR comments: {str(e)}")
            
    def post_pr_comment(self, pr_details: Dict, comment_text: str) -> Dict:
        """Posts a comment on the PR with enhanced error handling"""
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
                raise ValueError("Cannot post comment. Please check repository permissions and ensure token has write access")
            else:
                raise ValueError(f"Failed to post PR comment: {str(e)}")
