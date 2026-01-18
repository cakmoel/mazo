#!/usr/bin/env python3
"""
Test configuration and fixtures
"""

import json
import os
import sys
import tempfile
from unittest.mock import Mock

import pytest

# Add parent directory to path to import locustfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_routes_file():
    """Create a temporary routes.json file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # Write basic routes structure
        basic_routes = {
            "home": {"urls": ["/"], "methods": ["GET"], "controller": "HomeController@index"},
            "single": {"urls": ["/post/1/test"], "methods": ["GET"], "controller": "PostController@show"},
        }
        json.dump(basic_routes, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response"""
    response = Mock()
    response.status_code = 200
    response.text = "<html><body>Test content</body></html>"
    response.cookies = {}
    response.headers = {}
    return response


@pytest.fixture
def mock_csrf_response():
    """Create a mock response with CSRF token"""
    response = Mock()
    response.status_code = 200
    response.text = """
    <form>
        <input type="hidden" name="login_form" value="csrf_test_token_123">
        <button type="submit">Login</button>
    </form>
    """
    response.cookies = {}
    response.headers = {}
    return response


@pytest.fixture
def mock_login_success_response():
    """Create a mock successful login response"""
    response = Mock()
    response.status_code = 200
    response.text = "Login successfully Welcome to dashboard"
    response.cookies = {"session": "test_session_id"}
    response.headers = {"Location": "/admin"}
    return response


@pytest.fixture
def mock_login_failure_response():
    """Create a mock failed login response"""
    response = Mock()
    response.status_code = 200
    response.text = "Check your login details Invalid credentials"
    response.cookies = {}
    response.headers = {}
    return response
