from app import app
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Export the application instance
application = app

def on_starting(server):
    """Log when Gunicorn starts"""
    logger.info("Gunicorn server is starting up...")

def on_reload(server):
    """Log when Gunicorn reloads"""
    logger.info("Reloading Gunicorn workers...")

def post_worker_init(worker):
    """Log when a worker starts"""
    logger.info(f"Gunicorn worker {worker.pid} initialized")

def worker_exit(server, worker):
    """Log when a worker exits"""
    logger.info(f"Gunicorn worker {worker.pid} exited")

if __name__ == "__main__":
    try:
        logger.info("Starting PR Review Assistant application...")
        logger.info("Server configuration:")
        logger.info(f"- Host: 0.0.0.0")
        logger.info(f"- Port: {os.environ.get('PORT', 5000)}")
        logger.info(f"- Debug mode: {os.environ.get('FLASK_DEBUG', 'False')}")
        logger.info(f"- Environment: {os.environ.get('FLASK_ENV', 'production')}")
        port = int(os.environ.get("PORT", 5000))
        application.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)
