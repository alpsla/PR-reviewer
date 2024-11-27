import os
import re
from github import Github
from github.GithubException import GithubException
from dotenv import load_dotenv
import requests

class GitHubService:
    """Service for interacting with GitHub API"""
    
    def __init__(self):
        self.github = None
        self.token = None
        self.token_valid = False
    
    def authenticate(self):
        """Authenticate with GitHub using token from environment variables"""
        try:
            load_dotenv()
            self.token = os.getenv('GITHUB_TOKEN')
            if not self.token:
                print("Error: GITHUB_TOKEN not found in environment variables")
                return False
            
            self.github = Github(self.token)
            
            # Test the token by making a simple API call
            self.github.get_user().login
            self.token_valid = True
            return True
            
        except GithubException as e:
            if e.status == 401:
                print("Error: Invalid GitHub token")
            else:
                print(f"GitHub API error: {str(e)}")
            return False
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return False
    
    def fetch_pr_files(self, owner, repo, pr_url):
        """Fetch files from a PR"""
        try:
            # Extract PR number from URL
            pr_number = int(re.search(r'/pull/(\d+)', pr_url).group(1))
            
            # Get repository
            repo = self.github.get_repo(f"{owner}/{repo}")
            
            # Get PR
            pr = repo.get_pull(pr_number)
            
            # Get files
            files = []
            for file in pr.get_files():
                files.append({
                    'filename': file.filename,
                    'status': file.status,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes,
                    'blob_url': file.blob_url,
                    'raw_url': file.raw_url,
                    'contents_url': file.contents_url,
                    'patch': file.patch if hasattr(file, 'patch') else None
                })
            
            return files
            
        except Exception as e:
            print(f"Error fetching PR files: {str(e)}")
            return []
    
    def get_file_content(self, owner, repo, path, ref=None):
        """Get content of a file from GitHub"""
        try:
            repo = self.github.get_repo(f"{owner}/{repo}")
            try:
                content = repo.get_contents(path, ref=ref)
                if isinstance(content, list):
                    print(f"Warning: {path} is a directory")
                    return None
                return content.decoded_content.decode('utf-8')
            except Exception as e:
                print(f"Error getting file content for {path}: {str(e)}")
                # Try getting the raw content directly
                try:
                    # Get the correct SHA for the ref
                    if ref:
                        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
                    else:
                        # Try to get the default branch
                        try:
                            default_branch = repo.default_branch
                            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{path}"
                        except:
                            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
                    
                    headers = {'Authorization': f'token {self.token}'} if self.token else {}
                    response = requests.get(raw_url, headers=headers)
                    if response.status_code == 200:
                        return response.text
                    else:
                        print(f"Failed to get raw content: {response.status_code}")
                        return None
                except Exception as e:
                    print(f"Error getting raw content: {str(e)}")
                    return None
                
        except Exception as e:
            print(f"Error accessing repository: {str(e)}")
            return None

    def fetch_pr_data(self, pr_details):
        """Fetch PR data including head SHA"""
        try:
            repo = self.github.get_repo(f"{pr_details['owner']}/{pr_details['repo']}")
            pr = repo.get_pull(pr_details['pr_number'])
            return {
                'head': {
                    'sha': pr.head.sha,
                    'ref': pr.head.ref,
                    'repo': pr.head.repo.full_name if pr.head.repo else None
                },
                'base': {
                    'sha': pr.base.sha,
                    'ref': pr.base.ref,
                    'repo': pr.base.repo.full_name
                },
                'number': pr.number,
                'title': pr.title,
                'state': pr.state,
                'merged': pr.merged
            }
        except Exception as e:
            print(f"Error fetching PR data: {str(e)}")
            return None
