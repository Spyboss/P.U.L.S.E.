import unittest
import importlib
import sys
import os

class TestCircularImports(unittest.TestCase):
    """Test suite for circular import resolution"""
    
    def test_execution_flow_import(self):
        """Test importing ExecutionFlow without circular dependency errors"""
        # Direct import without any context
        try:
            from utils.execution_flow import ExecutionFlow
            # Create an instance to test initialization
            flow = ExecutionFlow()
            self.assertIsNotNone(flow)
            self.assertTrue(hasattr(flow, 'model_interface'))
        except ImportError as e:
            self.fail(f"Failed to import ExecutionFlow: {e}")
    
    def test_model_interface_import(self):
        """Test importing ModelInterface without circular dependency errors"""
        # Direct import without any context
        try:
            from skills.model_interface import ModelInterface
            # Create an instance to test initialization
            model = ModelInterface()
            self.assertIsNotNone(model)
        except ImportError as e:
            self.fail(f"Failed to import ModelInterface: {e}")
    
    def test_bidirectional_imports(self):
        """Test that both modules can be imported in any order without errors"""
        try:
            # First import model_interface
            import skills.model_interface
            # Then import execution_flow
            import utils.execution_flow
            
            # Reload modules to test the other way around
            importlib.reload(skills.model_interface)
            importlib.reload(utils.execution_flow)
            
            # Try again with different order
            importlib.reload(utils.execution_flow)
            importlib.reload(skills.model_interface)
            
            self.assertTrue(True)  # No exception raised
        except ImportError as e:
            self.fail(f"Circular import still exists: {e}")
    
    def test_lazy_loading_model_interface(self):
        """Test the lazy loading of ModelInterface in ExecutionFlow"""
        try:
            from utils.execution_flow import ExecutionFlow
            flow = ExecutionFlow()
            
            # Access model_interface property but verify _model_interface is None before
            self.assertIsNone(flow._model_interface)
            
            # Access the property which should trigger lazy loading
            interface = flow.model_interface
            
            # Verify it's no longer None
            self.assertIsNotNone(flow._model_interface)
            self.assertIsNotNone(interface)
        except Exception as e:
            self.fail(f"Lazy loading failed: {e}")
    
    def test_get_execution_flow(self):
        """Test the get_execution_flow function in model_interface"""
        try:
            from skills.model_interface import get_execution_flow
            
            # Should be None initially
            from skills.model_interface import _execution_flow
            self.assertIsNone(_execution_flow)
            
            # Get the execution flow
            flow = get_execution_flow()
            
            # Should not be None now
            self.assertIsNotNone(flow)
        except Exception as e:
            self.fail(f"get_execution_flow failed: {e}")

if __name__ == '__main__':
    unittest.main() 