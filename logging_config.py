import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any, Union
import traceback
from flask import has_request_context, request
from contextlib import contextmanager
import threading

# Thread-local storage for request context
_request_context = threading.local()

class DatabaseHandler(logging.Handler):
    """Handler that stores logs in database for user-specific tracking."""
    def __init__(self, max_records: int = 1000000, rotation_size: int = 100000):
        super().__init__()
        self.buffer = []
        self.buffer_size = 100  # Batch size for DB inserts
        self.max_records = max_records
        self.rotation_size = rotation_size  # Number of records to delete during rotation
        self.current_record_count = 0
        
    def emit(self, record):
        """Store the log record in database."""
        try:
            # Check if we've hit the maximum records limit
            if self.current_record_count >= self.max_records:
                self._rotate_records()
            
            # Extract user information from record
            user_id = getattr(record, 'user_id', None)
            if not user_id and hasattr(_request_context, 'user_id'):
                user_id = _request_context.user_id
            
            # Create log entry
            log_entry = {
                'timestamp': datetime.utcnow(),
                'level': record.levelname,
                'message': self.format(record),
                'user_id': user_id,
                'component': record.component if hasattr(record, 'component') else 'main',
                'request_id': getattr(record, 'request_id', None),
                'environment': os.getenv('FLASK_ENV', 'development')
            }
            
            # Add to buffer
            self.buffer.append(log_entry)
            self.current_record_count += 1
            
            # If buffer is full, flush to database
            if len(self.buffer) >= self.buffer_size:
                self.flush()
                
        except Exception as e:
            # Fallback to stderr if database logging fails
            sys.stderr.write(f'Error in DatabaseHandler: {str(e)}\n')
            raise  # Re-raise the exception after logging
    
    def flush(self):
        """Flush buffered logs to database."""
        if not self.buffer:
            return
            
        try:
            # Insert logs into database
            self._db_insert(self.buffer)
            self.buffer = []
        except Exception as e:
            sys.stderr.write(f'Error flushing logs to database: {str(e)}\n')
            raise  # Re-raise the exception after logging
            
    def _db_insert(self, records):
        """Insert records into the database."""
        # TODO: Implement actual database insert
        # Example using SQLAlchemy:
        # from database import db, LogEntry
        # db.session.bulk_insert_mappings(LogEntry, records)
        # db.session.commit()
        pass
    
    def _rotate_records(self):
        """
        Rotate old records out of the database when max_records is reached.
        This implements a FIFO (First In, First Out) rotation policy.
        """
        try:
            # Calculate how many records to delete
            records_to_delete = min(self.rotation_size, 
                                  self.current_record_count - (self.max_records * 0.8))
            
            if records_to_delete <= 0:
                return
                
            # Example using SQLAlchemy:
            # from database import db, LogEntry
            # oldest_records = db.session.query(LogEntry)\
            #     .order_by(LogEntry.timestamp.asc())\
            #     .limit(int(records_to_delete))
            # 
            # for record in oldest_records:
            #     db.session.delete(record)
            # 
            # db.session.commit()
            
            # Update current record count
            self.current_record_count -= int(records_to_delete)
            
            # Log the rotation event
            sys.stderr.write(
                f'Rotated {int(records_to_delete)} old log records. '
                f'Current record count: {self.current_record_count}\n'
            )
            
        except Exception as e:
            sys.stderr.write(f'Error rotating log records: {str(e)}\n')
            
    def get_record_count(self):
        """
        Get the current number of records in the database.
        This should be called periodically to ensure accuracy of current_record_count.
        """
        try:
            # Example using SQLAlchemy:
            # from database import db, LogEntry
            # return db.session.query(LogEntry).count()
            return self.current_record_count
        except Exception as e:
            sys.stderr.write(f'Error getting record count: {str(e)}\n')
            return self.current_record_count

class RequestContextFilter(logging.Filter):
    """Filter that adds request context to log records."""
    def filter(self, record):
        if has_request_context():
            # Only set attributes if they exist in the request object
            if hasattr(request, 'request_id'):
                record.request_id = request.request_id
            if hasattr(request, 'user_id'):
                record.user_id = request.user_id
            if hasattr(request, 'remote_addr'):
                record.ip = request.remote_addr
            if hasattr(request, 'path'):
                record.path = request.path
            if hasattr(request, 'method'):
                record.method = request.method
        else:
            # Get from thread-local storage if available
            record.request_id = getattr(_request_context, 'request_id', None)
            record.user_id = getattr(_request_context, 'user_id', None)
            record.ip = getattr(_request_context, 'ip', None)
            record.path = getattr(_request_context, 'path', None)
            record.method = getattr(_request_context, 'method', None)
        return True

class RateLimitFilter(logging.Filter):
    """Filter that implements rate limiting for logs."""
    def __init__(self, rate_limit: int = 1000, per_seconds: int = 60):
        super().__init__()
        self.rate_limit = rate_limit
        self.per_seconds = per_seconds
        self.counts = {}
        self.last_reset = datetime.utcnow()

    def filter(self, record):
        now = datetime.utcnow()
        # Reset counts if time window has passed
        if (now - self.last_reset).total_seconds() >= self.per_seconds:
            self.counts.clear()
            self.last_reset = now

        # Get counter for this log level
        level_count = self.counts.get(record.levelno, 0)
        if level_count >= self.rate_limit:
            return False
        
        self.counts[record.levelno] = level_count + 1
        return True

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""
    def format(self, record):
        if isinstance(record.msg, str):
            try:
                # Try to parse the message as JSON if it's a string
                record.msg = json.loads(record.msg)
            except json.JSONDecodeError:
                # If it's not JSON, create a basic structured log
                record.msg = {
                    "message": record.msg,
                    "timestamp": datetime.utcnow().isoformat(),
                    "logger": record.name,
                    "level": record.levelname
                }
        return json.dumps(record.msg, default=str)

class StructuredLogger:
    """Enhanced logger with structured logging and user context."""
    def __init__(self, name: str, component: Optional[str] = None):
        self.component = component or "main"
        self.logger = logging.getLogger(self.component)
        self.context: Dict[str, Any] = {"component": self.component}
        
    def set_context(self, **kwargs):
        """Set context information that will be included in all log messages"""
        self.context.update(kwargs)
        
    def _format_message(self, message: str, extra: Optional[Dict[str, Any]] = None) -> str:
        """Format message with context and extra information"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "logger": self.logger.name,
            "component": self.component,
            "message": message,
            "context": self.context,
            "environment": os.getenv('FLASK_ENV', 'development')
        }
        
        # Add request context if available
        if has_request_context():
            log_data.update({
                "request_id": getattr(request, 'request_id', None),
                "user_id": getattr(request, 'user_id', None),
                "ip": request.remote_addr,
                "path": request.path,
                "method": request.method
            })
        elif hasattr(_request_context, 'request_id'):
            log_data.update({
                "request_id": _request_context.request_id,
                "user_id": getattr(_request_context, 'user_id', None),
                "ip": getattr(_request_context, 'ip', None),
                "path": getattr(_request_context, 'path', None),
                "method": getattr(_request_context, 'method', None)
            })
            
        if extra:
            log_data["extra"] = extra
        return json.dumps(log_data, default=str)
        
    def info(self, message: str, **kwargs):
        """Log an info message with context"""
        self.logger.info(self._format_message(message, kwargs))
        
    def error(self, message: str, exc_info: bool = True, **kwargs):
        """Log an error message with context and optional exception info"""
        if exc_info and sys.exc_info()[0] is not None:
            kwargs['traceback'] = traceback.format_exc()
        self.logger.error(self._format_message(message, kwargs))
        
    def debug(self, message: str, **kwargs):
        """Log a debug message with context"""
        self.logger.debug(self._format_message(message, kwargs))
        
    def warning(self, message: str, **kwargs):
        """Log a warning message with context"""
        self.logger.warning(self._format_message(message, kwargs))

@contextmanager
def user_context(user_id: str, **kwargs):
    """Context manager for setting user-specific logging context."""
    previous_context = {
        'user_id': getattr(_request_context, 'user_id', None),
        'request_id': getattr(_request_context, 'request_id', None)
    }
    
    # Set new context
    _request_context.user_id = user_id
    for key, value in kwargs.items():
        setattr(_request_context, key, value)
    
    try:
        yield
    finally:
        # Restore previous context
        for key, value in previous_context.items():
            if value is None:
                delattr(_request_context, key)
            else:
                setattr(_request_context, key, value)

def setup_logging(
    component: str = "main",
    log_level: Union[str, int] = logging.INFO,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    log_to_console: bool = True,
    log_to_db: bool = True,
    rate_limit: int = 1000,  # Maximum logs per minute
    db_max_records: int = 1000000,  # Maximum database records
    retention_days: int = 30  # Log retention period
):
    """Set up logging configuration for a specific component."""
    logger = logging.getLogger(component)
    logger.setLevel(log_level)
    
    # Prevent log propagation to avoid duplicate logs
    logger.propagate = False
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Add rate limiting filter
    rate_limiter = RateLimitFilter(rate_limit=rate_limit)
    logger.addFilter(rate_limiter)
    
    # Create JSON formatter
    json_formatter = JsonFormatter()
    
    # Main file handler with rotation
    log_file = get_log_path(component)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(logging.INFO)  # Only INFO and above go to main log
    logger.addHandler(file_handler)
    
    # Error file handler
    error_file = get_log_path(component, "error")
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    error_handler.setFormatter(json_formatter)
    error_handler.setLevel(logging.ERROR)  # Only ERROR and above
    logger.addHandler(error_handler)
    
    # Console handler if enabled
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(json_formatter)
        console_handler.setLevel(logging.DEBUG if log_level == logging.DEBUG else logging.INFO)
        logger.addHandler(console_handler)
    
    # Database handler if enabled
    if log_to_db and os.getenv('FLASK_ENV') != 'testing':
        db_handler = DatabaseHandler(max_records=db_max_records)
        db_handler.setLevel(logging.INFO)
        logger.addHandler(db_handler)
    
    # Add request context filter
    context_filter = RequestContextFilter()
    logger.addFilter(context_filter)
    
    # Schedule cleanup of old logs
    cleanup_old_logs(os.path.dirname(log_file), retention_days)

def get_log_path(component: str, log_type: str = "main") -> str:
    """Get the appropriate log file path based on component and type."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d')
    if log_type == "error":
        return os.path.join(log_dir, f"{component}_error_{timestamp}.log")
    return os.path.join(log_dir, f"{component}_{timestamp}.log")

def get_logger(name: str, component: Optional[str] = None) -> StructuredLogger:
    """Get a structured logger instance for a specific component."""
    # Set up logging for the component if not already set up
    setup_logging(component=component or name)
    return StructuredLogger(name, component)

def cleanup_old_logs(log_dir: str, max_days: int = 30) -> None:
    """Clean up old log files beyond max_days."""
    now = datetime.now()
    for filename in os.listdir(log_dir):
        if not filename.endswith('.log'):
            continue
            
        filepath = os.path.join(log_dir, filename)
        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        if (now - file_time).days > max_days:
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Error removing old log file {filepath}: {e}")

# Example usage:
# with user_context("user123", request_id="req456"):
#     logger = get_logger(__name__, "typescript_analyzer")
#     logger.set_context(
#         pr_url="https://github.com/org/repo/pull/123",
#         language="typescript"
#     )
#     logger.info("Analyzing TypeScript code")
