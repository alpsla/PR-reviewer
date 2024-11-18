from app import app
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Export the application instance
application = app

if __name__ == "__main__":
    try:
        logger.info("Starting PR Review Assistant application...")
        port = int(os.environ.get("PORT", 5000))
        application.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)
