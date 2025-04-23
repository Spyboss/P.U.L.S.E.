import unittest
import gc
import sys
from unittest.mock import patch, MagicMock
from utils.memory_guard import memory_guard

class TestMemoryGuard(unittest.TestCase):
    """Test suite for memory_guard context manager"""

    @patch('utils.memory_guard.gc')
    @patch('utils.memory_guard.psutil.Process')
    def test_memory_guard_below_threshold(self, mock_process, mock_gc):
        """Test that memory_guard doesn't trigger additional GC when below threshold"""
        # Setup mock process with memory usage below threshold
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value.rss = 2 * 1024**3  # 2GB
        mock_process.return_value = mock_process_instance

        # Execute memory_guard with force_gc=False to disable automatic GC
        with memory_guard(force_gc=False):
            pass

        # Verify gc.collect wasn't called
        mock_gc.collect.assert_not_called()

    @patch('utils.memory_guard.gc')
    @patch('utils.memory_guard.psutil.Process')
    def test_memory_guard_above_threshold(self, mock_process, mock_gc):
        """Test that memory_guard triggers GC when above threshold"""
        # Setup mock process with memory usage above threshold
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value.rss = 3.5 * 1024**3  # 3.5GB
        mock_process.return_value = mock_process_instance

        # Execute memory_guard
        with memory_guard():
            pass

        # Verify gc.collect was called
        mock_gc.collect.assert_called()

    @patch('utils.memory_guard.gc')
    @patch('utils.memory_guard.psutil.Process')
    def test_memory_guard_with_exception(self, mock_process, mock_gc):
        """Test that memory_guard triggers GC when an exception occurs within the context"""
        # Setup mock process with memory usage above threshold
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value.rss = 3.5 * 1024**3  # 3.5GB
        mock_process.return_value = mock_process_instance

        # Execute memory_guard with exception
        try:
            with memory_guard():
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Verify gc.collect was called despite the exception
        mock_gc.collect.assert_called()

if __name__ == '__main__':
    unittest.main()