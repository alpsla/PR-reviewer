import os
import logging
from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify
from database import db
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

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pr_review_assistant_secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reviews.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Import models after db initialization to avoid circular imports
from models import Review

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
        
        review_data = claude_service.analyze_pr(context)
        
        # Store review data in session for save/comment actions
        session['pr_details'] = pr_details
        session['review_data'] = review_data
        session['pr_url'] = pr_url
        
        # Log mock review usage
        if review_data.get('is_mock', False):
            logger.warning(f"Using mock review. Reason: {review_data.get('mock_reason', 'unknown')}")
            flash('Using automated review service fallback. Some features may be limited.', 'warning')
        
        return render_template('review.html', 
            review=review_data, 
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

@app.route('/save-review', methods=['POST'])
def save_review():
    try:
        if not session.get('review_data') or not session.get('pr_url'):
            raise ValueError("No review data found in session")
            
        review_data = session['review_data']
        pr_url = session['pr_url']
        
        # Create new review record
        review = Review(
            pr_url=pr_url,
            review_content=review_data['summary'],
            is_mock=review_data.get('is_mock', False),
            mock_reason=review_data.get('mock_reason'),
            structured=review_data.get('structured', True)
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Store review ID in session for comment linking
        session['saved_review_id'] = review.id
        
        logger.info(f"Review saved successfully for PR: {pr_url}")
        return jsonify({'message': 'Review saved successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error saving review: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/post-comment', methods=['POST'])
def post_comment():
    try:
        if not session.get('review_data') or not session.get('pr_details'):
            raise ValueError("No review data found in session")
            
        review_data = session['review_data']
        pr_details = session['pr_details']
        
        # Post comment to GitHub
        comment_result = github_service.post_pr_comment(
            pr_details,
            review_data['summary']
        )
        
        # Update review record if exists
        if session.get('saved_review_id'):
            review = Review.query.get(session['saved_review_id'])
            if review:
                review.github_comment_id = comment_result['id']
                db.session.commit()
        
        logger.info(f"Comment posted successfully to PR: {pr_details}")
        return jsonify({
            'message': 'Comment posted successfully',
            'comment_url': comment_result['url']
        }), 200
        
    except Exception as e:
        logger.error(f"Error posting comment: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Create database tables
with app.app_context():
    db.create_all()
