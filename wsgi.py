from app import app
import logging
import sys
import os
from sqlalchemy import text
from flask import request

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
        with application.app_context():
            from database import db
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False

def test_service_initialization():
    """Test service initialization"""
    try:
        with application.app_context():
            from services.github_service import GitHubService
            from services.claude_service import ClaudeService
            
            github_service = GitHubService(os.environ.get('GITHUB_TOKEN', ''))
            claude_service = ClaudeService(os.environ.get('CLAUDE_API_KEY', ''))
            
            if github_service and claude_service:
                logger.info("Service initialization test successful")
                return True
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

# Wrap application with middleware
application.wsgi_app = HealthLoggingMiddleware(application.wsgi_app)

if __name__ == "__main__":
    try:
        logger.info("=== Starting PR Review Assistant (Development Mode) ===")
        
        if not verify_environment():
            raise RuntimeError("Environment verification failed")
            
        if not test_database_connection():
            raise RuntimeError("Database connection test failed")
            
        if not test_service_initialization():
            raise RuntimeError("Service initialization test failed")
            
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Development server starting on port {port}")
        application.run(host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)
