#!/usr/bin/env python3
"""
Test runner script for local development
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    success = result.returncode == 0
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"\n{status}: {description}")
    
    return success

def main():
    """Main test runner"""
    print("🚀 Mazo Test Runner")
    print("Running comprehensive test suite...")
    
    tests_passed = 0
    tests_total = 0
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Shell script validation
    tests_total += 1
    if run_command("shellcheck locust.sh", "ShellCheck validation"):
        tests_passed += 1
    
    # 2. BATS tests
    tests_total += 1
    if run_command("bats tests/bash/", "BATS shell tests"):
        tests_passed += 1
    
    # 3. Python syntax check
    tests_total += 1
    if run_command("python -m py_compile locustfile.py", "Python syntax check"):
        tests_passed += 1
    
    # 4. Python unit tests
    tests_total += 1
    if run_command("pytest tests/python/ -v --tb=short", "Python unit tests"):
        tests_passed += 1
    
    # 5. Script configuration test
    tests_total += 1
    if run_command("./locust.sh --check-only", "Script configuration test"):
        tests_passed += 1
    
    # 6. Test with sample routes.json
    tests_total += 1
    sample_routes_test = '''
import sys
sys.path.insert(0, '.')
from locustfile import RouteLoader
import json

# Create sample routes
sample_routes = {
    "home": {"urls": ["/"], "methods": ["GET"], "controller": "HomeController@index"},
    "single": {"urls": ["/post/1/test"], "methods": ["GET"], "controller": "PostController@show"}
}

with open('test_routes.json', 'w') as f:
    json.dump(sample_routes, f)

try:
    loader = RouteLoader('test_routes.json')
    loader.load_routes()
    print(f"✅ Successfully loaded {len(loader.get_all_routes())} routes")
    os.remove('test_routes.json')
    print("✅ Integration test passed")
except Exception as e:
    print(f"❌ Integration test failed: {e}")
    sys.exit(1)
'''
    
    if run_command(f"python3 -c '{sample_routes_test}'", "Integration test with sample routes"):
        tests_passed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("🏁 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("🎉 All tests passed! Ready to commit.")
        return 0
    else:
        print(f"❌ {tests_total - tests_passed} test(s) failed. Please fix before committing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())