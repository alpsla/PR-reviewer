import unittest
import os
import logging
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, call, PropertyMock
import tempfile
import shutil
from logging_config import (
    DatabaseHandler,
    RateLimitFilter,
    RequestContextFilter,
    setup_logging,
    get_log_path,
    cleanup_old_logs
)

class TestDatabaseHandler(unittest.TestCase):
    def setUp(self):
        self.handler = DatabaseHandler(max_records=1000, rotation_size=100)
        self.mock_db = MagicMock()
    
    def test_buffer_management(self):
        """Test that records are buffered and flushed correctly"""
        with patch.object(self.handler, 'flush') as mock_flush:
            # Add records up to buffer size
            for i in range(self.handler.buffer_size):
                record = logging.LogRecord(
                    'test', logging.INFO, 'pathname', 1,
                    f'test message {i}', (), None
                )
                self.handler.emit(record)
            
            # Check buffer was flushed when full
            mock_flush.assert_called_once()
            
            # Manually clear buffer as we mocked flush
            self.handler.buffer = []
            self.assertEqual(len(self.handler.buffer), 0)
    
    def test_rotation_trigger(self):
        """Test that rotation is triggered when max_records is reached"""
        with patch.object(self.handler, '_rotate_records') as mock_rotate:
            # Add records up to max_records
            for i in range(self.handler.max_records + 1):
                record = logging.LogRecord(
                    'test', logging.INFO, 'pathname', 1,
                    f'test message {i}', (), None
                )
                self.handler.emit(record)
                
            # Check rotation was triggered
            mock_rotate.assert_called_once()

    def test_rotation_size_calculation(self):
        """Test that rotation size is calculated correctly"""
        self.handler.current_record_count = 1200  # Above max_records (1000)
        
        with patch.object(self.handler, 'flush'):
            self.handler._rotate_records()
            # Should delete rotation_size (100) records
            self.assertEqual(self.handler.current_record_count, 1100)

    def test_error_handling(self):
        """Test error handling in emit and flush methods"""
        # Test emit error handling
        record = logging.LogRecord(
            'test', logging.INFO, 'pathname', 1,
            'test message', (), None
        )
        
        # Test emit error handling
        with patch('sys.stderr') as mock_stderr:
            with patch.object(self.handler, 'format', side_effect=Exception('Test error')):
                try:
                    self.handler.emit(record)
                except Exception:
                    pass  # Expected to raise
                mock_stderr.write.assert_called_with('Error in DatabaseHandler: Test error\n')

        # Test flush error handling
        # Fill the buffer
        self.handler.buffer = [{'test': 'data'}]
        
        # Mock database operation to raise an error
        def mock_db_operation(*args, **kwargs):
            raise Exception('DB error')
        
        with patch('sys.stderr') as mock_stderr:
            with patch.object(self.handler, '_db_insert', side_effect=mock_db_operation):
                try:
                    self.handler.flush()
                except Exception:
                    pass  # Expected to raise
                
                # Verify the exact error message format
                mock_stderr.write.assert_called_with('Error flushing logs to database: DB error\n')

    def test_record_count_accuracy(self):
        """Test that record counting is accurate"""
        initial_count = self.handler.get_record_count()
        
        # Add some records
        for i in range(5):
            record = logging.LogRecord(
                'test', logging.INFO, 'pathname', 1,
                f'test message {i}', (), None
            )
            self.handler.emit(record)
        
        # Check count increased correctly
        self.assertEqual(self.handler.get_record_count(), initial_count + 5)

class TestRateLimitFilter(unittest.TestCase):
    def setUp(self):
        self.filter = RateLimitFilter(rate_limit=5, per_seconds=1)
    
    def test_rate_limiting(self):
        """Test that logs are rate limited correctly"""
        record = logging.LogRecord(
            'test', logging.INFO, 'pathname', 1,
            'test message', (), None
        )
        
        # First 5 logs should pass
        for _ in range(5):
            self.assertTrue(self.filter.filter(record))
        
        # 6th log should be blocked
        self.assertFalse(self.filter.filter(record))
        
        # After waiting, should accept logs again
        time.sleep(1.1)  # Wait for rate limit window to pass
        self.assertTrue(self.filter.filter(record))
    
    def test_per_level_limiting(self):
        """Test that rate limits are tracked per log level"""
        info_record = logging.LogRecord(
            'test', logging.INFO, 'pathname', 1,
            'info message', (), None
        )
        error_record = logging.LogRecord(
            'test', logging.ERROR, 'pathname', 1,
            'error message', (), None
        )
        
        # Use up INFO quota
        for _ in range(5):
            self.assertTrue(self.filter.filter(info_record))
        self.assertFalse(self.filter.filter(info_record))
        
        # ERROR should still work
        self.assertTrue(self.filter.filter(error_record))

    def test_window_reset(self):
        """Test that rate limit window resets correctly"""
        record = logging.LogRecord(
            'test', logging.INFO, 'pathname', 1,
            'test message', (), None
        )
        
        # Use up the quota
        for _ in range(5):
            self.assertTrue(self.filter.filter(record))
        self.assertFalse(self.filter.filter(record))
        
        # Manually reset the window
        self.filter.last_reset = datetime.utcnow() - timedelta(seconds=2)
        
        # Should work again
        self.assertTrue(self.filter.filter(record))

    def test_zero_rate_limit(self):
        """Test behavior with zero rate limit"""
        filter_zero = RateLimitFilter(rate_limit=0)
        record = logging.LogRecord(
            'test', logging.INFO, 'pathname', 1,
            'test message', (), None
        )
        
        # Should always block
        self.assertFalse(filter_zero.filter(record))

class TestLoggingSetup(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
    
    def test_log_file_creation(self):
        """Test that log files are created with correct handlers"""
        component = "test_component"
        setup_logging(
            component=component,
            log_level=logging.INFO,
            max_bytes=1000,
            backup_count=2,
            log_to_console=True,
            log_to_db=False  # Disable DB for this test
        )
        
        logger = logging.getLogger(component)
        logger.info("Test message")
        
        # Check log file exists
        log_path = get_log_path(component)
        self.assertTrue(os.path.exists(log_path))
        
        # Check file contents
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("Test message", content)
    
    def test_log_rotation(self):
        """Test that log files are rotated correctly"""
        component = "test_component"
        max_bytes = 100
        
        setup_logging(
            component=component,
            max_bytes=max_bytes,
            backup_count=2,
            log_to_console=False,
            log_to_db=False
        )
        
        logger = logging.getLogger(component)
        
        # Write enough logs to trigger rotation
        long_message = "x" * 50  # 50 bytes
        for _ in range(4):  # Should create main log + 2 backups
            logger.info(long_message)
        
        log_path = get_log_path(component)
        self.assertTrue(os.path.exists(log_path))
        self.assertTrue(os.path.exists(f"{log_path}.1"))
        self.assertTrue(os.path.exists(f"{log_path}.2"))
        self.assertFalse(os.path.exists(f"{log_path}.3"))  # Shouldn't exist

    def test_multiple_components(self):
        """Test logging with multiple components"""
        components = ["comp1", "comp2", "comp3"]
        
        # Set up logging for each component
        for component in components:
            setup_logging(
                component=component,
                log_level=logging.INFO,
                max_bytes=1000,
                backup_count=1,
                log_to_console=False,
                log_to_db=False
            )
            
            logger = logging.getLogger(component)
            logger.info(f"Test message for {component}")
            
            # Verify log file exists and contains message
            log_path = get_log_path(component)
            self.assertTrue(os.path.exists(log_path))
            with open(log_path, 'r') as f:
                content = f.read()
                self.assertIn(f"Test message for {component}", content)

    def test_log_levels(self):
        """Test that log levels are respected"""
        component = "test_component"
        setup_logging(
            component=component,
            log_level=logging.WARNING,
            log_to_console=False,
            log_to_db=False
        )
        
        logger = logging.getLogger(component)
        log_path = get_log_path(component)
        
        # Info shouldn't be logged
        logger.info("Info message")
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertNotIn("Info message", content)
        
        # Warning should be logged
        logger.warning("Warning message")
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("Warning message", content)

class TestRequestContextFilter(unittest.TestCase):
    def setUp(self):
        self.filter = RequestContextFilter()
        
    def test_request_context_present(self):
        """Test that request context is added to log records when present"""
        # Create a mock request object
        mock_request = MagicMock()
        mock_request.request_id = '123'
        mock_request.user_id = 'user456'
        mock_request.remote_addr = '127.0.0.1'
        mock_request.path = '/test'
        mock_request.method = 'GET'
        
        # Patch both has_request_context and request
        with patch('logging_config.has_request_context', return_value=True):
            with patch('logging_config.request', mock_request):
                record = logging.LogRecord(
                    'test', logging.INFO, 'pathname', 1,
                    'test message', (), None
                )
                
                self.filter.filter(record)
                
                self.assertEqual(record.request_id, '123')
                self.assertEqual(record.user_id, 'user456')
                self.assertEqual(record.ip, '127.0.0.1')
                self.assertEqual(record.path, '/test')
                self.assertEqual(record.method, 'GET')
    
    def test_no_request_context(self):
        """Test behavior when no request context is available"""
        # Patch has_request_context
        with patch('logging_config.has_request_context', return_value=False):
            record = logging.LogRecord(
                'test', logging.INFO, 'pathname', 1,
                'test message', (), None
            )
            
            self.filter.filter(record)
            
            # Should have None values for request context
            self.assertIsNone(record.request_id)
            self.assertIsNone(record.user_id)
            self.assertIsNone(record.ip)
            self.assertIsNone(record.path)
            self.assertIsNone(record.method)

    def test_missing_attributes(self):
        """Test handling of missing request attributes"""
        # Create a mock request object with minimal attributes
        mock_request = MagicMock(spec=['request_id'])
        mock_request.request_id = '123'
        # Explicitly configure the mock to raise AttributeError for missing attributes
        type(mock_request).user_id = PropertyMock(side_effect=AttributeError)
        type(mock_request).remote_addr = PropertyMock(side_effect=AttributeError)
        type(mock_request).path = PropertyMock(side_effect=AttributeError)
        type(mock_request).method = PropertyMock(side_effect=AttributeError)
        
        with patch('logging_config.has_request_context', return_value=True):
            with patch('logging_config.request', mock_request):
                record = logging.LogRecord(
                    'test', logging.INFO, 'pathname', 1,
                    'test message', (), None
                )
                
                self.filter.filter(record)
                
                # Should have the one set attribute
                self.assertEqual(record.request_id, '123')
                # Others should not be set
                self.assertFalse(hasattr(record, 'user_id'))
                self.assertFalse(hasattr(record, 'ip'))
                self.assertFalse(hasattr(record, 'path'))
                self.assertFalse(hasattr(record, 'method'))

if __name__ == '__main__':
    unittest.main()
