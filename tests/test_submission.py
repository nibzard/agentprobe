"""Tests for the submission module."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import json

from agentprobe.submission import DataSanitizer, ResultSubmitter, ResultSubmission
from agentprobe.models import TestResult


class TestDataSanitizer:
    """Test data sanitization functionality."""
    
    def test_sanitize_api_keys(self):
        """Test API key sanitization."""
        text = "Set API_KEY=sk-1234567890 and token: abcdef123456"
        sanitized = DataSanitizer.sanitize_text(text)
        assert "sk-1234567890" not in sanitized
        assert "abcdef123456" not in sanitized
        assert "[REDACTED_KEY]" in sanitized
    
    def test_sanitize_emails(self):
        """Test email sanitization."""
        text = "Contact user@example.com for details"
        sanitized = DataSanitizer.sanitize_text(text)
        assert "user@example.com" not in sanitized
        assert "[REDACTED_EMAIL]" in sanitized
    
    def test_sanitize_ip_addresses(self):
        """Test IP address sanitization."""
        text = "Connected to 192.168.1.100"
        sanitized = DataSanitizer.sanitize_text(text)
        assert "192.168.1.100" not in sanitized
        assert "[REDACTED_IP]" in sanitized
    
    def test_sanitize_home_paths(self):
        """Test home path sanitization."""
        text = "File at /home/username/project/file.txt"
        sanitized = DataSanitizer.sanitize_text(text)
        assert "username" not in sanitized
        assert "[REDACTED_PATH]" in sanitized
    
    def test_sanitize_list(self):
        """Test list sanitization."""
        items = ["api_key=secret123", "normal text", "email@test.com"]
        sanitized = DataSanitizer.sanitize_list(items)
        assert len(sanitized) == 3
        assert "secret123" not in sanitized[0]
        assert "normal text" in sanitized[1]
        assert "email@test.com" not in sanitized[2]
    
    def test_sanitize_path(self):
        """Test path sanitization."""
        assert DataSanitizer.sanitize_path("/home/alice/project") == "/home/[USER]/project"
        assert DataSanitizer.sanitize_path("/Users/bob/Documents") == "/Users/[USER]/Documents"
        assert DataSanitizer.sanitize_path("/etc/config") == "/etc/config"


class TestResultSubmitter:
    """Test result submission functionality."""
    
    @pytest.fixture
    def submitter(self, tmp_path):
        """Create a submitter with test config path."""
        # Patch the CONFIG_FILE class variable directly
        with patch.object(ResultSubmitter, 'CONFIG_FILE', tmp_path / ".agentprobe" / "sharing.json"):
            return ResultSubmitter()
    
    def test_config_management(self, tmp_path):
        """Test configuration save/load."""
        # Create a fresh submitter with patched config path
        with patch.object(ResultSubmitter, 'CONFIG_FILE', tmp_path / ".agentprobe" / "sharing.json"):
            submitter = ResultSubmitter()
            
            config = {
                "enabled": True,
                "api_key": "test-key",
                "api_url": "https://test.api"
            }
            submitter.save_config(config)
            
            # Verify file was created
            config_file = tmp_path / ".agentprobe" / "sharing.json"
            assert config_file.exists()
            
            # Load and verify - save_config just saves what's passed
            loaded = json.loads(config_file.read_text())
            assert loaded == config
            
            # Create a new submitter to test loading
            submitter2 = ResultSubmitter()
            loaded_config = submitter2._load_config()
            # Check that saved values are loaded
            assert loaded_config["enabled"] == config["enabled"]
            assert loaded_config["api_key"] == config["api_key"]
            assert loaded_config["api_url"] == config["api_url"]
    
    def test_anonymous_id_generation(self, submitter, tmp_path):
        """Test anonymous ID is generated and persisted."""
        id1 = submitter.anonymous_id
        assert id1 is not None
        assert len(id1) == 16
        
        # Create new submitter with same config path, should get same ID
        with patch.object(ResultSubmitter, 'CONFIG_FILE', tmp_path / ".agentprobe" / "sharing.json"):
            submitter2 = ResultSubmitter()
            assert submitter2.anonymous_id == id1
    
    def test_enable_sharing(self, submitter):
        """Test enabling/disabling sharing."""
        submitter.enable_sharing(True)
        assert submitter.enabled is True
        
        submitter.enable_sharing(False)
        assert submitter.enabled is False
    
    @pytest.mark.asyncio
    async def test_submit_result_disabled(self, submitter):
        """Test submission when disabled."""
        submitter.enabled = False
        result = TestResult(
            run_id="test-123",
            tool="vercel",
            scenario="deploy",
            trace=[],
            duration=10.5,
            analysis={"success": True}
        )
        
        # Should return False without making request
        submitted = await submitter.submit_result(result)
        assert submitted is False
    
    @pytest.mark.asyncio
    async def test_submit_result_success(self, submitter):
        """Test successful submission."""
        submitter.enabled = True
        submitter.api_key = "test-key"
        
        result = TestResult(
            run_id="test-123",
            tool="vercel",
            scenario="deploy",
            trace=[],
            duration=10.5,
            analysis={
                "success": True,
                "friction_points": ["auth"],
                "recommendations": ["Use --token flag"]
            }
        )
        
        # Mock HTTP client
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            submitted = await submitter.submit_result(result, force=True)
            
            assert submitted is True
            mock_client.post.assert_called_once()
            
            # Verify payload
            call_args = mock_client.post.call_args
            assert call_args[0][0].endswith("/results")
            assert "Authorization" in call_args[1]["headers"]
            
            # Check payload structure
            payload = call_args[1]["json"]
            assert payload["tool"] == "vercel"
            assert payload["scenario"] == "deploy"
            assert payload["execution"]["success"] is True
    
    def test_prepare_payload_sanitization(self, submitter):
        """Test payload preparation with sanitization."""
        # Create result with sensitive data
        trace_mock = Mock()
        trace_mock.role = "assistant"
        trace_mock.content = "Using API_KEY=secret123 to authenticate"
        
        result = TestResult(
            run_id="test-123",
            tool="vercel",
            scenario="deploy",
            trace=[trace_mock],
            duration=10.5,
            analysis={
                "success": False,
                "error_message": "Failed with token: abc123",
                "recommendations": ["Check email@example.com"]
            }
        )
        
        submitter.include_traces = True
        payload = submitter._prepare_payload(result)
        
        # Verify sanitization
        assert "secret123" not in payload.execution.error_message
        assert "abc123" not in payload.execution.error_message
        assert "email@example.com" not in str(payload.analysis.recommendations)
        
        # Verify structure
        assert isinstance(payload, ResultSubmission)
        assert payload.tool == "vercel"
        assert payload.scenario == "deploy"