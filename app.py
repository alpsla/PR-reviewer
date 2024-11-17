import os
import logging
from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from services.github_service import GitHubService
from services.claude_service import ClaudeService
from utils.pr_parser import parse_pr_url
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pr_review_assistant_secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reviews.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Initialize services with proper type handling
github_token: Optional[str] = os.environ.get("GITHUB_TOKEN")
claude_api_key: Optional[str] = os.environ.get("CLAUDE_API_KEY")

if not github_token:
    logger.warning("GitHub token not found in environment variables")
if not claude_api_key:
    logger.warning("Claude API key not found in environment variables")

github_service = GitHubService(github_token if github_token else "")
claude_service = ClaudeService(claude_api_key if claude_api_key else "")

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/review', methods=['POST'])
def review():
    pr_url = request.form.get('pr_url')
    if not pr_url:
        flash('Please provide a PR URL', 'error')
        return redirect(url_for('index'))
    
    try:
        logger.info(f"Processing review request for PR: {pr_url}")
        
        # Parse PR URL
        pr_details = parse_pr_url(pr_url)
        if not pr_details:
            logger.error("Invalid PR URL format")
            flash('Invalid PR URL format. Please provide a valid GitHub pull request URL.', 'error')
            return redirect(url_for('index'))

        # Fetch PR data
        logger.info("Fetching PR data from GitHub")
        pr_data = github_service.fetch_pr_data(pr_details)
        
        # Analyze with Claude
        logger.info("Analyzing PR with Claude")
        context = {
            'pr_data': pr_data,
            'files': github_service.fetch_pr_files(pr_details),
            'comments': github_service.fetch_pr_comments(pr_details)
        }
        
        review = claude_service.analyze_pr(context)
        
        # Log mock review usage
        if review.get('is_mock', False):
            logger.warning(f"Using mock review. Reason: {review.get('mock_reason', 'unknown')}")
            flash('Using automated review service fallback. Some features may be limited.', 'warning')
        
        return render_template('review.html', 
            review=review, 
            pr_url=pr_url,
            current_time=datetime.utcnow()
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        flash(f'Validation Error: {str(e)}', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Unexpected error during review: {str(e)}")
        flash(f'Error processing PR: {str(e)}', 'error')
        return redirect(url_for('index'))

with app.app_context():
    db.create_all()
