import os
import logging
from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from asgiref.sync import sync_to_async
from database import db
from services.github_service import GitHubService
from services.claude_service import ClaudeService
from utils.pr_parser import parse_pr_url
from utils.logging_utils import setup_logging, get_logger
from datetime import datetime
from typing import Optional
import jwt
from urllib.parse import urlparse
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure main application logger
logger = get_logger(__name__, "main")
logger.set_context(
    app_name="pr_reviewer",
    environment=os.getenv("FLASK_ENV", "development")
)

def create_app():
    """Create and configure the Flask application."""
    logger.info("Initializing Flask application", 
                extra={
                    "flask_env": os.getenv("FLASK_ENV", "development"),
                    "debug_mode": os.getenv("FLASK_DEBUG", "True").lower() == "true"
                })
    
    # Initialize Flask app
    app = Flask(__name__)
    CORS(app)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pr_review_assistant_secret")

    # Load configuration
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'development_secret_key')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

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

    try:
        logger.debug(f"GitHub Token present: {'Yes' if github_token else 'No'}")
        logger.debug(f"Claude API Key present: {'Yes' if claude_api_key else 'No'}")
        
        # Initialize GitHub service
        github_service = GitHubService(github_token)
        if not github_service.token_valid:
            logger.error("GitHub token validation failed")
            raise ValueError("GitHub token validation failed")
        logger.info("GitHub token validated successfully")
        
        # Initialize Claude service
        claude_service = ClaudeService(claude_api_key)
        if claude_service.init_error:
            logger.error(f"Claude service initialization failed: {claude_service.init_error}")
            raise ValueError(f"Claude service initialization failed: {claude_service.init_error}")
        logger.info("Claude service initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise

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

    @app.route('/review', methods=['POST'])
    def review():
        """Handle PR review request."""
        try:
            # Validate input
            pr_url = request.form.get('pr_url')
            if not pr_url:
                logger.error("No PR URL provided")
                flash('Please provide a PR URL', 'error')
                return redirect(url_for('index'))

            logger.info(f"Processing review request for PR: {pr_url}")
            
            # Get PR data from GitHub
            try:
                logger.info("Fetching PR data from GitHub")
                pr_info = github_service.get_pr_info(pr_url)
                if not pr_info:
                    logger.error("Failed to fetch PR data from GitHub")
                    flash('Failed to fetch PR data from GitHub', 'error')
                    return redirect(url_for('index'))
            except Exception as e:
                logger.error(f"GitHub API error: {str(e)}")
                flash(f'Error accessing GitHub: {str(e)}', 'error')
                return redirect(url_for('index'))
                
            # Filter TypeScript files and get their content
            try:
                ts_files = []
                repo_name = f"{pr_info['base']['repo']['full_name']}"
                head_sha = pr_info['head']['sha']
                
                for file in pr_info['files']:
                    if not file['filename'].endswith(('.ts', '.tsx')):
                        continue
                        
                    # Get file content
                    try:
                        content = None
                        if file['status'] != 'removed':
                            content = github_service.get_file_content(repo_name, file['filename'], head_sha)
                            if not content and 'raw_url' in file:
                                try:
                                    import requests
                                    response = requests.get(file['raw_url'])
                                    if response.status_code == 200:
                                        content = response.text
                                except Exception as e:
                                    logger.warning(f"Failed to get content from raw_url for {file['filename']}: {str(e)}")
                        
                        file_info = {
                            'filename': file['filename'],
                            'content': content,
                            'status': file['status'],
                            'additions': file.get('additions', 0),
                            'deletions': file.get('deletions', 0),
                            'changes': file.get('changes', 0),
                            'patch': file.get('patch'),
                            'raw_url': file.get('raw_url'),
                            'contents_url': file.get('contents_url')
                        }
                        ts_files.append(file_info)
                        logger.debug(f"Added {file['filename']} to analysis queue with content length: {len(content) if content else 0}")
                    except Exception as e:
                        logger.error(f"Error getting content for {file['filename']}: {str(e)}")
                        continue
                
                if not ts_files:
                    logger.warning("No TypeScript files found in PR")
                    flash('No TypeScript files found in this PR', 'warning')
                    return redirect(url_for('index'))
                    
                logger.info(f"Found {len(ts_files)} TypeScript files to analyze")
                
            except Exception as e:
                logger.error(f"Error processing PR files: {str(e)}")
                flash('Error processing PR files', 'error')
                return redirect(url_for('index'))
                
            # Run TypeScript analysis
            try:
                logger.info("Starting TypeScript analysis")
                from services.code_analysis.analyzers.typescript_analyzer import TypeScriptAnalyzer, AnalysisError
                typescript_analyzer = TypeScriptAnalyzer()
                ts_analysis = typescript_analyzer.analyze_files(ts_files)
            except AnalysisError as e:
                logger.error(f"TypeScript analysis error: {str(e)}")
                flash(f'Analysis error: {str(e)}', 'error')
                return redirect(url_for('index'))
            except Exception as e:
                logger.error(f"Unexpected error in TypeScript analysis: {str(e)}")
                flash('An unexpected error occurred during analysis', 'error')
                return redirect(url_for('index'))
            
            # Convert analysis results
            try:
                analysis_dict = ts_analysis.to_dict()
                analysis_results = {
                    'overall_health': float(analysis_dict['quality_score']),
                    'type_safety': float(analysis_dict['type_analysis']['metrics']['type_coverage']),
                    'documentation': float(analysis_dict['doc_analysis']['metrics']['coverage']),
                    'code_quality': float(analysis_dict['quality_score']),
                    'type_issues': analysis_dict['type_analysis']['examples'],
                    'documentation_issues': analysis_dict['doc_analysis']['issues'],
                    'quality_gates': analysis_dict['quality_gates'],
                    'action_items': analysis_dict['action_items'],
                    'best_practices': analysis_dict['best_practices']
                }
            except Exception as e:
                logger.error(f"Error converting analysis results: {str(e)}")
                analysis_results = {
                    'overall_health': 0.0,
                    'type_safety': 0.0,
                    'documentation': 0.0,
                    'code_quality': 0.0,
                    'type_issues': [],
                    'documentation_issues': [],
                    'quality_gates': [],
                    'action_items': [],
                    'best_practices': {'strong_areas': [], 'needs_improvement': []}
                }
                flash('Error processing analysis results', 'warning')
            
            # Store results in database
            try:
                # Convert analysis results to JSON-serializable format
                review_content = {
                    'analysis': analysis_results,
                    'pr_url': pr_url,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                review = Review(
                    pr_url=pr_url,
                    review_content=str(review_content),
                    structured=True
                )
                db.session.add(review)
                db.session.commit()
                logger.info(f"Saved review for PR: {pr_url}")
            except Exception as e:
                logger.error(f"Database error: {str(e)}", exc_info=True)
                db.session.rollback()
                flash('Error saving analysis results', 'warning')

            # Prepare template variables
            template_vars = {
                'pr_url': pr_url,
                'current_time': datetime.utcnow(),
                'review': {
                    'is_mock': False,
                    'structured': True,
                    'mock_reason': None,
                    'summary': str(analysis_results.get('summary', '')),
                },
                'analysis': {
                    'overall_health': float(analysis_dict.get('quality_score', 0.0)),
                    'type_safety': float(analysis_dict.get('type_analysis', {}).get('metrics', {}).get('type_coverage', 0.0)),
                    'documentation': float(analysis_dict.get('doc_analysis', {}).get('metrics', {}).get('coverage', 0.0)),
                    'code_quality': float(analysis_dict.get('quality_score', 0.0)),
                    'type_issues': analysis_dict.get('type_analysis', {}).get('examples', []),
                    'documentation_issues': analysis_dict.get('doc_analysis', {}).get('issues', []),
                    'quality_gates': analysis_dict.get('quality_gates', []),
                    'action_items': analysis_dict.get('action_items', []),
                    'best_practices': {
                        'strong_areas': analysis_dict.get('best_practices', {}).get('strong_areas', []),
                        'needs_improvement': analysis_dict.get('best_practices', {}).get('needs_improvement', [])
                    }
                }
            }
            
            return render_template('review.html', **template_vars)
        except Exception as e:
            logger.error(f"Template rendering error: {str(e)}", exc_info=True)
            flash('Error displaying results', 'error')
            return redirect(url_for('index'))
            
        except Exception as e:
            logger.error(f"Unexpected error in review route: {str(e)}")
            flash('An unexpected error occurred', 'error')
            return redirect(url_for('index'))

    @app.route('/typescript-analysis', methods=['GET', 'POST'])
    def typescript_analysis():
        if request.method == 'GET':
            return render_template('typescript_report_new.html', analysis_data={})
        
        try:
            data = request.get_json()
            pr_url = data.get('pr_url')
            
            if not pr_url:
                return jsonify({'error': 'PR URL is required'}), 400
            
            # Initialize the analyzer
            from services.code_analysis.analyzers.typescript_analyzer import TypeScriptAnalyzer
            typescript_analyzer = TypeScriptAnalyzer()
            
            # Get PR files and analyze them
            files = typescript_analyzer.get_pr_files(pr_url)
            analysis_results = []
            
            for file_info in files:
                if file_info['filename'].endswith('.ts') or file_info['filename'].endswith('.tsx'):
                    content = file_info.get('content', '')
                    analysis = typescript_analyzer.analyze_file(content, file_info['filename'])
                    analysis_results.append(analysis.to_dict())
            
            # Combine results from multiple files
            combined_analysis = typescript_analyzer.combine_analyses(analysis_results)
            
            # Return the analysis results based on request type
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(combined_analysis)
            
            return render_template('typescript_report_new.html', analysis_data=combined_analysis)
            
        except Exception as e:
            logger.error(f"Error in typescript analysis: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/test-typescript', methods=['GET'])
    def test_typescript():
        """Test route for TypeScript analysis"""
        try:
            # Initialize the analyzer
            from services.code_analysis.analyzers.typescript_analyzer import TypeScriptAnalyzer
            typescript_analyzer = TypeScriptAnalyzer()
            
            # Read the test file
            with open('test_analysis.ts', 'r') as f:
                content = f.read()
            
            # Analyze the file
            analysis = typescript_analyzer.analyze_file(content, 'test_analysis.ts')
            
            # Convert to dict for template
            analysis_data = {
                'type_analysis': analysis.type_analysis.to_dict(),
                'doc_analysis': analysis.doc_analysis.to_dict(),
                'framework_analysis': analysis.framework_analysis.to_dict(),
                'quality_score': analysis.quality_score,
                'quality_gates': [gate.to_dict() for gate in analysis.quality_gates]
            }
            
            # Return the analysis results
            return render_template('typescript_report_new.html', analysis_data=analysis_data)
            
        except Exception as e:
            logger.error(f"Error in test typescript analysis: {str(e)}")
            return jsonify({'error': str(e)}), 500

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
                # Verify GitHub service is available
                if not github_service:
                    raise ValueError("GitHub service not available")
                    
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
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port, debug=True)