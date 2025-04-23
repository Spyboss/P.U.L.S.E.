"""
Unit tests for the error monitoring system
"""

import unittest
import os
import json
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

from utils.error_monitoring import (
    log_error,
    get_error_stats,
    get_recent_errors,
    analyze_error_trends,
    clear_error_store,
    export_errors,
    import_errors,
    from_integration_error,
    ErrorSeverity
)


class TestErrorMonitoring(unittest.TestCase):
    """Test cases for the error monitoring system"""

    def setUp(self):
        """Set up test fixtures"""
        # Clear the error store before each test
        clear_error_store()

    def test_log_error(self):
        """Test logging an error"""
        # Create a test error
        error = ValueError("Test error")
        context = {"param1": "value1", "param2": 123}
        
        # Log the error
        error_record = log_error(
            error=error,
            context=context,
            source="test",
            operation="test_operation",
            severity=ErrorSeverity.ERROR
        )
        
        # Check the error record
        self.assertEqual(error_record["error_type"], "ValueError")
        self.assertEqual(error_record["error_message"], "Test error")
        self.assertEqual(error_record["source"], "test")
        self.assertEqual(error_record["operation"], "test_operation")
        self.assertEqual(error_record["severity"], ErrorSeverity.ERROR)
        self.assertEqual(error_record["context"], context)
        
        # Check that the error was stored
        stats = get_error_stats()
        self.assertEqual(stats["total_errors"], 1)
        self.assertEqual(stats["errors_by_source"]["test"], 1)
        self.assertEqual(stats["errors_by_type"]["ValueError"], 1)

    def test_get_error_stats(self):
        """Test getting error statistics"""
        # Log some test errors
        log_error(ValueError("Error 1"), {}, "source1", "op1", ErrorSeverity.ERROR)
        log_error(TypeError("Error 2"), {}, "source1", "op2", ErrorSeverity.WARNING)
        log_error(RuntimeError("Error 3"), {}, "source2", "op1", ErrorSeverity.CRITICAL)
        
        # Get the stats
        stats = get_error_stats()
        
        # Check the stats
        self.assertEqual(stats["total_errors"], 3)
        self.assertEqual(stats["errors_by_source"]["source1"], 2)
        self.assertEqual(stats["errors_by_source"]["source2"], 1)
        self.assertEqual(stats["errors_by_type"]["ValueError"], 1)
        self.assertEqual(stats["errors_by_type"]["TypeError"], 1)
        self.assertEqual(stats["errors_by_type"]["RuntimeError"], 1)
        self.assertEqual(stats["errors_by_severity"][ErrorSeverity.ERROR], 1)
        self.assertEqual(stats["errors_by_severity"][ErrorSeverity.WARNING], 1)
        self.assertEqual(stats["errors_by_severity"][ErrorSeverity.CRITICAL], 1)

    def test_get_recent_errors(self):
        """Test getting recent errors"""
        # Log some test errors
        log_error(ValueError("Error 1"), {}, "source1", "op1", ErrorSeverity.ERROR)
        log_error(TypeError("Error 2"), {}, "source1", "op2", ErrorSeverity.WARNING)
        log_error(RuntimeError("Error 3"), {}, "source2", "op1", ErrorSeverity.CRITICAL)
        
        # Get recent errors
        recent = get_recent_errors(limit=2)
        
        # Check the recent errors
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["error_type"], "RuntimeError")
        self.assertEqual(recent[1]["error_type"], "TypeError")
        
        # Test filtering
        source1_errors = get_recent_errors(source="source1")
        self.assertEqual(len(source1_errors), 2)
        self.assertEqual(source1_errors[0]["source"], "source1")
        self.assertEqual(source1_errors[1]["source"], "source1")
        
        warning_errors = get_recent_errors(severity=ErrorSeverity.WARNING)
        self.assertEqual(len(warning_errors), 1)
        self.assertEqual(warning_errors[0]["severity"], ErrorSeverity.WARNING)

    def test_analyze_error_trends(self):
        """Test analyzing error trends"""
        # Log some test errors
        log_error(ValueError("Error 1"), {}, "source1", "op1", ErrorSeverity.ERROR)
        log_error(TypeError("Error 2"), {}, "source1", "op2", ErrorSeverity.WARNING)
        log_error(RuntimeError("Error 3"), {}, "source2", "op1", ErrorSeverity.CRITICAL)
        
        # Analyze trends
        trends = analyze_error_trends()
        
        # Check the trends
        self.assertIn("errors_by_hour", trends)
        self.assertIn("trend", trends)
        self.assertIn("error_type_trends", trends)
        
        # Should have one hour with 3 errors
        hours = trends["errors_by_hour"]
        self.assertEqual(len(hours), 1)
        self.assertEqual(list(hours.values())[0], 3)

    def test_export_import_errors(self):
        """Test exporting and importing errors"""
        # Log some test errors
        log_error(ValueError("Error 1"), {}, "source1", "op1", ErrorSeverity.ERROR)
        log_error(TypeError("Error 2"), {}, "source1", "op2", ErrorSeverity.WARNING)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_path = temp.name
        
        try:
            # Export errors
            self.assertTrue(export_errors(temp_path))
            
            # Clear the error store
            clear_error_store()
            self.assertEqual(get_error_stats()["total_errors"], 0)
            
            # Import errors
            self.assertTrue(import_errors(temp_path))
            
            # Check that the errors were imported
            stats = get_error_stats()
            self.assertEqual(stats["total_errors"], 2)
            self.assertEqual(stats["errors_by_type"]["ValueError"], 1)
            self.assertEqual(stats["errors_by_type"]["TypeError"], 1)
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_from_integration_error(self):
        """Test creating an error record from an integration error"""
        # Create a test integration error
        integration_error = {
            "success": False,
            "error_type": "github_error",
            "message": "API rate limit exceeded",
            "status_code": 403,
            "user_message": "GitHub API rate limit exceeded. Please try again later."
        }
        
        # Create an error record
        error_record = from_integration_error(
            error_dict=integration_error,
            source="github",
            operation="get_repo_info",
            context={"repo": "user/repo"}
        )
        
        # Check the error record
        self.assertEqual(error_record["source"], "github")
        self.assertEqual(error_record["operation"], "get_repo_info")
        self.assertEqual(error_record["error_message"], "API rate limit exceeded")
        self.assertEqual(error_record["context"]["repo"], "user/repo")
        self.assertEqual(error_record["context"]["integration_error"], integration_error)
        
        # Check that the error was stored
        stats = get_error_stats()
        self.assertEqual(stats["total_errors"], 1)
        self.assertEqual(stats["errors_by_source"]["github"], 1)

    @patch('structlog.get_logger')
    def test_notification(self, mock_get_logger):
        """Test error notification"""
        # Set up the mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Log a critical error with notification
        log_error(
            error=RuntimeError("Critical error"),
            context={},
            source="test",
            operation="critical_operation",
            severity=ErrorSeverity.CRITICAL,
            notify=True
        )
        
        # Check that the logger was called for the notification
        mock_logger.info.assert_called_with(
            "Would send notification for error: test_", 
            mock_logger.info.call_args[0][0].split("_")[1:]
        )


if __name__ == '__main__':
    unittest.main()
