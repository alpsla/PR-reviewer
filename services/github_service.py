from github import Github
from typing import Dict, List

class GitHubService:
    def __init__(self, token: str):
        self.github = Github(token)
    
    def fetch_pr_data(self, pr_details: Dict) -> Dict:
        """Fetches PR data using GitHub API"""
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
        except Exception as e:
            raise Exception(f"Failed to fetch PR data: {str(e)}")
    
    def fetch_pr_files(self, pr_details: Dict) -> List[Dict]:
        """Fetches files changed in the PR"""
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
        except Exception as e:
            raise Exception(f"Failed to fetch PR files: {str(e)}")
    
    def fetch_pr_comments(self, pr_details: Dict) -> List[Dict]:
        """Fetches PR comments"""
        try:
            repo = self.github.get_repo(f"{pr_details['owner']}/{pr_details['repo']}")
            pr = repo.get_pull(pr_details['number'])
            
            return [{
                'user': comment.user.login,
                'body': comment.body,
                'created_at': comment.created_at
            } for comment in pr.get_comments()]
        except Exception as e:
            raise Exception(f"Failed to fetch PR comments: {str(e)}")
