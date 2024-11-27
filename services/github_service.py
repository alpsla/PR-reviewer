from github import Github
from github.GithubException import GithubException
from typing import Dict, List, Optional
import logging
import re

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
            self.token_valid = True  # Set to True initially, will be set to False if validation fails
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

    def fetch_pr_data(self, pr_details: Dict[str, str]) -> Optional[Dict]:
        """Fetch pull request data from GitHub."""
        try:
            repo_name = f"{pr_details['owner']}/{pr_details['repo']}"
            repo = self.github.get_repo(repo_name)
            pr_number = int(pr_details['number'])
            pr = repo.get_pull(pr_number)
            
            # Convert PR object to dict
            pr_data = {
                'title': pr.title,
                'body': pr.body,
                'state': pr.state,
                'created_at': pr.created_at.isoformat(),
                'updated_at': pr.updated_at.isoformat(),
                'user': {
                    'login': pr.user.login,
                    'avatar_url': pr.user.avatar_url
                },
                'base': {
                    'repo': {
                        'full_name': repo_name
                    }
                },
                'head': {
                    'ref': pr.head.ref,
                    'sha': pr.head.sha
                }
            }
            
            return pr_data
            
        except Exception as e:
            logger.error(f"Failed to fetch PR data: {str(e)}")
            return None
            
    def fetch_pr_files_sync(self, pr_details: Dict[str, str]) -> Optional[List[Dict]]:
        """Fetch files from a pull request."""
        try:
            repo_name = f"{pr_details['owner']}/{pr_details['repo']}"
            repo = self.github.get_repo(repo_name)
            pr_number = int(pr_details['number'])
            pr = repo.get_pull(pr_number)
            
            files = []
            for file in pr.get_files():
                try:
                    # Get file content from the PR's head commit
                    content = None
                    if file.status != 'removed':  # Only get content for non-removed files
                        try:
                            content = repo.get_contents(file.filename, ref=pr.head.sha)
                            content = content.decoded_content.decode('utf-8') if content else None
                            logger.debug(f"Successfully fetched content for {file.filename}")
                        except Exception as e:
                            logger.warning(f"Failed to get content for {file.filename}: {str(e)}")
                            # If direct content fetch fails, try using raw_url
                            if hasattr(file, 'raw_url') and file.raw_url:
                                try:
                                    import requests
                                    response = requests.get(file.raw_url)
                                    if response.status_code == 200:
                                        content = response.text
                                        logger.debug(f"Successfully fetched content from raw_url for {file.filename}")
                                except Exception as e:
                                    logger.warning(f"Failed to get content from raw_url for {file.filename}: {str(e)}")
                    
                    file_data = {
                        'filename': file.filename,
                        'status': file.status,
                        'additions': file.additions,
                        'deletions': file.deletions,
                        'changes': file.changes,
                        'patch': file.patch if hasattr(file, 'patch') else None,
                        'raw_url': file.raw_url if hasattr(file, 'raw_url') else None,
                        'contents_url': file.contents_url if hasattr(file, 'contents_url') else None,
                        'content': content
                    }
                    files.append(file_data)
                    logger.debug(f"Added file {file.filename} to analysis queue")
                except Exception as e:
                    logger.error(f"Error processing file {file.filename}: {str(e)}")
                    continue
                
            logger.info(f"Successfully fetched {len(files)} files from PR")
            return files
            
        except Exception as e:
            logger.error(f"Failed to fetch PR files: {str(e)}")
            return None
            
    def fetch_pr_comments_sync(self, pr_details: Dict[str, str]) -> Optional[List[Dict]]:
        """Fetch comments from a pull request."""
        try:
            repo_name = f"{pr_details['owner']}/{pr_details['repo']}"
            repo = self.github.get_repo(repo_name)
            pr_number = int(pr_details['number'])
            pr = repo.get_pull(pr_number)
            
            comments = []
            for comment in pr.get_comments():
                comment_data = {
                    'id': comment.id,
                    'user': comment.user.login,
                    'body': comment.body,
                    'created_at': comment.created_at.isoformat(),
                    'updated_at': comment.updated_at.isoformat(),
                    'path': comment.path if hasattr(comment, 'path') else None,
                    'position': comment.position if hasattr(comment, 'position') else None
                }
                comments.append(comment_data)
                
            return comments
            
        except Exception as e:
            logger.error(f"Failed to fetch PR comments: {str(e)}")
            return None

    def get_file_content(self, repo_name: str, file_path: str, ref: str) -> Optional[str]:
        """Get file content from GitHub repository"""
        try:
            owner, repo = repo_name.split('/')
            repo_obj = self.github.get_repo(repo_name)
            content = repo_obj.get_contents(file_path, ref=ref)
            return content.decoded_content.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to get file content: {str(e)}")
            return None

    def get_pr_info(self, pr_url: str) -> Optional[Dict]:
        """Get PR information from GitHub."""
        try:
            pr_details = self._parse_pr_url(pr_url)
            if not pr_details:
                logger.error(f"Invalid PR URL format: {pr_url}")
                return None
                
            # Get PR data
            pr_data = self.fetch_pr_data(pr_details)
            if not pr_data:
                logger.error("Failed to fetch PR data")
                return None
                
            # Get files
            files = self.fetch_pr_files_sync(pr_details)
            if not files:
                logger.error("Failed to fetch PR files")
                return None
                
            # Add files to PR data
            pr_data['files'] = files
            pr_data['changed_files'] = len(files)
            
            return pr_data
            
        except Exception as e:
            logger.error(f"Error getting PR info: {str(e)}")
            return None
            
    def _parse_pr_url(self, pr_url: str) -> Optional[Dict[str, str]]:
        """Parse GitHub PR URL into components."""
        try:
            # Parse URL pattern: https://github.com/owner/repo/pull/number
            pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
            match = re.match(pattern, pr_url)
            
            if not match:
                return None
                
            return {
                'owner': match.group(1),
                'repo': match.group(2),
                'number': match.group(3)
            }
            
        except Exception as e:
            logger.error(f"Error parsing PR URL: {str(e)}")
            return None