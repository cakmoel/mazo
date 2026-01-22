#!/usr/bin/env python3
"""
Unit tests for BaseUser class and authentication functionality
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add parent directory to path to import locustfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from locustfile import AdminUser, BaseUser, ReaderUser


# Module-level fixtures for pytest to find them
@pytest.fixture
def mock_client():
    """Mock HTTP client"""
    return Mock()

@pytest.fixture
def mock_environment():
    """Mock Locust environment"""
    env = Mock()
    # Mock host attribute to avoid StopTest exception
    env.host = "http://test.example.com"
    env.parsed_options = Mock()
    env.parsed_options.host = "http://test.example.com"
    return env

@pytest.fixture
def base_user(mock_client, mock_environment):
    """Create BaseUser instance for testing"""
    with patch.object(BaseUser, 'host', 'http://test.example.com'):
        user = BaseUser(environment=mock_environment)
        user.client = mock_client
        # Manually initialize attributes that are set in on_start()
        user.logged_in = False
        user.credentials = None
        user.session_cookies = {}
        return user


class TestBaseUser:
    """Test BaseUser class"""

    def test_base_user_initialization(self, base_user):
        """Test BaseUser initialization"""
        assert base_user.is_admin is False
        assert base_user.logged_in is False
        assert base_user.credentials is None
        assert base_user.session_cookies == {}

    @patch("locustfile.route_loader")
    def test_extract_csrf_token_success(self, mock_route_loader, base_user):
        """Test CSRF token extraction from HTML"""
        html_content = """
        <form>
            <input type="hidden" name="csrf_token" value="test_csrf_token_123">
            <button type="submit">Submit</button>
        </form>
        """
        token = base_user.extract_csrf_token(html_content)
        assert token == "test_csrf_token_123"

    def test_extract_csrf_token_multiple_names(self, base_user):
        """Test CSRF token extraction with different input names"""
        html_content = """
        <form>
            <input type="hidden" name="login_form" value="login_token">
            <input type="hidden" name="csrf_token" value="csrf_token">
        </form>
        """
        token = base_user.extract_csrf_token(html_content)
        assert token == "login_token"  # Should find the first match

    def test_extract_csrf_token_meta_tag(self, base_user):
        """Test CSRF token extraction from meta tag"""
        html_content = """
        <html>
        <head>
            <meta name="csrf-token" content="meta_csrf_token">
        </head>
        <body></body>
        </html>
        """
        token = base_user.extract_csrf_token(html_content)
        assert token == "meta_csrf_token"

    def test_extract_csrf_token_not_found(self, base_user):
        """Test CSRF token extraction when no token found"""
        html_content = "<form><button>Submit</button></form>"
        token = base_user.extract_csrf_token(html_content)
        assert token is None

    @patch("locustfile.route_loader")
    def test_build_url_success(self, mock_route_loader, base_user):
        """Test URL building from route name"""
        mock_route_loader.get_path.return_value = "/post/{id}/{slug}"

        url = base_user.build_url("single", id=123, slug="test-post")
        assert url == "/post/123/test-post"

    @patch("locustfile.route_loader")
    def test_build_url_route_not_found(self, mock_route_loader, base_user):
        """Test URL building when route not found"""
        mock_route_loader.get_path.return_value = None

        url = base_user.build_url("nonexistent")
        assert url == ""  # build_url returns empty string for missing routes

    @patch("locustfile.route_loader")
    def test_get_random_route_url(self, mock_route_loader, base_user):
        """Test getting random route URL"""
        mock_route_loader.get_random_url.return_value = "/random/post/123"

        url = base_user.get_random_route_url("single")
        assert url == "/random/post/123"


class TestAuthentication:
    """Test authentication functionality"""

    @pytest.fixture
    def admin_user_with_mock(self):
        """Create AdminUser with mocked dependencies"""
        with patch("locustfile.route_loader") as mock_loader:
            mock_loader.route_exists.return_value = True
            mock_loader.get_path.side_effect = lambda route: {"login": "/login", "login-submit": "/login/submit"}.get(
                route
            )

            user = AdminUser()
            user.client = Mock()
            return user, mock_loader

    def test_admin_user_properties(self):
        """Test AdminUser class properties"""
        assert AdminUser.is_admin is True
        assert AdminUser.weight == 2

    def test_reader_user_properties(self):
        """Test ReaderUser class properties"""
        assert ReaderUser.is_admin is False
        assert ReaderUser.weight == 8

    @patch("locustfile.route_loader")
    @patch("locustfile.ADMIN_USERS", [{"username": "administrator", "password": "4dMini5TrAt0R(*)"}])
    def test_login_success(self, mock_route_loader):
        """Test successful login flow"""
        mock_route_loader.route_exists.return_value = True
        mock_route_loader.get_path.side_effect = lambda route: {"login": "/login", "login-submit": "/login/submit"}.get(
            route
        )

        env = Mock()
        env.host = "http://test.example.com"
        with patch.object(AdminUser, 'host', 'http://test.example.com'):
            user = AdminUser(environment=env)
            user.client = Mock()
            
            # Manually set credentials to avoid randomness and control test data
            user.credentials = {"username": "administrator", "password": "4dMini5TrAt0R(*)"}
            user.logged_in = False
            user.session_cookies = {}
            
            # Mock login page response
            login_response = Mock()
            login_response.status_code = 200
            login_response.text = '<form><input name="login_form" value="csrf123"></form>'

            # Mock login submit response
            submit_response = Mock()
            submit_response.status_code = 200
            submit_response.text = "Login successfully Welcome to dashboard"
            submit_response.cookies = {"session": "test_session"}

            user.client.get.return_value = login_response
            # Mock the context manager properly
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=submit_response)
            mock_context.__exit__ = Mock(return_value=None)
            user.client.post.return_value = mock_context

            result = user.login()

            assert result is True
            assert user.logged_in is True
            assert user.session_cookies == {"session": "test_session"}
            assert user.credentials and user.credentials["username"] == "administrator"

    @patch("locustfile.route_loader")
    def test_login_missing_routes(self, mock_route_loader):
        """Test login when required routes are missing"""
        mock_route_loader.route_exists.return_value = False

        env = Mock()
        env.host = "http://test.example.com"
        with patch.object(AdminUser, 'host', 'http://test.example.com'):
            user = AdminUser(environment=env)
            user.client = Mock()
            
            # Manually set credentials to avoid randomness and control test data
            user.credentials = {"username": "administrator", "password": "4dMini5TrAt0R(*)"}
            user.logged_in = False
            user.session_cookies = {}

            result = user.login()

            assert result is False
            assert user.logged_in is False

    @patch("locustfile.route_loader")
    def test_login_failure_invalid_credentials(self, mock_route_loader):
        """Test login failure due to invalid credentials"""
        mock_route_loader.route_exists.return_value = True
        mock_route_loader.get_path.side_effect = lambda route: {"login": "/login", "login-submit": "/login/submit"}.get(
            route
        )

        env = Mock()
        env.host = "http://test.example.com"
        with patch.object(AdminUser, 'host', 'http://test.example.com'):
            user = AdminUser(environment=env)
            user.client = Mock()
            user.credentials = {"username": "baduser", "password": "badpass"}

            # Mock responses
            login_response = Mock()
            login_response.status_code = 200
            login_response.text = '<form><input name="login_form" value="csrf123"></form>'

            submit_response = Mock()
            submit_response.status_code = 200
            submit_response.text = "Check your login details Invalid credentials"
            submit_response.cookies = {}

            user.client.get.return_value = login_response
            # Mock the context manager properly
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=submit_response)
            mock_context.__exit__ = Mock(return_value=None)
            user.client.post.return_value = mock_context

            result = user.login()

            assert result is False
            assert user.logged_in is False

    @patch("locustfile.route_loader")
    def test_ensure_logged_in_already_logged_in(self, mock_route_loader):
        """Test ensure_logged_in when already logged in"""
        mock_route_loader.route_exists.return_value = True

        env = Mock()
        env.host = "http://test.example.com"
        with patch.object(AdminUser, 'host', 'http://test.example.com'):
            user = AdminUser(environment=env)
            user.logged_in = True
            user.credentials = {"username": "testuser", "password": "testpass"}

            result = user.ensure_logged_in()

            assert result is True

    @patch("locustfile.route_loader")
    @patch.object(AdminUser, "login")
    def test_ensure_logged_in_not_logged_in(self, mock_login, mock_route_loader):
        """Test ensure_logged_in when not logged in"""
        mock_route_loader.route_exists.return_value = True
        mock_login.return_value = True

        env = Mock()
        env.host = "http://test.example.com"
        with patch.object(AdminUser, 'host', 'http://test.example.com'):
            user = AdminUser(environment=env)
            user.logged_in = False
            user.credentials = {"username": "testuser", "password": "testpass"}

            result = user.ensure_logged_in()

            assert result is True
            mock_login.assert_called_once()


@pytest.fixture
def reader_user(mock_client, mock_environment):
    """Create ReaderUser with mocked dependencies"""
    # Patch the global route_loader instance at import time
    with patch("locustfile.route_loader") as mock_loader:
        # Set up comprehensive mock responses for all route loader methods
        mock_loader.get_random_url.side_effect = lambda route_name: {
            "home": "/",
            "single": "/post/8/cicero",
            "category": "/category/technology", 
            "archive": "/archive/2024/1",
            "rss": "/rss.xml",
            "sitemap": "/sitemap.xml",
            "search-get": "/search"
        }.get(route_name, f"/default/{route_name}")
        
        mock_loader.get_path.return_value = "/test/{route_name}"
        mock_loader.route_exists.return_value = True

        with patch.object(ReaderUser, 'host', 'http://test.example.com'):
            user = ReaderUser(environment=mock_environment)
            user.client = mock_client
            return user, mock_loader


class TestUserTasks:
    """Test user task methods"""

    def test_view_homepage(self, reader_user):
        """Test ReaderUser view_homepage task"""
        user, mock_loader = reader_user

        # Mock the get_random_route_url method directly on the user instance
        with patch.object(user, 'get_random_route_url', return_value="/"):
            user.view_homepage()

        user.client.get.assert_called_once_with("/", name="[READER] homepage")

    def test_view_random_post(self, reader_user):
        """Test ReaderUser view_random_post task"""
        user, mock_loader = reader_user

        with patch("locustfile.POSTS", [{"id": 3, "slug": "visiting-bali-a-journey-of-serenity-and-culture"}]):
            # Mock get_random_route_url to return None so it uses fallback method
            with patch.object(user, 'get_random_route_url', return_value=None):
                with patch.object(user, 'build_url', return_value="/post/3/visiting-bali-a-journey-of-serenity-and-culture"):
                    user.view_random_post()

        # Should call with URL that matches POSTS data (fallback method)
        call_args = user.client.get.call_args
        actual_url = call_args[0][0] if call_args else None
        expected_url = "/post/3/visiting-bali-a-journey-of-serenity-and-culture"
        assert actual_url == expected_url, f"Expected {expected_url}, got {actual_url}"
        assert call_args[1]['name'] == "[READER] post_single" if call_args and len(call_args) > 1 else None

    def test_view_categories(self, reader_user):
        """Test ReaderUser view_categories task"""
        user, mock_loader = reader_user

        with patch.object(user, 'get_random_route_url', return_value="/category/technology"):
            user.view_categories()

        # Should call with mocked category URL
        call_args = user.client.get.call_args
        actual_url = call_args[0][0] if call_args else None
        expected_url = "/category/technology"
        assert actual_url == expected_url, f"Expected {expected_url}, got {actual_url}"
        assert call_args[1]['name'] == "[READER] category" if call_args and len(call_args) > 1 else None

    def test_view_rss_feed(self, reader_user):
        """Test ReaderUser view_rss_feed task"""
        user, mock_loader = reader_user

        with patch.object(user, 'get_random_route_url', return_value="/rss.xml"):
            user.view_rss_feed()

        user.client.get.assert_called_once_with("/rss.xml", name="[READER] rss_feed")

    def test_view_sitemap(self, reader_user):
        """Test ReaderUser view_sitemap task"""
        user, mock_loader = reader_user

        with patch.object(user, 'get_random_route_url', return_value="/sitemap.xml"):
            user.view_sitemap()

        user.client.get.assert_called_once_with("/sitemap.xml", name="[READER] sitemap")


@pytest.fixture
def admin_user(mock_client, mock_environment):
    """Create AdminUser with mocked dependencies"""
    # Patch the global route_loader instance at import time
    with patch("locustfile.route_loader") as mock_loader:
        # Set up comprehensive mock responses for all route loader methods
        mock_loader.get_random_url.side_effect = lambda route_name: {
            "dashboard": "/admin",
            "posts": "/admin/posts",
            "comments": "/admin/comments", 
            "users": "/admin/users",
            "categories": "/admin/categories",
            "post-add": "/admin/posts/create",
            "profile-edit": "/profile/edit"
        }.get(route_name, f"/admin/default/{route_name}")
        
        mock_loader.get_path.return_value = "/admin/{route_name}"
        mock_loader.route_exists.return_value = True

        with patch.object(AdminUser, 'host', 'http://test.example.com'):
            user = AdminUser(environment=mock_environment)
            user.client = mock_client
            user.logged_in = True
            user.credentials = {"username": "testadmin", "password": "testpass"}
            return user, mock_loader


class TestAdminTasks:
    """Test admin user task methods"""

    def test_dashboard(self, admin_user):
        """Test AdminUser dashboard task"""
        user, mock_loader = admin_user

        with patch.object(user, 'get_random_route_url', return_value="/admin"):
            user.dashboard()

        user.client.get.assert_called_once_with("/admin", name="[ADMIN] dashboard")

    def test_manage_posts(self, admin_user):
        """Test AdminUser manage_posts task"""
        user, mock_loader = admin_user

        with patch.object(user, 'get_random_route_url', return_value="/admin/posts"):
            user.manage_posts()

        user.client.get.assert_called_once_with("/admin/posts", name="[ADMIN] posts_list")

    def test_manage_comments(self, admin_user):
        """Test AdminUser manage_comments task"""
        user, mock_loader = admin_user

        with patch.object(user, 'get_random_route_url', return_value="/admin/comments"):
            user.manage_comments()

        user.client.get.assert_called_once_with("/admin/comments", name="[ADMIN] comments_list")

    def test_manage_users(self, admin_user):
        """Test AdminUser manage_users task"""
        user, mock_loader = admin_user

        with patch.object(user, 'get_random_route_url', return_value="/admin/users"):
            user.manage_users()

        user.client.get.assert_called_once_with("/admin/users", name="[ADMIN] users_list")

    def test_manage_categories(self, admin_user):
        """Test AdminUser manage_categories task"""
        user, mock_loader = admin_user

        with patch.object(user, 'get_random_route_url', return_value="/admin/categories"):
            user.manage_categories()

        user.client.get.assert_called_once_with("/admin/categories", name="[ADMIN] categories_list")
