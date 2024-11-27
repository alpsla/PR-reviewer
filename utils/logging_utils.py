import os
import logging
import functools
from typing import Optional, Callable
from flask import request
from datetime import datetime

class RequestContextFilter(logging.Filter):
    """Filter that adds request context to log records."""
    def filter(self, record):
        try:
            from flask import request
            if request:
                record.url = getattr(request, 'url', None)
                record.method = getattr(request, 'method', None)
                record.ip = getattr(request, 'remote_addr', None)
                record.request_id = getattr(request, 'request_id', None)
        except RuntimeError:
            # Outside request context
            record.url = None
            record.method = None
            record.ip = None
            record.request_id = None
        return True

def setup_logging(
    app_name: str,
    logs_dir: str,
    log_level: int = logging.DEBUG,
    request_context: bool = True
) -> logging.Logger:
    """
    Set up logging with both file and console handlers.
    
    Args:
        app_name: Name of the application/module
        logs_dir: Directory to store log files
        log_level: Logging level (default: DEBUG)
        request_context: Whether to include request context in logs (default: True)
    
    Returns:
        Logger instance configured with file and console handlers
    """
    # Ensure logs directory exists
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    base_format = '%(asctime)s - %(name)s - %(levelname)s'
    if request_context:
        log_format = f'{base_format} - [%(ip)s %(method)s %(url)s] - %(message)s'
    else:
        log_format = f'{base_format} - %(message)s'
    
    formatter = logging.Formatter(log_format)
    
    # General logs file handler
    general_handler = logging.FileHandler(
        os.path.join(logs_dir, 'pr_reviewer.log')
    )
    general_handler.setLevel(log_level)
    general_handler.setFormatter(formatter)
    
    # Error logs file handler
    error_handler = logging.FileHandler(
        os.path.join(logs_dir, 'pr_reviewer_error.log')
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(general_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    # Add request context filter if needed
    if request_context:
        logger.addFilter(RequestContextFilter())
    
    return logger

def log_function_call(logger: Optional[logging.Logger] = None) -> Callable:
    """
    Decorator to log function calls with parameters and return values.
    
    Args:
        logger: Logger instance to use. If None, will use the module's logger.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get the logger
            log = logger or logging.getLogger(func.__module__)
            
            # Log function call
            func_name = f"{func.__module__}.{func.__qualname__}"
            log.debug(
                f"Calling {func_name} with args={args}, kwargs={kwargs}"
            )
            
            try:
                # Call the function
                start_time = datetime.now()
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                # Log successful completion
                log.debug(
                    f"{func_name} completed in {duration:.2f}s with result={result}"
                )
                return result
                
            except Exception as e:
                # Log error
                log.error(
                    f"Error in {func_name}: {str(e)}",
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator
