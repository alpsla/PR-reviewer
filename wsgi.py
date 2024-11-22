import logging
import sys
import os
from urllib.parse import urlparse
from sqlalchemy import text
from flask import Flask, request, render_template, jsonify, redirect, url_for
from flask_cors import CORS
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Create Flask instance
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates')

# Enable CORS
CORS(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Export the application instance
application = app

def verify_environment():
    """Verify required environment variables"""
    required_vars = ['DATABASE_URL', 'GITHUB_TOKEN', 'CLAUDE_API_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
        
    logger.info("Environment verification completed successfully")
    return True

def test_database_connection():
    """Test database connection"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.exc import SQLAlchemyError
        
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is not set")
            
        # Parse the URL to handle any special characters
        parsed = urlparse(db_url)
        if parsed.scheme == "postgres":
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
            conn.commit()
            
        logger.info("Database connection test successful")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error testing database connection: {str(e)}")
        return False

def test_service_initialization():
    """Test service initialization"""
    try:
        from services.github_service import GitHubService
        from services.claude_service import ClaudeService
        
        github_token = os.environ.get('GITHUB_TOKEN')
        claude_api_key = os.environ.get('CLAUDE_API_KEY')
        
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        if not claude_api_key:
            raise ValueError("CLAUDE_API_KEY environment variable is not set")
        
        github_service = GitHubService(github_token)
        claude_service = ClaudeService(claude_api_key)
        
        if github_service and claude_service:
            logger.info("Service initialization test successful")
            return True
        return False
    except Exception as e:
        logger.error(f"Service initialization test failed: {str(e)}")
        return False

def on_starting(server):
    """Log when Gunicorn starts"""
    logger.info("=== Starting PR Review Assistant ===")
    logger.info("Verifying startup requirements...")
    
    if not verify_environment():
        logger.error("Environment verification failed")
        sys.exit(1)
        
    if not test_database_connection():
        logger.error("Database connection test failed")
        sys.exit(1)
        
    if not test_service_initialization():
        logger.error("Service initialization test failed")
        sys.exit(1)
        
    logger.info("All startup checks passed successfully")
    logger.info(f"Server Configuration:")
    logger.info(f"- Workers: {server.cfg.workers}")
    logger.info(f"- Worker Class: {server.cfg.worker_class}")
    logger.info(f"- Bind: {server.cfg.bind}")
    logger.info(f"- Timeout: {server.cfg.timeout}")
    logger.info(f"- Environment: {os.environ.get('FLASK_ENV', 'production')}")

def on_reload(server):
    """Log when Gunicorn reloads"""
    logger.info("=== Reloading PR Review Assistant ===")
    logger.info("Verifying reload requirements...")
    verify_environment()
    test_database_connection()
    test_service_initialization()

def post_worker_init(worker):
    """Log when a worker starts"""
    logger.info(f"Worker {worker.pid} initialized and ready")
    logger.info(f"Worker configuration:")
    logger.info(f"- PID: {worker.pid}")
    logger.info(f"- App: {worker.app}")
    logger.info(f"- Timeout: {worker.timeout}")

def worker_exit(server, worker):
    """Log when a worker exits"""
    logger.info(f"Worker {worker.pid} exiting...")
    logger.info(f"Exit status: {worker.exitcode}")

def pre_request(worker, req):
    """Log before processing each request"""
    logger.info(f"Processing request: {req.path} [{req.method}]")

def post_request(worker, req, environ, resp):
    """Log after processing each request"""
    logger.info(f"Completed request: {req.path} [{req.method}] - Status: {resp.status}")

class HealthLoggingMiddleware:
    """Middleware to log health check requests"""
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path == '/health':
            logger.info("Processing health check request")
            
        response = self.app(environ, start_response)
        
        if path == '/health':
            logger.info("Completed health check request")
            
        return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Startup event handler for FastAPI"""
    try:
        logger.info("=== Starting PR Review Assistant ===")
        
        if not verify_environment():
            raise RuntimeError("Environment verification failed")
            
        if not test_database_connection():
            raise RuntimeError("Database connection test failed")
            
        if not test_service_initialization():
            raise RuntimeError("Service initialization test failed")
            
        logger.info("All startup checks passed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

@app.route("/")
def index():
    """Home page"""
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        return render_template(
            "index.html",
            error="GitHub token is not configured. Some features may be limited."
        )
    return render_template("index.html")

@app.route("/review", methods=["POST"])
def review():
    """Review PR"""
    try:
        # Parse PR URL
        from utils.pr_parser import parse_pr_url
        pr_details = parse_pr_url(pr_url)
        if not pr_details:
            logger.error("Invalid PR URL format")
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "error": "Invalid PR URL format"}
            )

        # Initialize services
        github_token = os.environ.get("GITHUB_TOKEN")
        claude_api_key = os.environ.get("CLAUDE_API_KEY")

        if not github_token or not claude_api_key:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "error": "Missing API credentials"}
            )

        from services.github_service import GitHubService
        from services.claude_service import ClaudeService
        
        github_service = GitHubService(github_token)
        claude_service = ClaudeService(claude_api_key)

        # Fetch PR data
        pr_data = github_service.fetch_pr_data(pr_details)
        files = await github_service.fetch_pr_files(pr_details)
        comments = await github_service.fetch_pr_comments(pr_details)
        
        # Convert files and comments content for analysis
        for file in files:
            try:
                file['content'] = file.get('patch', '')  # Use patch as content for analysis
            except Exception as e:
                logger.error(f"Error processing file content: {str(e)}")
                file['content'] = ''

        # Initialize services
        from services.code_structure_service import CodeStructureService
        from plugins.documentation_parser import DocumentationParser
        
        code_structure_service = CodeStructureService()
        doc_parser = DocumentationParser()
        doc_parser.initialize()

        # Analyze code structure and documentation
        structure_analysis = {}
        for file in files:
            try:
                analysis = code_structure_service.analyze_code(
                    file.get('content', ''),
                    file['filename']
                )
                structure_analysis[file['filename']] = {
                    'structures': analysis.structures,
                    'imports': analysis.imports,
                    'total_complexity': analysis.total_complexity
                }
            except Exception as e:
                logger.error(f"Error analyzing {file['filename']}: {str(e)}")

        # Prepare context for Claude analysis
        # Parse documentation
        doc_analysis = await doc_parser.execute({
            'files': [{'filename': f['filename'], 'content': f.get('content', '')} for f in files]
        })

        context = {
            'pr_data': pr_data,
            'files': files,
            'comments': comments,
            'structure_analysis': structure_analysis,
            'documentation_analysis': doc_analysis
        }
        
        review_data = await claude_service.analyze_pr(context)

        return templates.TemplateResponse(
            "review.html",
            {
                "request": request,
                "review": review_data,
                "pr_url": pr_url,
                "current_time": datetime.utcnow()
            }
        )

    except Exception as e:
        logger.error(f"Error processing review: {str(e)}")
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": str(e)}
        )

@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        from database import db
        with db.session() as session:
            session.execute(text('SELECT 1'))
        return JSONResponse({"status": "healthy", "message": "Service is running"})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            {"status": "unhealthy", "message": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("wsgi:app", host="0.0.0.0", port=port, reload=True)
