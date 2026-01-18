#!/usr/bin/env python3
"""
Unit tests for BaseUser class and authentication functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import locustfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from locustfile import BaseUser, ReaderUser, AdminUser


class TestBaseUser:
    """Test BaseUser class"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock HTTP client"""
        return Mock()
    
    @pytest.fixture
    def base_user(self, mock_client):
        """Create BaseUser instance for testing"""
        user = BaseUser()
        user.client = mock_client
        return user
    
    def test_base_user_initialization(self, base_user):
        """Test BaseUser initialization"""
        assert base_user.is_admin is False
        assert base_user.logged_in is False
        assert base_user.credentials is None
        assert base_user.session_cookies == {}
    
    @patch('locustfile.route_loader')
    def test_extract_csrf_token_success(self, mock_route_loader, base_user):
        """Test CSRF token extraction from HTML"""
        html_content = '''
        <form>
            <input type="hidden" name="csrf_token" value="test_csrf_token_123">
            <button type="submit">Submit</button>
        </form>
        '''
        token = base_user.extract_csrf_token(html_content)
        assert token == "test_csrf_token_123"
    
    def test_extract_csrf_token_multiple_names(self, base_user):
        """Test CSRF token extraction with different input names"""
        html_content = '''
        <form>
            <input type="hidden" name="login_form" value="login_token">
            <input type="hidden" name="csrf_token" value="csrf_token">
        </form>
        '''
        token = base_user.extract_csrf_token(html_content)
        assert token == "login_token"  # Should find the first match
    
    def test_extract_csrf_token_meta_tag(self, base_user):
        """Test CSRF token extraction from meta tag"""
        html_content = '''
        <html>
        <head>
            <meta name="csrf-token" content="meta_csrf_token">
        </head>
        <body></body>
        </html>
        '''
        token = base_user.extract_csrf_token(html_content)
        assert token == "meta_csrf_token"
    
    def test_extract_csrf_token_not_found(self, base_user):
        """Test CSRF token extraction when no token found"""
        html_content = '<form><button>Submit</button></form>'
        token = base_user.extract_csrf_token(html_content)
        assert token is None
    
    @patch('locustfile.route_loader')
    def test_build_url_success(self, mock_route_loader, base_user):
        """Test URL building from route name"""
        mock_route_loader.get_path.return_value = "/post/{id}/{slug}"
        
        url = base_user.build_url("single", id=123, slug="test-post")
        assert url == "/post/123/test-post"
    
    @patch('locustfile.route_loader')
    def test_build_url_route_not_found(self, mock_route_loader, base_user):
        """Test URL building when route not found"""
        mock_route_loader.get_path.return_value = None
        
        url = base_user.build_url("nonexistent")
        assert url is None
    
    @patch('locustfile.route_loader')
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
        with patch('locustfile.route_loader') as mock_loader:
            mock_loader.route_exists.return_value = True
            mock_loader.get_path.side_effect = lambda route: {
                "login": "/login",
                "login-submit": "/login/submit"
            }.get(route)
            
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
    
    @patch('locustfile.route_loader')
    @patch('locustfile.ADMIN_USERS', [{"username": "testadmin", "password": "testpass"}])
    def test_login_success(self, mock_route_loader):
        """Test successful login flow"""
        mock_route_loader.route_exists.return_value = True
        mock_route_loader.get_path.side_effect = lambda route: {
            "login": "/login",
            "login-submit": "/login/submit"
        }.get(route)
        
        user = AdminUser()
        user.client = Mock()
        
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
        user.client.post.return_value.__enter__.return_value = submit_response
        
        result = user.login()
        
        assert result is True
        assert user.logged_in is True
        assert user.session_cookies == {"session": "test_session"}
        assert user.credentials["username"] == "testadmin"
    
    @patch('locustfile.route_loader')
    def test_login_missing_routes(self, mock_route_loader):
        """Test login when required routes are missing"""
        mock_route_loader.route_exists.return_value = False
        
        user = AdminUser()
        user.client = Mock()
        
        result = user.login()
        
        assert result is False
        assert user.logged_in is False
    
    @patch('locustfile.route_loader')
    def test_login_failure_invalid_credentials(self, mock_route_loader):
        """Test login failure due to invalid credentials"""
        mock_route_loader.route_exists.return_value = True
        mock_route_loader.get_path.side_effect = lambda route: {
            "login": "/login",
            "login-submit": "/login/submit"
        }.get(route)
        
        user = AdminUser()
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
        user.client.post.return_value.__enter__.return_value = submit_response
        
        result = user.login()
        
        assert result is False
        assert user.logged_in is False
    
    @patch('locustfile.route_loader')
    def test_ensure_logged_in_already_logged_in(self, mock_route_loader):
        """Test ensure_logged_in when already logged in"""
        mock_route_loader.route_exists.return_value = True
        
        user = AdminUser()
        user.logged_in = True
        user.credentials = {"username": "testuser", "password": "testpass"}
        
        result = user.ensure_logged_in()
        
        assert result is True
    
    @patch('locustfile.route_loader')
    @patch.object(AdminUser, 'login')
    def test_ensure_logged_in_not_logged_in(self, mock_login, mock_route_loader):
        """Test ensure_logged_in when not logged in"""
        mock_route_loader.route_exists.return_value = True
        mock_login.return_value = True
        
        user = AdminUser()
        user.logged_in = False
        user.credentials = {"username": "testuser", "password": "testpass"}
        
        result = user.ensure_logged_in()
        
        assert result is True
        mock_login.assert_called_once()


class TestUserTasks:
    """Test user task methods"""
    
    @pytest.fixture
    def reader_user(self):
        """Create ReaderUser with mocked dependencies"""
        with patch('locustfile.route_loader') as mock_loader:
            mock_loader.get_random_url.return_value = "/test/url"
            
            user = ReaderUser()
            user.client = Mock()
            return user, mock_loader
    
    def test_view_homepage(self, reader_user):
        """Test ReaderUser view_homepage task"""
        user, mock_loader = reader_user
        
        user.view_homepage()
        
        user.client.get.assert_called_once_with("/test/url", name="[READER] homepage")
    
    def test_view_random_post(self, reader_user):
        """Test ReaderUser view_random_post task"""
        user, mock_loader = reader_user
        
        with patch('locustfile.POSTS', [{"id": 1, "slug": "test"}]):
            user.view_random_post()
        
        user.client.get.assert_called_once_with("/test/url", name="[READER] post_single")
    
    def test_view_categories(self, reader_user):
        """Test ReaderUser view_categories task"""
        user, mock_loader = reader_user
        
        user.view_categories()
        
        user.client.get.assert_called_once_with("/test/url", name="[READER] category")
    
    def test_view_rss_feed(self, reader_user):
        """Test ReaderUser view_rss_feed task"""
        user, mock_loader = reader_user
        
        user.view_rss_feed()
        
        user.client.get.assert_called_once_with("/test/url", name="[READER] rss_feed")
    
    def test_view_sitemap(self, reader_user):
        """Test ReaderUser view_sitemap task"""
        user, mock_loader = reader_user
        
        user.view_sitemap()
        
        user.client.get.assert_called_once_with("/test/url", name="[READER] sitemap")


class TestAdminTasks:
    """Test admin user task methods"""
    
    @pytest.fixture
    def admin_user(self):
        """Create AdminUser with mocked dependencies"""
        with patch('locustfile.route_loader') as mock_loader:
            mock_loader.get_random_url.return_value = "/admin/test"
            mock_loader.route_exists.return_value = True
            
            user = AdminUser()
            user.client = Mock()
            user.logged_in = True
            user.credentials = {"username": "testadmin", "password": "testpass"}
            return user, mock_loader
    
    def test_dashboard(self, admin_user):
        """Test AdminUser dashboard task"""
        user, mock_loader = admin_user
        
        with patch.object(user, 'ensure_logged_in', return_value=True):
            user.dashboard()
        
        user.client.get.assert_called_once_with("/admin/test", name="[ADMIN] dashboard")
    
    def test_manage_posts(self, admin_user):
        """Test AdminUser manage_posts task"""
        user, mock_loader = admin_user
        
        with patch.object(user, 'ensure_logged_in', return_value=True):
            user.manage_posts()
        
        user.client.get.assert_called_once_with("/admin/test", name="[ADMIN] posts_list")
    
    def test_manage_comments(self, admin_user):
        """Test AdminUser manage_comments task"""
        user, mock_loader = admin_user
        
        with patch.object(user, 'ensure_logged_in', return_value=True):
            user.manage_comments()
        
        user.client.get.assert_called_once_with("/admin/test", name="[ADMIN] comments_list")
    
    def test_manage_users(self, admin_user):
        """Test AdminUser manage_users task"""
        user, mock_loader = admin_user
        
        with patch.object(user, 'ensure_logged_in', return_value=True):
            user.manage_users()
        
        user.client.get.assert_called_once_with("/admin/test", name="[ADMIN] users_list")
    
    def test_manage_categories(self, admin_user):
        """Test AdminUser manage_categories task"""
        user, mock_loader = admin_user
        
        with patch.object(user, 'ensure_logged_in', return_value=True):
            user.manage_categories()
        
        user.client.get.assert_called_once_with("/admin/test", name="[ADMIN] categories_list")