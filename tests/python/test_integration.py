#!/usr/bin/env python3
"""
Integration tests for RouteLoader with real routes.json structure
"""

import json
import os
import sys
import tempfile

import pytest

# Add parent directory to path to import locustfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from locustfile import HTTPMethod, RouteDefinition, RouteLoader


class TestRouteLoaderIntegration:
    """Integration tests with actual routes.json structure"""

    @pytest.fixture
    def sample_routes_data(self):
        """Sample routes data matching the actual structure"""
        return {
            "home": {"urls": ["/"], "methods": ["GET"], "controller": "PostController@home"},
            "single": {
                "urls": ["/post/8/cicero", "/post/6/kafka", "/post/5/far-far-away"],
                "methods": ["GET"],
                "controller": "PostController@show",
            },
            "category": {
                "urls": ["/category/documentation", "/category/food", "/category/programming"],
                "methods": ["GET"],
                "controller": "CategoryController@show",
            },
            "login": {"urls": ["/login"], "methods": ["GET"], "controller": "AuthController@login"},
            "login-submit": {
                "urls": ["/login-submit"],
                "methods": ["POST"],
                "controller": "AuthController@loginSubmit",
            },
            "dashboard": {"urls": ["/admin"], "methods": ["GET"], "controller": "UserController@dashboard"},
            "comment-store": {
                "urls": ["/post/8/cicero/comment", "/post/6/kafka/comment"],
                "methods": ["POST"],
                "controller": "CommentController@store",
            },
            "rss": {"urls": ["/rss.xml"], "methods": ["GET", "HEAD"], "controller": "RSSController@rss"},
            "sitemap": {
                "urls": ["/sitemap.xml"],
                "methods": ["GET", "HEAD"],
                "controller": "SitemapController@generate",
            },
            "api-posts-index": {
                "urls": ["/api/v1/posts"],
                "methods": ["GET"],
                "controller": "Api\\PostController@index",
            },
        }

    @pytest.fixture
    def route_loader(self, sample_routes_data, tmp_path):
        """Create RouteLoader with sample data"""
        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(sample_routes_data))

        loader = RouteLoader(str(routes_file))
        loader.load_routes()
        return loader

    def test_load_complete_routes(self, route_loader):
        """Test loading all routes from sample data"""
        routes = route_loader.get_all_routes()
        assert len(routes) == 10

        # Verify specific routes exist
        assert "home" in routes
        assert "single" in routes
        assert "category" in routes
        assert "login" in routes
        assert "dashboard" in routes

    def test_public_vs_protected_routes(self, route_loader):
        """Test public vs protected route classification"""
        public_routes = route_loader.get_public_routes()
        protected_routes = route_loader.get_protected_routes()

        # Public routes (GET only)
        assert "home" in public_routes
        assert "single" in public_routes
        assert "category" in public_routes
        assert "rss" in public_routes
        assert "sitemap" in public_routes

        # Protected routes (POST or admin)
        assert "login-submit" in protected_routes
        assert "dashboard" in protected_routes
        assert "comment-store" in protected_routes

        # Login should be public (GET method)
        assert "login" in public_routes

    def test_single_route_with_multiple_urls(self, route_loader):
        """Test route with multiple URLs"""
        single_route = route_loader.get_route("single")
        assert single_route is not None
        assert len(single_route.urls) == 3
        assert "/post/8/cicero" in single_route.urls
        assert "/post/6/kafka" in single_route.urls
        assert "/post/5/far-far-away" in single_route.urls

    def test_get_random_url_single_route(self, route_loader):
        """Test getting random URL from single route"""
        random_url = route_loader.get_random_url("single")
        assert random_url in ["/post/8/cicero", "/post/6/kafka", "/post/5/far-far-away"]

    def test_get_random_url_comment_store(self, route_loader):
        """Test getting random URL from comment-store route"""
        random_url = route_loader.get_random_url("comment-store")
        assert random_url in ["/post/8/cicero/comment", "/post/6/kafka/comment"]

    def test_get_all_urls_category(self, route_loader):
        """Test getting all URLs for category route"""
        category_urls = route_loader.get_all_urls("category")
        assert len(category_urls) == 3
        assert "/category/documentation" in category_urls
        assert "/category/food" in category_urls
        assert "/category/programming" in category_urls

    def test_multiple_http_methods(self, route_loader):
        """Test routes with multiple HTTP methods"""
        rss_route = route_loader.get_route("rss")
        sitemap_route = route_loader.get_route("sitemap")

        assert HTTPMethod.GET in rss_route.methods
        assert HTTPMethod.HEAD in rss_route.methods

        assert HTTPMethod.GET in sitemap_route.methods
        assert HTTPMethod.HEAD in sitemap_route.methods

    def test_api_routes(self, route_loader):
        """Test API route structure"""
        api_route = route_loader.get_route("api-posts-index")
        assert api_route is not None
        assert api_route.controller == "Api\\PostController@index"
        assert api_route.urls == ["/api/v1/posts"]
        assert HTTPMethod.GET in api_route.methods

    def test_admin_routes_structure(self, route_loader):
        """Test admin route structure"""
        dashboard_route = route_loader.get_route("dashboard")
        assert dashboard_route is not None
        assert dashboard_route.controller == "UserController@dashboard"
        assert dashboard_route.urls == ["/admin"]
        assert dashboard_route.requires_auth is True  # Admin routes should require auth

    def test_auth_routes(self, route_loader):
        """Test authentication routes"""
        login_route = route_loader.get_route("login")
        login_submit_route = route_loader.get_route("login-submit")

        assert login_route is not None
        assert login_submit_route is not None

        # Login GET should be public
        assert login_route.requires_auth is False

        # Login submit POST should be protected
        assert login_submit_route.requires_auth is True

    def test_comment_routes(self, route_loader):
        """Test comment-related routes"""
        comment_store = route_loader.get_route("comment-store")
        assert comment_store is not None
        assert comment_store.controller == "CommentController@store"
        assert HTTPMethod.POST in comment_store.methods
        assert comment_store.requires_auth is True

    def test_feed_routes(self, route_loader):
        """Test RSS and sitemap routes"""
        rss_route = route_loader.get_route("rss")
        sitemap_route = route_loader.get_route("sitemap")

        assert rss_route.urls == ["/rss.xml"]
        assert sitemap_route.urls == ["/sitemap.xml"]

        # Both should be public
        assert rss_route.requires_auth is False
        assert sitemap_route.requires_auth is False

    def test_route_controller_validation(self, route_loader):
        """Test that all controllers have proper @method format"""
        routes = route_loader.get_all_routes()

        for route_name, route in routes.items():
            assert "@" in route.controller, f"Route {route_name} has invalid controller format: {route.controller}"

    def test_route_url_validation(self, route_loader):
        """Test that all routes have proper URL structure"""
        routes = route_loader.get_all_routes()

        for route_name, route in routes.items():
            assert route.urls, f"Route {route_name} has no URLs"
            assert all(url.startswith("/") for url in route.urls), f"Route {route_name} has invalid URL: {route.urls}"


class TestRouteLoaderEdgeCases:
    """Test edge cases with the actual routes structure"""

    def test_empty_urls_array(self, tmp_path):
        """Test route with empty URLs array"""
        routes_data = {"empty_urls": {"urls": [], "methods": ["GET"], "controller": "TestController@index"}}

        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))

        # Should still load but handle empty URLs gracefully
        loader.load_routes()
        route = loader.get_route("empty_urls")
        assert route.urls == []
        assert route.path is None  # No URLs to determine path

    def test_missing_urls_field(self, tmp_path):
        """Test route without URLs field (backward compatibility)"""
        routes_data = {"old_format": ["/old/path", "OldController@method"]}

        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))
        loader.load_routes()

        route = loader.get_route("old_format")
        assert route.urls == ["/old/path"]
        assert route.path == "/old/path"

    def test_invalid_controller_in_routes(self, tmp_path):
        """Test route with invalid controller format"""
        routes_data = {
            "invalid_controller": {
                "urls": ["/test"],
                "methods": ["GET"],
                "controller": "InvalidController",  # Missing @method
            }
        }

        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))

        # Should skip invalid routes but continue loading others
        with pytest.raises(RuntimeError, match="No valid routes found"):
            loader.load_routes()

    def test_mixed_route_formats(self, tmp_path):
        """Test loading mixed old and new route formats"""
        routes_data = {
            "new_format": {"urls": ["/new"], "methods": ["GET"], "controller": "NewController@index"},
            "old_format": ["/old", "OldController@method"],
            "object_format": {"0": "/object", "1": "ObjectController@method", "methods": ["GET", "POST"]},
        }

        routes_file = tmp_path / "routes.json"
        routes_file.write_text(json.dumps(routes_data))

        loader = RouteLoader(str(routes_file))
        loader.load_routes()

        routes = loader.get_all_routes()
        assert len(routes) == 3
        assert "new_format" in routes
        assert "old_format" in routes
        assert "object_format" in routes
