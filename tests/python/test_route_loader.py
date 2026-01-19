#!/usr/bin/env python3
"""
Unit tests for RouteLoader class
"""

import json
import os
import sys
import tempfile
from unittest.mock import mock_open, patch

import pytest

# Add parent directory to path to import locustfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from locustfile import HTTPMethod, RouteDefinition, RouteLoader


class TestRouteDefinition:
    """Test RouteDefinition data class"""

    def test_route_definition_creation(self):
        """Test creating a valid RouteDefinition"""
        route = RouteDefinition(
            name="test_route",
            path="/test",
            controller="TestController@index",
            methods=[HTTPMethod.GET],
            roles=["user"],
            requires_auth=False,
            urls=["/test"],
        )

        assert route.name == "test_route"
        assert route.path == "/test"
        assert route.controller == "TestController@index"
        assert route.methods == [HTTPMethod.GET]
        assert route.roles == ["user"]
        assert route.urls == ["/test"]

    def test_route_definition_auto_detect_auth(self):
        """Test automatic authentication detection"""
        # Route with POST method should require auth
        route_post = RouteDefinition(
            name="post_route",
            path="/post",
            controller="TestController@store",
            methods=[HTTPMethod.POST],
            roles=[],
            requires_auth=False,
            urls=["/post"],
        )
        assert route_post.requires_auth is True

        # Route with roles should require auth
        route_roles = RouteDefinition(
            name="admin_route",
            path="/admin",
            controller="AdminController@index",
            methods=[HTTPMethod.GET],
            roles=["admin"],
            requires_auth=False,
            urls=["/admin"],
        )
        assert route_roles.requires_auth is True

    def test_route_definition_validation(self):
        """Test route definition validation"""
        # Invalid controller format
        with pytest.raises(ValueError, match="Invalid controller format"):
            RouteDefinition(
                name="invalid_route",
                path="/test",
                controller="invalid_controller",
                methods=[HTTPMethod.GET],
                roles=[],
                requires_auth=False,
                urls=["/test"],
            )


class TestRouteLoader:
    """Test RouteLoader class"""

    def test_init(self):
        """Test RouteLoader initialization"""
        loader = RouteLoader()
        assert loader.route_file == "routes.json"
        assert loader._loaded is False
        assert loader._routes == {}
        assert loader._load_attempts == 0

    def test_init_custom_file(self):
        """Test RouteLoader with custom file"""
        loader = RouteLoader("custom_routes.json")
        assert loader.route_file == "custom_routes.json"

    def test_load_routes_file_not_found(self):
        """Test loading routes when file doesn't exist"""
        loader = RouteLoader("nonexistent.json")
        with pytest.raises(FileNotFoundError):
            loader.load_routes()

    def test_load_routes_invalid_json(self, tmp_path):
        """Test loading routes with invalid JSON"""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")

        loader = RouteLoader(str(invalid_file))
        with pytest.raises(RuntimeError, match="Invalid JSON"):
            loader.load_routes()

    def test_load_routes_empty_file(self, tmp_path):
        """Test loading routes from empty file"""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("")

        loader = RouteLoader(str(empty_file))
        with pytest.raises(RuntimeError, match="contains only whitespace"):
            loader.load_routes()

    def test_load_routes_success_new_format(self, tmp_path):
        """Test loading routes with new format"""
        routes_data = {
            "home": {"urls": ["/", "/home"], "methods": ["GET"], "controller": "HomeController@index"},
            "post": {
                "urls": ["/post/1/test", "/post/2/another"],
                "methods": ["GET", "POST"],
                "controller": "PostController@show",
                "roles": ["user"],
            },
        }

        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))
        loader.load_routes()

        assert loader._loaded is True
        assert len(loader._routes) == 2
        assert "home" in loader._routes
        assert "post" in loader._routes

        home_route = loader._routes["home"]
        assert home_route.urls == ["/", "/home"]
        assert home_route.methods == [HTTPMethod.GET]
        assert home_route.controller == "HomeController@index"

    def test_load_routes_backward_compatibility_array(self, tmp_path):
        """Test loading routes with old array format"""
        routes_data = {"old_route": ["/old/path", "OldController@method"]}

        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))
        loader.load_routes()

        assert len(loader._routes) == 1
        old_route = loader._routes["old_route"]
        assert old_route.path == "/old/path"
        assert old_route.controller == "OldController@method"
        assert old_route.urls == ["/old/path"]

    def test_load_routes_backward_compatibility_object(self, tmp_path):
        """Test loading routes with old object format"""
        routes_data = {
            "object_route": {
                "0": "/object/path",
                "1": "ObjectController@method",
                "methods": ["GET", "POST"],
                "roles": ["admin"],
            }
        }

        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))
        loader.load_routes()

        assert len(loader._routes) == 1
        object_route = loader._routes["object_route"]
        assert object_route.path == "/object/path"
        assert object_route.controller == "ObjectController@method"
        assert HTTPMethod.GET in object_route.methods
        assert HTTPMethod.POST in object_route.methods
        assert object_route.roles == ["admin"]

    def test_route_exists(self, tmp_path):
        """Test checking if route exists"""
        routes_data = {"home": {"urls": ["/"], "methods": ["GET"], "controller": "HomeController@index"}}
        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))
        assert loader.route_exists("home") is True
        assert loader.route_exists("nonexistent") is False

    def test_get_path(self, tmp_path):
        """Test getting route path"""
        routes_data = {"home": {"urls": ["/home"], "methods": ["GET"], "controller": "HomeController@index"}}
        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))
        assert loader.get_path("home") == "/home"
        assert loader.get_path("nonexistent") is None

    def test_get_random_url(self, tmp_path):
        """Test getting random URL from route"""
        routes_data = {
            "multi": {"urls": ["/url1", "/url2", "/url3"], "methods": ["GET"], "controller": "MultiController@index"}
        }
        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))
        random_url = loader.get_random_url("multi")
        assert random_url in ["/url1", "/url2", "/url3"]

    def test_get_all_urls(self, tmp_path):
        """Test getting all URLs for a route"""
        routes_data = {"test": {"urls": ["/test1", "/test2"], "methods": ["GET"], "controller": "TestController@index"}}
        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))
        urls = loader.get_all_urls("test")
        assert urls == ["/test1", "/test2"]

    def test_get_public_routes(self, tmp_path):
        """Test getting public routes (no auth required)"""
        routes_data = {
            "public": {"urls": ["/public"], "methods": ["GET"], "controller": "PublicController@index"},
            "private": {"urls": ["/private"], "methods": ["POST"], "controller": "PrivateController@store"},
        }
        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))
        public_routes = loader.get_public_routes()
        assert "public" in public_routes
        assert "private" not in public_routes

    def test_get_protected_routes(self, tmp_path):
        """Test getting protected routes (auth required)"""
        routes_data = {
            "public": {"urls": ["/public"], "methods": ["GET"], "controller": "PublicController@index"},
            "private": {"urls": ["/private"], "methods": ["POST"], "controller": "PrivateController@store"},
        }
        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))
        protected_routes = loader.get_protected_routes()
        assert "private" in protected_routes
        assert "public" not in protected_routes

    def test_max_load_attempts(self, tmp_path):
        """Test maximum load attempts limit"""
        routes_file = tmp_path / "routes.json"
        routes_file.write_text('{"test": "invalid"}')

        loader = RouteLoader(str(routes_file))

        # Should raise RuntimeError when no valid routes found
        with pytest.raises(RuntimeError, match="No valid routes found in route file"):
            loader.load_routes()  # This will fail because route is invalid
