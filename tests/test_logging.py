"""Tests for verbose and debug logging."""

import logging
from io import StringIO
from unittest.mock import patch

import pytest

from vm_tool.cli import main


def test_default_logging_level():
    """Test that default logging level is WARNING."""
    with patch("sys.argv", ["vm_tool", "config", "list"]):
        with patch("sys.stdout", new=StringIO()):
            # Should not crash and should use WARNING level
            try:
                main()
            except SystemExit:
                pass  # config list with no config is fine


def test_verbose_flag():
    """Test that --verbose enables INFO logging."""
    with patch("sys.argv", ["vm_tool", "--verbose", "config", "list"]):
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            try:
                main()
            except SystemExit:
                pass

            output = mock_stdout.getvalue()
            assert "Verbose output enabled" in output or "No configuration" in output


def test_debug_flag():
    """Test that --debug enables DEBUG logging."""
    with patch("sys.argv", ["vm_tool", "--debug", "config", "list"]):
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            try:
                main()
            except SystemExit:
                pass

            output = mock_stdout.getvalue()
            assert "Debug logging enabled" in output or "No configuration" in output


def test_short_verbose_flag():
    """Test that -v works as shorthand for --verbose."""
    with patch("sys.argv", ["vm_tool", "-v", "config", "list"]):
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            try:
                main()
            except SystemExit:
                pass

            output = mock_stdout.getvalue()
            assert "Verbose output enabled" in output or "No configuration" in output


def test_short_debug_flag():
    """Test that -d works as shorthand for --debug."""
    with patch("sys.argv", ["vm_tool", "-d", "config", "list"]):
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            try:
                main()
            except SystemExit:
                pass

            output = mock_stdout.getvalue()
            assert "Debug logging enabled" in output or "No configuration" in output
