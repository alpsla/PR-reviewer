import logging
from logging_config import setup_logging, get_logger

def test_logging():
    # Set up logging for the test component with debug level
    setup_logging(component="test", log_level=logging.DEBUG, log_to_console=True)
    
    # Get a logger instance
    logger = get_logger(__name__, component="test")
    
    # Log some test messages
    print("Logging test messages...")
    
    logger.info("This is a test info message")
    print("Info message logged")
    
    logger.error("This is a test error message", exc_info=True)
    print("Error message logged")
    
    logger.debug("This is a test debug message")
    print("Debug message logged")
    
    logger.warning("This is a test warning message")
    print("Warning message logged")
    
    # Print logger configuration
    print("\nLogger configuration:")
    print(f"Logger name: {logger.logger.name}")
    print(f"Logger level: {logger.logger.level}")
    print(f"Logger handlers: {len(logger.logger.handlers)}")
    for i, handler in enumerate(logger.logger.handlers):
        print(f"\nHandler {i + 1}:")
        print(f"  Type: {type(handler).__name__}")
        print(f"  Level: {handler.level}")
        print(f"  Formatter: {type(handler.formatter).__name__}")
        if isinstance(handler, logging.FileHandler):
            print(f"  Filename: {handler.baseFilename}")

if __name__ == "__main__":
    test_logging()
