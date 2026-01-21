#!/usr/bin/env python3
"""
Locust performance test for PHP MVC Blog
-----------------------------------------------------------
Author: M.Noermoehammad https://github.com/cakmoel
Version: 3.0.0
License: MIT
"""

import json
import logging
import os
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from bs4 import BeautifulSoup
from locust import HttpUser, between, tag, task

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("blog_loadtest")

# ------------------------
# ENHANCED ROUTE LOADING SYSTEM
# ------------------------

ROUTE_FILE = "routes.json"


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class RouteDefinition:
    """Data class representing a route definition"""

    name: str
    path: Optional[str]
    controller: str
    methods: List[HTTPMethod]
    roles: List[str]
    requires_auth: bool
    urls: List[str]

    def __post_init__(self):
        """Validate route definition after initialization"""
        if self.path and not self.path.startswith("/"):
            logger.warning(f"Route '{self.name}' path '{self.path}' should start with '/'")

        if not self.controller or "@" not in self.controller:
            raise ValueError(f"Invalid controller format for route '{self.name}': {self.controller}")

        # Auto-detect if authentication is required
        if not self.requires_auth:
            self.requires_auth = bool(self.roles) or any(
                method in [HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.DELETE] for method in self.methods
            ) or (self.path and "/admin" in self.path) or "dashboard" in self.name.lower()


class RouteLoader:
    """
    Route loader with support for new URL format
    """

    def __init__(self, route_file: str = ROUTE_FILE):
        self.route_file = route_file
        self._routes: Dict[str, RouteDefinition] = {}
        self._loaded = False
        self._load_attempts = 0
        self._max_load_attempts = 3
        self._raw_routes_data: Dict = {}  # Store raw data for URL access

    def load_routes(self, force_reload: bool = False) -> None:
        """
        Load routes from JSON file with comprehensive error handling
        """
        if self._loaded and not force_reload:
            return

        if self._load_attempts >= self._max_load_attempts:
            raise RuntimeError(f"Failed to load routes after {self._max_load_attempts} attempts")

        self._load_attempts += 1

        try:
            # Check if file exists and is readable
            if not os.path.exists(self.route_file):
                raise FileNotFoundError(f"Route file '{self.route_file}' not found")

            if not os.access(self.route_file, os.R_OK):
                raise PermissionError(f"Route file '{self.route_file}' is not readable")

            # Read and parse JSON
            with open(self.route_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    raise RuntimeError(f"Route file '{self.route_file}' contains only whitespace")

                try:
                    self._raw_routes_data = json.loads(content)
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Invalid JSON in '{self.route_file}': {e}")

            # Validate top-level structure
            if not isinstance(self._raw_routes_data, dict):
                raise RuntimeError("Route file must contain a JSON object at root level")

            if len(self._raw_routes_data) < 5:
                logger.warning(
                    f"Route file contains only {len(self._raw_routes_data)} routes, which seems low for production"
                )

            # Process routes
            processed_routes = {}
            skipped_routes = []

            for route_name, route_data in self._raw_routes_data.items():
                try:
                    route_def = self._parse_route_definition(route_name, route_data)
                    processed_routes[route_name] = route_def
                except (ValueError, KeyError, TypeError) as e:
                    logger.error(f"Skipping invalid route '{route_name}': {e}")
                    skipped_routes.append(route_name)
                    continue

            if skipped_routes:
                logger.warning(f"Skipped {len(skipped_routes)} invalid routes: {skipped_routes}")

            if not processed_routes:
                raise RuntimeError("No valid routes found in route file")

            # Update routes atomically
            self._routes = processed_routes
            self._loaded = True
            self._load_attempts = 0  # Reset attempts on success

            logger.info(f"Successfully loaded {len(self._routes)} routes from {self.route_file}")
            if skipped_routes:
                logger.info(f"Skipped {len(skipped_routes)} invalid routes")

        except Exception as e:
            logger.error(f"Failed to load routes (attempt {self._load_attempts}): {e}")
            if self._load_attempts >= self._max_load_attempts:
                logger.critical("Maximum load attempts reached. Route system is unavailable.")
            raise

    def _parse_route_definition(self, name: str, data: Any) -> RouteDefinition:
        """
        Parse a route definition from raw data - SUPPORTS NEW FORMAT
        """
        path = None
        controller = None
        methods = [HTTPMethod.GET]  # Default method
        roles = []
        urls = []  # Store actual URLs

        # Handle NEW route format with "urls" array
        if isinstance(data, dict) and "urls" in data:
            # New format: {"urls": ["/path1", "/path2"], "methods": [...], "controller": "..."}
            urls = data["urls"]
            if urls and isinstance(urls, list) and len(urls) > 0:
                # Use the first URL as the primary path for route matching
                path = str(urls[0])
            else:
                # Handle empty URLs array gracefully
                path = None
                urls = []

            controller = str(data.get("controller", ""))

            # Parse HTTP methods
            if "methods" in data:
                methods = []
                for method in data["methods"]:
                    try:
                        methods.append(HTTPMethod(method.upper()))
                    except ValueError:
                        logger.warning(f"Invalid HTTP method '{method}' in route '{name}', skipping")

                if not methods:
                    methods = [HTTPMethod.GET]

# Parse roles (initialize empty array, populate if present)
            roles = []
            if "roles" in data:
                roles = [str(role) for role in data["roles"]]
        
        # Handle OLD array format for backward compatibility
        elif isinstance(data, list):
            # Array format: ["/path", "Controller@method"]
            if len(data) < 2:
                raise ValueError("Array format requires at least [path, controller]")

            path = str(data[0])
            controller = str(data[1])
            urls = [path]  # Use path as the only URL

        # Handle OLD object format for backward compatibility
        elif isinstance(data, dict):
            # Object format: {"0": "/path", "1": "Controller@method", "methods": [...], "roles": [...]}
            if "0" in data:
                path = str(data["0"])
                controller = str(data.get("1", ""))
                urls = [path]

            # Parse HTTP methods
            if "methods" in data:
                methods = []
                for method in data["methods"]:
                    try:
                        methods.append(HTTPMethod(method.upper()))
                    except ValueError:
                        logger.warning(f"Invalid HTTP method '{method}' in route '{name}', skipping")

                if not methods:
                    methods = [HTTPMethod.GET]

            # Parse roles
            if "roles" in data:
                roles = [str(role) for role in data["roles"]]

        else:
            raise ValueError(f"Route data must be array or object, got {type(data)}")

        # Validate required fields
        # Path can be None for empty URLs (edge case)
        if path is not None and not path:
            raise ValueError("Route path cannot be empty string")

        if not controller:
            raise ValueError("Route controller cannot be empty")

        if "@" not in controller:
            raise ValueError(f"Controller must be in 'Controller@method' format, got '{controller}'")

        return RouteDefinition(
            name=name,
            path=path,
            controller=controller,
            methods=methods,
            roles=roles,
            requires_auth=False,  # Will be auto-detected in __post_init__
            urls=urls,
        )

    def route_exists(self, name: str) -> bool:
        """Check if a route exists"""
        if not self._loaded:
            self.load_routes()
        return name in self._routes

    def get_path(self, name: str) -> Optional[str]:
        """Get path for a route"""
        if not self._loaded:
            self.load_routes()

        route = self._routes.get(name)
        return route.path if route else None

    def get_controller(self, name: str) -> Optional[str]:
        """Get controller for a route"""
        if not self._loaded:
            self.load_routes()

        route = self._routes.get(name)
        return route.controller if route else None

    def get_methods(self, name: str) -> List[HTTPMethod]:
        """Get allowed HTTP methods for a route"""
        if not self._loaded:
            self.load_routes()

        route = self._routes.get(name)
        return route.methods if route else [HTTPMethod.GET]

    def get_roles(self, name: str) -> List[str]:
        """Get required roles for a route"""
        if not self._loaded:
            self.load_routes()

        route = self._routes.get(name)
        return route.roles if route else []

    def requires_authentication(self, name: str) -> bool:
        """Check if a route requires authentication"""
        if not self._loaded:
            self.load_routes()

        route = self._routes.get(name)
        return route.requires_auth if route else False

    def get_route(self, name: str) -> Optional[RouteDefinition]:
        """Get complete route definition"""
        if not self._loaded:
            self.load_routes()

        return self._routes.get(name)

    def get_all_routes(self) -> Dict[str, RouteDefinition]:
        """Get all loaded routes"""
        if not self._loaded:
            self.load_routes()

        return self._routes.copy()

    def get_public_routes(self) -> Dict[str, RouteDefinition]:
        """Get routes that don't require authentication"""
        if not self._loaded:
            self.load_routes()

        return {name: route for name, route in self._routes.items() if not route.requires_auth}

    def get_protected_routes(self) -> Dict[str, RouteDefinition]:
        """Get routes that require authentication"""
        if not self._loaded:
            self.load_routes()

        return {name: route for name, route in self._routes.items() if route.requires_auth}

    def get_random_url(self, route_name: str) -> Optional[str]:
        """Get a random URL from route's URL list"""
        if not self._loaded:
            self.load_routes()

        route = self._routes.get(route_name)
        if route and route.urls:
            return random.choice(route.urls)

        return route.path if route else None

    def get_all_urls(self, route_name: str) -> List[str]:
        """Get all URLs for a route"""
        if not self._loaded:
            self.load_routes()

        route = self._routes.get(route_name)
        return route.urls if route else []


# ------------------------
# GLOBAL CONFIGURATION
# ------------------------

# Initialize enhanced route loader
route_loader = RouteLoader()


# Backward compatibility functions
def load_routes():
    """Load route definitions (legacy function)"""
    route_loader.load_routes()


def route_exists(name):
    """Check if route exists (legacy function)"""
    return route_loader.route_exists(name)


def get_path(name):
    """Get route path (legacy function)"""
    return route_loader.get_path(name)


def get_controller(name):
    """Get route controller (legacy function)"""
    return route_loader.get_controller(name)


def get_methods(name):
    """Get route methods (legacy function)"""
    return [method.value for method in route_loader.get_methods(name)]


def get_roles(name):
    """Get route roles (legacy function)"""
    return route_loader.get_roles(name)


POSTS = []

ADMIN_USERS = [
    {"username": "YOUR_USERNAME", "password": "YOUR_PASSWORD"},
    {"username": "YOUR_USERNAME", "password": "YOUR_PASSWORD"},
    {"username": "YOUR_USERNAME", "password": "YOUR_PASSWORD"},
    {"username": "YOUR_USERNAME", "password": "YOUR_PASSWORD"},
]

READER_USERS = [
    {"username": "YOUR_USERNAME", "password": "YOUR_PASSWORD"},
    {"username": "YOUR_USERNAME", "password": "YOUR_PASSWORD"},
]

# Initialize routes
try:
    route_loader.load_routes()
    logger.info("Route system initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize route system: {e}")


# ------------------------
# ENHANCED BASE USER CLASS
# ------------------------


class BaseUser(HttpUser):
    abstract = True
    wait_time = between(1.2, 3.5)
    is_admin = False

    def on_start(self):
        global POSTS
        if not POSTS:
            self.load_posts()

        self.logged_in = False
        self.credentials = None
        self.session_cookies = {}

        if self.is_admin:
            self.credentials = random.choice(ADMIN_USERS)
            self.login()
        elif READER_USERS:
            self.credentials = random.choice(READER_USERS)

        logger.info(f"User started: {self.credentials['username'] if self.credentials and 'username' in self.credentials else 'Anonymous'}")

    def on_stop(self):
        username = self.credentials["username"] if self.credentials and "username" in self.credentials else "Anonymous"
        logger.info(f"User stopped: {username} (logged_in: {self.logged_in})")

    def load_posts(self):
        """Load post list from API or scrape homepage with fallbacks"""
        global POSTS
        if POSTS:
            return

        # Try multiple API endpoints
        api_endpoints = [
            ("api-posts-index", "/api/v1/posts"),
            ("api-posts-recent", "/api/v1/posts/recent"),
            ("api-posts-popular", "/api/v1/posts/popular"),
        ]

        for route_name, fallback_path in api_endpoints:
            try:
                api_path = route_loader.get_path(route_name) or fallback_path
                res = self.client.get(api_path, name=f"[API] {route_name}")

                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list):
                        POSTS = [{"id": p["id"], "slug": p.get("slug", f"post-{p['id']}")} for p in data if "id" in p]
                    elif isinstance(data, dict) and "posts" in data:
                        POSTS = [
                            {"id": p["id"], "slug": p.get("slug", f"post-{p['id']}")}
                            for p in data["posts"]
                            if "id" in p
                        ]

                    if POSTS:
                        logger.info(f"Loaded {len(POSTS)} posts from {route_name}")
                        return
            except Exception as e:
                logger.debug(f"API endpoint {route_name} failed: {e}")
                continue

        # Fallback: use URLs from single route
        try:
            single_urls = route_loader.get_all_urls("single")
            if single_urls:
                for url in single_urls:
                    if url.startswith("/post/"):
                        parts = url.strip("/").split("/")
                        if len(parts) >= 3 and parts[1].isdigit():
                            POSTS.append({"id": int(parts[1]), "slug": parts[2]})

                if POSTS:
                    logger.info(f"Extracted {len(POSTS)} posts from route URLs")
                    return
        except Exception as e:
            logger.debug(f"Could not extract posts from route URLs: {e}")

        # Last fallback - generate sample posts
        POSTS = [{"id": i, "slug": f"sample-post-{i}"} for i in range(1, 11)]
        logger.warning(f"Using {len(POSTS)} fallback sample posts")

    def login(self):
        """Perform login with enhanced error handling and session management"""
        if not route_loader.route_exists("login") or not route_loader.route_exists("login-submit"):
            logger.warning("Login routes missing; skipping admin login")
            return False

        login_path = route_loader.get_path("login")
        submit_path = route_loader.get_path("login-submit")

        try:
            # Get login page for CSRF token
            res = self.client.get(login_path or "/login", name="[AUTH] login_page")
            if res.status_code != 200:
                logger.error(f"Failed to load login page: HTTP {res.status_code}")
                return False

            csrf_token = self.extract_csrf_token(res.text)
            if not csrf_token:
                logger.warning("No CSRF token found in login form")

            # Build complete payload matching PHP form exactly
            payload = {
                "username": self.credentials["username"] if self.credentials and "username" in self.credentials else "",
                "password": self.credentials["password"] if self.credentials and "password" in self.credentials else "",
                "login_form": csrf_token or "",
                "remember": "on",
            }

            # Submit login
            with self.client.post(
                submit_path or "/login", data=payload, name="[AUTH] login_submit", catch_response=True
            ) as response:

                # Enhanced success detection
                success_indicators = ["Login successfully", "Logout", "dashboard", "/admin", "Welcome", "Dashboard"]

                error_indicators = {
                    "Check your login details": "Invalid credentials",
                    "Username and password required": "Missing credentials",
                    "Invalid CSRF token": "CSRF validation failed",
                    "Account locked": "Account temporarily locked",
                    "Too many attempts": "Rate limited",
                }

                if response.status_code == 200:
                    if any(indicator in response.text for indicator in success_indicators):
                        response.success()
                        self.logged_in = True
                        self.session_cookies = dict(response.cookies)
                        logger.info(f"Successfully logged in as {self.credentials['username'] if self.credentials and 'username' in self.credentials else 'unknown'}")
                        return True
                    else:
                        # Check for specific errors
                        error_msg = "Unknown failure - returned to login page"
                        for indicator, message in error_indicators.items():
                            if indicator in response.text:
                                error_msg = message
                                break

                        response.failure(f"Login failed: {error_msg}")
                        self.logged_in = False
                        logger.warning(f"Login failed for {self.credentials['username'] if self.credentials and 'username' in self.credentials else 'unknown'}: {error_msg}")
                        return False

                elif response.status_code in [500, 502, 503]:
                    response.failure(f"Server error ({response.status_code}) during login")
                    self.logged_in = False
                    logger.error(f"Server {response.status_code} error for {self.credentials['username'] if self.credentials and 'username' in self.credentials else 'unknown'}")
                    return False
                else:
                    response.failure(f"HTTP {response.status_code} during login")
                    self.logged_in = False
                    logger.error(f"HTTP {response.status_code} for {self.credentials['username'] if self.credentials and 'username' in self.credentials else 'unknown'}")
                    return False

        except Exception as e:
            logger.error(f"Login exception for {self.credentials['username'] if self.credentials and 'username' in self.credentials else 'unknown'}: {str(e)}")
            self.logged_in = False
            return False

    def ensure_logged_in(self):
        """Ensure persistent admin session with enhanced retry logic"""
        if not self.logged_in:
            logger.info(f"Attempting to login {self.credentials['username'] if self.credentials and 'username' in self.credentials else 'unknown'}")
            success = self.login()
            if not success:
                logger.error(f"Failed to establish admin session for {self.credentials['username'] if self.credentials and 'username' in self.credentials else 'unknown'}")
            return success
        return True

    def extract_csrf_token(self, html):
        """Extract CSRF token from HTML with multiple strategies"""
        soup = BeautifulSoup(html, "html.parser")

        # Try multiple possible CSRF token input names
        token_names = ["login_form", "csrf_token", "_token", "csrf", "authenticity_token"]

        for name in token_names:
            token = soup.find("input", {"name": name})
            if token and token.get("value"):
                return token["value"]

        # Try meta tags
        meta_token = soup.find("meta", {"name": "csrf-token"})
        if meta_token:
            return meta_token.get("content")

        return None

    def build_url(self, route_name: str, **params) -> Optional[str]:
        """Build URL from route name with parameters"""
        path = route_loader.get_path(route_name)
        if not path:
            logger.warning(f"Route '{route_name}' not found")
            return None

        # Replace named parameters in the path
        for key, value in params.items():
            pattern = f"(?<{key}>[^/]+)"
            if pattern in path:
                path = path.replace(pattern, str(value))
            else:
                # Fallback for simple {param} syntax
                path = path.replace(f"{{{key}}}", str(value))

        return path

    def get_random_route_url(self, route_name: str) -> Optional[str]:
        """Get a random URL from route's URL list - PRIMARY METHOD"""
        return route_loader.get_random_url(route_name)


# ------------------------
# ENHANCED READER USER
# ------------------------


class ReaderUser(BaseUser):
    weight = 8
    is_admin = False

    @task(4)
    @tag("browse", "public")
    def view_homepage(self):
        """View homepage using random URL or fallback"""
        url = self.get_random_route_url("home") or "/"
        self.client.get(url, name="[READER] homepage")

    @task(6)
    @tag("browse", "public")
    def view_random_post(self):
        """View random post using actual URLs from routes.json"""
        # Try to get a random URL from the route first
        random_url = self.get_random_route_url("single")
        if random_url:
            self.client.get(random_url, name="[READER] post_single")
        else:
            # Fallback to old method
            if not POSTS:
                self.load_posts()
            post = random.choice(POSTS)
            url = self.build_url("single", id=post["id"], slug=post["slug"]) or f"/post/{post['id']}/{post['slug']}"
            self.client.get(url, name="[READER] post_single")

    @task(3)
    @tag("browse", "public")
    def view_categories(self):
        """View random category using actual URLs from routes.json"""
        random_url = self.get_random_route_url("category")
        if random_url:
            self.client.get(random_url, name="[READER] category")
        else:
            # Fallback
            url = self.build_url("category", category="technology") or "/category/technology"
            self.client.get(url, name="[READER] category")

    @task(2)
    @tag("browse", "public")
    def view_archive(self):
        """View archive using actual URLs from routes.json"""
        random_url = self.get_random_route_url("archive")
        if random_url:
            self.client.get(random_url, name="[READER] archive")
        else:
            # Fallback
            url = self.build_url("archive", year=2024, month=random.randint(1, 12)) or "/archive"
            self.client.get(url, name="[READER] archive")

    @task(1)
    @tag("search", "public")
    def search_content(self):
        """Search content"""
        search_terms = ["technology", "programming", "web development", "php", "python"]
        term = random.choice(search_terms)

        # Try search-term route first
        url = self.build_url("search-term", search=term)
        if url:
            self.client.get(url, name="[READER] search_term")
        else:
            # Fallback to GET search
            search_url = self.get_random_route_url("search-get") or "/search"
            self.client.get(f"{search_url}?q={term}", name="[READER] search_get")

    @task(2)
    @tag("comment", "interactive")
    def comment_random_post(self):
        """Comment on random post using comment-store route from routes.json"""
        if not POSTS:
            self.load_posts()

        if not POSTS:
            logger.warning("No posts available for commenting")
            return

        # Get a random post from the available posts
        post = random.choice(POSTS)

        # Try to get a comment URL from the comment-store route
        comment_url = ""

        # Method 1: Try to get a random URL from comment-store route
        if route_loader.route_exists("comment-store"):
            comment_url = route_loader.get_random_url("comment-store") or ""
            logger.debug(f"Got comment URL from route: {comment_url}")

        # Method 2: If no comment-store route or URL, construct from post
        if not comment_url:
            # Get a post URL first
            post_url = self.get_random_route_url("single") or f"/post/{post['id']}/{post['slug']}"

            # Construct comment URL from post URL
            comment_url = post_url + "/comment"
            logger.debug(f"Constructed comment URL: {comment_url}")

        # First, we need to load the post page to get the CSRF token
        # But we need the post URL, not the comment URL
        post_url_for_csrf = comment_url.replace("/comment", "")

        logger.info(f"Loading post page for CSRF: {post_url_for_csrf}")

        # Load the post page to get CSRF token
        res = self.client.get(post_url_for_csrf, name="[READER] post_for_comment")
        if res.status_code != 200:
            logger.error(f"Failed to load post page: HTTP {res.status_code}")
            return

        # Extract form data
        soup = BeautifulSoup(res.text, "html.parser")

        # Find the comment form
        comment_form = soup.find("form", {"id": "commentForm"})
        if not comment_form:
            logger.error("No comment form found with id='commentForm'")
            # List all forms for debugging
            all_forms = soup.find_all("form")
            for form in all_forms:
                logger.error(f"Found form: id={form.get('id')}, action={form.get('action')}")
            return

        # Extract hidden fields
        csrf_input = comment_form.find("input", {"name": "comment_form"}) if comment_form else None
        post_id_input = comment_form.find("input", {"name": "post_id"}) if comment_form else None
        post_slug_input = comment_form.find("input", {"name": "post_slug"}) if comment_form else None

        if not csrf_input:
            logger.error("No CSRF token found (input name='comment_form')")
            return

        # Generate random user data
        author_id = random.randint(1, 9999)

        # Build payload exactly as your form expects
        payload = {
            "comment_form": csrf_input.get("value", "") if csrf_input else "",
            "post_id": post_id_input.get("value", "") if post_id_input else str(post["id"]),
            "post_slug": post_slug_input.get("value", "") if post_slug_input else post["slug"],
            "author": f"Reader{author_id}",
            "email": f"reader{author_id}@example.com",
            "content": f"This is a test comment from Locust user Reader{author_id}. Great post!",
            "saveInfo": "on",  # Checkbox value when checked
        }

        logger.info(f"Submitting comment to: {comment_url}")
        logger.debug(f"Payload keys: {list(payload.keys())}")

        # Submit comment
        with self.client.post(
            comment_url or "",
            data=payload,
            name="[READER] comment_submit",
            catch_response=True,
            allow_redirects=False,  # Don't follow redirects initially
        ) as response:
            # Log response details for debugging
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")

            # Check for different response scenarios

            # Scenario 1: Success with 302 redirect (common in PHP after POST)
            if response.status_code == 302:
                # Get the redirect location
                location = response.headers.get("Location", "")
                logger.info(f"Redirected to: {location}")

                # Check if redirect is back to the post (success) or to error page
                if location and ("/post/" in location or "comment" not in location):
                    response.success()
                    logger.info("Comment submitted successfully (302 redirect)")
                else:
                    response.failure(f"Unexpected redirect: {location}")
                    logger.warning(f"Unexpected redirect location: {location}")

            # Scenario 2: Success with 200 OK (stays on same page with success message)
            elif response.status_code == 200:
                # Check for success messages in the response
                response_text = response.text.lower()

                success_indicators = [
                    "comment submitted successfully",
                    "your comment is awaiting moderation",
                    "thank you for your comment",
                    "success",
                    "alert-success",
                ]

                error_indicators = ["error", "invalid", "required", "failed", "alert-danger", "alert-warning"]

                # Check flash messages in the response
                soup_response = BeautifulSoup(response.text, "html.parser")
                flash_alerts = soup_response.find_all(class_=["alert"])

                if flash_alerts:
                    for alert in flash_alerts:
                        alert_class = alert.get("class") or []
                        alert_text = alert.get_text().lower()
                        logger.info(f"Flash alert: classes={alert_class}, text={alert_text[:100]}")

                # Determine success/failure based on indicators
                if any(indicator in response_text for indicator in success_indicators):
                    response.success()
                    logger.info("Comment submitted successfully (200 with success message)")
                elif any(indicator in response_text for indicator in error_indicators):
                    # Extract error message if possible
                    error_msg = "Form validation error"
                    for alert in flash_alerts:
                        alert_classes = alert.get("class") or []
                        if "alert-danger" in alert_classes or "alert-warning" in alert_classes:
                            error_msg = alert.get_text().strip()[:100]
                            break
                    response.failure(f"Comment failed: {error_msg}")
                    logger.warning(f"Comment submission failed: {error_msg}")
                else:
                    # Check if we're still on a post page (might be success without message)
                    if "post/" in response.url or 'id="commentForm"' in response_text:
                        response.success()
                        logger.info("Comment likely submitted (still on post page)")
                    else:
                        response.failure("Unknown response - no clear success or error indicators")
                        logger.warning("Unknown response after comment submission")

            # Scenario 3: Validation error (422)
            elif response.status_code == 422:
                response.failure("Validation error (422)")
                logger.warning("Comment validation failed")

            # Scenario 4: CSRF error (403)
            elif response.status_code == 403:
                response.failure("CSRF validation failed (403)")
                logger.error("CSRF token validation failed")

            # Scenario 5: Server error
            elif response.status_code >= 500:
                response.failure(f"Server error ({response.status_code})")
                logger.error(f"Server error during comment submission")

            # Scenario 6: Other status codes
            else:
                response.failure(f"Unexpected HTTP status: {response.status_code}")
                logger.warning(f"Unexpected status code: {response.status_code}")

    @task(1)
    @tag("feed", "public")
    def view_rss_feed(self):
        """View RSS feed"""
        url = self.get_random_route_url("rss") or "/rss.xml"
        self.client.get(url, name="[READER] rss_feed")

    @task(1)
    @tag("seo", "public")
    def view_sitemap(self):
        """View sitemap"""
        url = self.get_random_route_url("sitemap") or "/sitemap.xml"
        self.client.get(url, name="[READER] sitemap")


# ------------------------
# ENHANCED ADMIN USER
# ------------------------


class AdminUser(BaseUser):
    weight = 2
    is_admin = True

    def on_start(self):
        super().on_start()
        # Pre-load admin routes to ensure they're available
        self.ensure_admin_routes()

    def ensure_admin_routes(self):
        """Verify that essential admin routes are available"""
        essential_routes = ["dashboard", "posts", "users", "comments", "categories"]
        missing_routes = [route for route in essential_routes if not route_loader.route_exists(route)]

        if missing_routes:
            logger.warning(f"Missing admin routes: {missing_routes}")

    @task(3)
    @tag("admin", "dashboard")
    def dashboard(self):
        if self.ensure_logged_in():
            url = self.get_random_route_url("dashboard") or "/admin"
            self.client.get(url, name="[ADMIN] dashboard")

    @task(3)
    @tag("admin", "content")
    def manage_posts(self):
        if self.ensure_logged_in():
            url = self.get_random_route_url("posts") or "/admin/posts"
            self.client.get(url, name="[ADMIN] posts_list")

    @task(2)
    @tag("admin", "content")
    def manage_comments(self):
        if self.ensure_logged_in():
            url = self.get_random_route_url("comments") or "/admin/comments"
            self.client.get(url, name="[ADMIN] comments_list")

    @task(2)
    @tag("admin", "users")
    def manage_users(self):
        if self.ensure_logged_in():
            url = self.get_random_route_url("users") or "/admin/users"
            self.client.get(url, name="[ADMIN] users_list")

    @task(2)
    @tag("admin", "content")
    def manage_categories(self):
        if self.ensure_logged_in():
            url = self.get_random_route_url("categories") or "/admin/categories"
            self.client.get(url, name="[ADMIN] categories_list")

    @task(1)
    @tag("admin", "create")
    def create_new_post(self):
        if self.ensure_logged_in():
            url = self.get_random_route_url("post-add") or "/admin/posts/create"

            # First get the create form for CSRF token
            res = self.client.get(url, name="[ADMIN] post_create_form")
            if res.status_code != 200:
                return

            # Extract CSRF token (simplified - adapt to your form)
            soup = BeautifulSoup(res.text, "html.parser")
            csrf_input = None
            for input_tag in soup.find_all("input"):
                name_attr = input_tag.get("name")
                if isinstance(name_attr, str) and "form" in name_attr.lower():
                    csrf_input = input_tag
                    break

            if csrf_input:
                # Submit a sample post (in real scenario, you'd fill all required fields)
                submit_url = self.get_random_route_url("post-add") or "/admin/posts/create"
                payload = {
                    "title": f"Test Post {random.randint(1000, 9999)}",
                    "content": "This is a test post created by Locust load testing.",
                    "csrf_token": csrf_input.get("value", ""),
                }
                self.client.post(submit_url, data=payload, name="[ADMIN] post_create_submit")

    @task(1)
    @tag("admin", "profile")
    def view_profile(self):
        if self.ensure_logged_in():
            url = self.get_random_route_url("profile-edit") or "/profile/edit"
            self.client.get(url, name="[ADMIN] profile_edit")

    @task(1)
    @tag("admin", "navigation")
    def view_random_admin_section(self):
        if self.ensure_logged_in():
            admin_sections = ["posts", "comments", "users", "categories", "dashboard", "profile-edit"]
            section = random.choice(admin_sections)
            url = self.get_random_route_url(section)
            if url:
                self.client.get(url, name=f"[ADMIN] {section}")


# ------------------------
# PERFORMANCE TEST CONFIGURATION
# ------------------------

if __name__ == "__main__":
    # Print configuration summary
    print("🚀 Production Locust Load Test Configuration")
    print("=" * 50)

    stats = {
        "total_routes": len(route_loader.get_all_routes()),
        "public_routes": len(route_loader.get_public_routes()),
        "protected_routes": len(route_loader.get_protected_routes()),
        "admin_users": len(ADMIN_USERS),
        "reader_users": len(READER_USERS),
    }

    for key, value in stats.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    print(f"\nUser Distribution:")
    print(f"  Readers: 80% ({ReaderUser.weight} weight)")
    print(f"  Admins: 20% ({AdminUser.weight} weight)")

    # Show sample URLs
    print(f"\nSample URLs from routes.json:")
    sample_routes = ["single", "category", "archive"]
    for route in sample_routes:
        urls = route_loader.get_all_urls(route)
        if urls:
            print(f"  {route}: {urls[0]}")

    print(f"\nRun with: locust -f this_file.py")
