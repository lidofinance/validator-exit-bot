"""Simple unit tests for scripts/generate.py"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

# Add scripts to path
scripts_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

from scripts.generate import AppContext


class TestAppContext:
    """Tests for AppContext class."""
    
    def test_app_context_initialization(self):
        """Test that AppContext initializes with correct parameters."""
        with patch('scripts.generate.KeysAPIClient') as mock_kapi, \
             patch('scripts.generate.CLClient') as mock_cl:
            
            mock_kapi_instance = Mock()
            mock_cl_instance = Mock()
            mock_kapi.return_value = mock_kapi_instance
            mock_cl.return_value = mock_cl_instance
            
            ctx = AppContext(debug=True, kapi_url="http://test-kapi", cl_url="http://test-cl")
            
            assert ctx.debug is True
            assert ctx.kapi == mock_kapi_instance
            assert ctx.cl_client == mock_cl_instance
            mock_kapi.assert_called_once_with("http://test-kapi")
            mock_cl.assert_called_once_with("http://test-cl")
    
    def test_app_context_log_when_debug_enabled(self, capsys):
        """Test that log outputs when debug is enabled."""
        with patch('scripts.generate.KeysAPIClient'), \
             patch('scripts.generate.CLClient'), \
             patch('click.secho') as mock_secho:
            
            ctx = AppContext(debug=True, kapi_url="http://test", cl_url="http://test")
            ctx.log("Test message")
            
            # Verify secho was called with debug message
            calls = [call for call in mock_secho.call_args_list if "Test message" in str(call)]
            assert len(calls) > 0
    
    def test_app_context_log_when_debug_disabled(self):
        """Test that log does not output when debug is disabled."""
        with patch('scripts.generate.KeysAPIClient'), \
             patch('scripts.generate.CLClient'), \
             patch('click.secho') as mock_secho:
            
            ctx = AppContext(debug=False, kapi_url="http://test", cl_url="http://test")
            mock_secho.reset_mock()  # Reset after init calls
            ctx.log("Test message")
            
            # Verify secho was not called for the test message
            calls = [call for call in mock_secho.call_args_list if "Test message" in str(call)]
            assert len(calls) == 0

