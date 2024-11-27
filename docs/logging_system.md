# Logging System Documentation

## Overview
The PR Reviewer application implements a comprehensive logging system that provides structured logging across different components. The system is designed to be extensible, maintainable, and consistent across all parts of the application.

## Core Components

### 1. Main Application Logging
The main application logger is configured in `app.py` and provides application-wide logging capabilities:

```python
logger = get_logger(__name__, "main")
logger.set_context(
    app_name="pr_reviewer",
    environment=os.getenv("FLASK_ENV", "development")
)
```

Features:
- Component-based logging with "main" as the root component
- Environment-aware logging (development/production)
- Request context tracking
- Structured log format with timestamps and severity levels

### 2. TypeScript Analyzer Logging
The TypeScript analyzer implements detailed logging for code analysis operations:

```python
logger = get_logger(__name__, "typescript_analyzer")
```

Features:
- Method entry/exit logging
- Error tracking with stack traces
- Analysis metrics logging
- Code pattern detection results

### 3. Framework-Specific Analyzers

#### TypeScript React Analyzer
Dedicated analyzer for React-specific patterns with enhanced logging:

```python
logger = get_logger(__name__, "typescript_react")
```

Features:
- React component analysis logging
- Hook usage tracking
- JSX pattern detection
- Component structure analysis

#### Framework Analyzer Template
Base template for creating new framework analyzers with consistent logging:

```python
class FrameworkAnalyzerTemplate:
    FRAMEWORK_NAME = "framework_name"
    logger = get_logger(__name__, f"typescript_{FRAMEWORK_NAME}")
```

## Log File Structure

### Directory Structure
```
/logs
├── main_YYYYMMDD.log           # Main application logs
├── typescript_YYYYMMDD.log     # TypeScript analyzer logs
├── typescript_react_YYYYMMDD.log   # React analyzer logs
└── [framework]_YYYYMMDD.log    # Framework-specific logs
```

### Log Format
All logs follow a consistent JSON-structured format:
```json
{
    "timestamp": "ISO-8601 timestamp",
    "logger": "component_name",
    "level": "INFO/ERROR/DEBUG",
    "message": "Log message",
    "context": {
        "component": "component_name",
        "method": "method_name",
        "extra_fields": "..."
    }
}
```

## Logging Features

### 1. Structured Context
Each log entry includes contextual information:
- Component name
- Method name
- File path
- Environment details
- User context (when available)

### 2. Error Handling
Enhanced error logging includes:
- Stack traces
- Error context
- Related variables
- Method parameters

### 3. Performance Metrics
Automatic logging of:
- Method execution times
- Analysis completion rates
- Pattern detection statistics

### 4. Security
The logging system implements security best practices:
- No sensitive data logging
- Configurable log levels
- Log rotation
- Rate limiting

## Database Logging

### Database Configuration
```python
DB_LOGGING = {
    'enabled': True,
    'connection_string': 'postgresql://user:password@localhost:5432/logs',
    'table_name': 'application_logs',
    'batch_size': 100,
    'flush_interval': 60  # seconds
}
```

Features:
- Asynchronous database logging
- Batch inserts for better performance
- Automatic table creation and indexing
- Connection pool management

### Log Table Schema
```sql
CREATE TABLE application_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE,
    level VARCHAR(10),
    component VARCHAR(50),
    message TEXT,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Database Retention Policy
- Logs older than 90 days are automatically archived
- Archived logs are moved to partitioned tables by month
- Automated cleanup of archived logs after 1 year

## Log Rotation and Limits

### File Rotation Settings
```python
ROTATION_CONFIG = {
    'max_bytes': 10485760,  # 10MB
    'backup_count': 5,
    'compression': True,
    'compression_method': 'gzip',
    'archive_dir': '/archive/logs'
}
```

### Size Limits
- Individual log file size: 10MB
- Maximum total log size: 1GB per component
- Maximum archive size: 10GB

### Time-based Rotation
- Daily rotation at midnight UTC
- Weekly compression of daily logs
- Monthly archival process

### Rate Limiting
```python
RATE_LIMITS = {
    'max_entries_per_second': 1000,
    'burst_limit': 5000,
    'throttle_interval': 0.1,
    'overflow_strategy': 'drop'
}
```

### Buffer Management
- In-memory buffer size: 1000 entries
- Flush interval: 60 seconds
- Buffer overflow handling: Drop or block

## Performance Optimization

### Batch Processing
- Log entries are batched for database inserts
- Configurable batch size and flush intervals
- Automatic retry mechanism for failed batches

### Caching
```python
CACHE_CONFIG = {
    'enabled': True,
    'max_size': 1000,
    'ttl': 3600,  # 1 hour
    'backend': 'redis'
}
```

### Resource Management
- CPU usage limits for logging operations
- Memory consumption monitoring
- I/O throttling for disk operations

## Monitoring and Alerts

### System Metrics
- Log volume per component
- Error rate tracking
- Storage utilization
- Processing latency

### Alert Thresholds
```python
ALERT_THRESHOLDS = {
    'error_rate': 0.01,  # 1% of total logs
    'disk_usage': 0.85,  # 85% capacity
    'processing_delay': 30  # seconds
}
```

### Health Checks
- Database connectivity
- File system access
- Buffer status
- Rate limit status

## Cleanup and Maintenance

### Automated Tasks
```python
MAINTENANCE_SCHEDULE = {
    'log_rotation': '0 0 * * *',  # Daily at midnight
    'compression': '0 1 * * 0',   # Weekly on Sunday
    'archival': '0 2 1 * *',     # Monthly on 1st
    'cleanup': '0 3 * * *'       # Daily at 3 AM
}
```

### Storage Management
- Automatic detection of low disk space
- Compression of old logs
- Removal of expired archives

### Recovery Procedures
- Automatic recovery from database failures
- Backup log files during maintenance
- Transaction rollback handling

## Usage Examples

### 1. Basic Logging
```python
logger.info("Operation completed", 
            extra={
                "operation": "analyze_file",
                "file_path": file_path
            })
```

### 2. Error Logging
```python
try:
    # Operation
except Exception as e:
    logger.error("Operation failed",
                 extra={
                     "error": str(e),
                     "context": context_data
                 })
```

### 3. Framework Analysis Logging
```python
logger.info("Framework analysis completed",
            extra={
                "framework": "react",
                "metrics": analysis_results
            })
```

## Configuration

### Environment Variables
- `LOG_LEVEL`: Set logging level (DEBUG/INFO/WARNING/ERROR)
- `LOG_FORMAT`: Configure log format
- `LOG_DIR`: Specify log directory

### Log Rotation
- Maximum file size: 10MB
- Backup count: 5
- Daily rotation

## Best Practices

1. **Structured Logging**
   - Always use structured logging with the `extra` parameter
   - Include relevant context in each log entry
   - Use appropriate log levels

2. **Error Handling**
   - Log exceptions with full context
   - Include stack traces for errors
   - Add relevant debugging information

3. **Performance**
   - Use appropriate log levels to avoid performance impact
   - Implement rate limiting for high-volume logs
   - Regular log rotation and cleanup

4. **Security**
   - Never log sensitive information
   - Sanitize user input in logs
   - Follow security best practices for log storage

## Adding New Framework Analyzers

To add a new framework analyzer:

1. Create a new file: `typescript_[framework]_analyzer.py`
2. Inherit from `FrameworkAnalyzerTemplate`
3. Override `FRAMEWORK_NAME`
4. Implement framework-specific patterns
5. Add framework-specific logging

Example:
```python
class TypeScriptAngularAnalyzer(FrameworkAnalyzerTemplate):
    FRAMEWORK_NAME = "angular"
    
    def __init__(self):
        super().__init__()
        self.logger.info("Initializing Angular analyzer",
                        extra={
                            "framework": "angular",
                            "patterns": self.framework_patterns.keys()
                        })
```

## Maintenance

### Log Cleanup
- Automatic cleanup of old logs (30 days retention)
- Compression of rotated logs
- Regular monitoring of log sizes

### Monitoring
- Log level adjustments based on environment
- Error rate monitoring
- Performance impact tracking

## Future Enhancements
1. Elasticsearch integration for log aggregation
2. Kibana dashboards for log visualization
3. Advanced log analysis features
4. Custom log formatters for different environments
