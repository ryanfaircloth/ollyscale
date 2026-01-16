"""Tests for AI agent demo application."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

import agent


def test_agent_imports():
    """Test that agent module can be imported."""
    # Check that required modules are imported
    assert hasattr(agent, "tracer")
    assert hasattr(agent, "client")
    assert hasattr(agent, "PROMPTS")
    assert hasattr(agent, "run_agent_workflow")


def test_prompts_are_defined():
    """Test that prompts list is properly defined."""
    assert isinstance(agent.PROMPTS, list)
    assert len(agent.PROMPTS) > 0
    # Check that all prompts are strings
    for prompt in agent.PROMPTS:
        assert isinstance(prompt, str)
        assert len(prompt.strip()) > 0


@patch("agent.client")
@patch("agent.tracer")
def test_run_agent_workflow(mock_tracer, mock_client):
    """Test the agent workflow runs without errors."""
    # Mock the tracer span
    mock_span = Mock()
    mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
    mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)

    # Mock the Ollama client response
    mock_response = {"message": {"content": "This is a test response from the AI model."}}
    mock_client.chat.return_value = mock_response

    # Run the workflow
    result = agent.run_agent_workflow()

    # Verify the result
    assert result == "This is a test response from the AI model."

    # Verify that tracer was called
    mock_tracer.start_as_current_span.assert_called_once()

    # Verify that client was called
    mock_client.chat.assert_called_once()

    # Verify span attributes were set
    assert mock_span.set_attribute.call_count == 2  # prompt and response_length


def test_ollama_host_environment():
    """Test that OLLAMA_HOST environment variable is handled correctly."""
    # The OLLAMA_HOST should be set from environment or default
    assert hasattr(agent, "OLLAMA_HOST")
    assert isinstance(agent.OLLAMA_HOST, str)
    assert len(agent.OLLAMA_HOST) > 0
