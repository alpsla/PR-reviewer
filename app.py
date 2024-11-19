import os
import logging
from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from database import db
from services.github_service import GitHubService
from services.claude_service import ClaudeService
from utils.pr_parser import parse_pr_url
from datetime import datetime
from typing import Optional
import jwt
from urllib.parse import urlparse
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verify_github_token(token: Optional[str]) -> tuple[bool, str]:
    """Verify GitHub token permissions with detailed feedback"""
    if not token:
        return False, "GitHub token not found in environment variables"
    
    try:
        # Initialize service to test token
        github_service = GitHubService(token)
        if github_service.token_valid:
            return True, "Token verified successfully"
        return False, "Token validation failed"
    except Exception as e:
        return False, f"Unexpected error validating token: {str(e)}"

def create_app():
    # Initialize Flask app
    app = Flask(__name__)
    CORS(app)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pr_review_assistant_secret")

    # Configure PostgreSQL database
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable is not set")
        raise ValueError("DATABASE_URL environment variable is required")

    try:
        # Parse the URL to handle any special characters
        parsed = urlparse(db_url)
        if parsed.scheme == "postgres":
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "connect_args": {
                "connect_timeout": 10
            }
        }

        # Initialize database
        logger.info("Initializing database connection...")
        db.init_app(app)
        
        from models import Review
        
        with app.app_context():
            try:
                db.create_all()
                db.session.execute(text('SELECT 1'))
                db.session.commit()
                logger.info("Database tables created/verified successfully")
            except Exception as e:
                logger.error(f"Failed to create/verify database tables: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

    # Initialize services
    github_token: Optional[str] = os.environ.get("GITHUB_TOKEN")
    claude_api_key: Optional[str] = os.environ.get("CLAUDE_API_KEY")

    if not github_token:
        logger.warning("GitHub token not found in environment variables")
    else:
        token_valid, token_message = verify_github_token(github_token)
        if not token_valid:
            logger.warning(f"GitHub token validation failed: {token_message}")
        else:
            logger.info("GitHub token validated successfully")

    if not claude_api_key:
        logger.warning("Claude API key not found in environment variables")

    # Initialize services without failing startup
    try:
        github_service = GitHubService(github_token if github_token else "")
        claude_service = ClaudeService(claude_api_key if claude_api_key else "")
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
        github_service = None
        claude_service = None

    @app.route('/', methods=['GET'])
    def index():
        # Show warning if GitHub token is not configured
        if not github_token:
            flash('GitHub token is not configured. Some features may be limited.', 'warning')
        elif github_service and not github_service.token_valid:
            flash('GitHub token validation failed. Some features may be limited.', 'warning')
        return render_template('index.html')

    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        try:
            # Test database connection
            with db.session.begin():
                db.session.execute(text('SELECT 1'))
            return jsonify({"status": "healthy", "message": "Service is running"}), 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({"status": "unhealthy", "message": str(e)}), 500

    @app.route('/review', methods=['GET', 'POST'])
    def review():
        if request.method == 'GET':
            return redirect(url_for('index'))
            
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

            # Verify GitHub token before proceeding
            if not github_token:
                flash('GitHub token is not configured. Please check environment variables.', 'error')
                return redirect(url_for('index'))
            
            token_valid, token_message = verify_github_token(github_token)
            if not token_valid:
                flash(f'GitHub token validation failed: {token_message}', 'error')
                return redirect(url_for('index'))

            # Fetch PR data
            try:
                logger.info("Fetching PR data from GitHub")
                pr_data = github_service.fetch_pr_data(pr_details)
            except ValueError as e:
                flash(f'Error accessing PR: {str(e)}', 'error')
                return redirect(url_for('index'))
            
            # Analyze with Claude
            logger.info("Analyzing PR with Claude")
            try:
                context = {
                    'pr_data': pr_data,
                    'files': github_service.fetch_pr_files(pr_details),
                    'comments': github_service.fetch_pr_comments(pr_details)
                }
                
                review_data = claude_service.analyze_pr(context)
            except ValueError as e:
                flash(f'Error analyzing PR: {str(e)}', 'error')
                return redirect(url_for('index'))
            
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

    @app.route('/save-review', methods=['POST', 'OPTIONS'])
    def save_review():
        if request.method == 'OPTIONS':
            return '', 204
            
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

    @app.route('/post-comment', methods=['POST', 'OPTIONS'])
    def post_comment():
        if request.method == 'OPTIONS':
            return '', 204
            
        try:
            if not session.get('review_data') or not session.get('pr_details'):
                raise ValueError("No review data found in session")
                
            # Verify GitHub token before posting comment
            token_valid, token_message = verify_github_token(github_token)
            if not token_valid:
                raise ValueError(f"GitHub token validation failed: {token_message}")
                
            review_data = session['review_data']
            pr_details = session['pr_details']
            
            try:
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
                
            except ValueError as e:
                logger.error(f"Failed to post comment: {str(e)}")
                return jsonify({'error': str(e)}), 403
                
        except Exception as e:
            logger.error(f"Error posting comment: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify(error=str(e)), 405

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Using default Flask port 5000
    app.run(host="0.0.0.0", port=port, debug=True)