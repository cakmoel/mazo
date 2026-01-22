#!/bin/bash
# Load testing script for 1000 iterations on myblog.local

set -e

echo "🚀 Starting 1000 Iteration Load Test - http://myblog.local"
echo "========================================================"

# Activate virtual environment
source venv/bin/activate

# Verify target is reachable
echo "📡 Checking connectivity to http://myblog.local..."
if curl -s --head --connect-timeout 10 "http://myblog.local" > /dev/null; then
    echo "✅ Target server is reachable"
else
    echo "❌ Target server is not reachable. Please check:"
    echo "   - myblog.local is in /etc/hosts pointing to 127.0.0.1"
    echo "   - Local web server is running"
    exit 1
fi

# Create results directory
RESULTS_DIR="load_test_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "📊 Results will be saved to: $RESULTS_DIR"

# Run load test with 1000 iterations
echo "🔥 Starting load test with 1000 iterations..."
echo "   - Target: http://myblog.local"
echo "   - Users: 50 concurrent"
echo "   - Spawn Rate: 10 users/second"
echo "   - Duration: Until 1000 iterations completed"
echo

# Run Locust in headless mode with CSV output
locust \
    -f locustfile.py \
    --host=http://myblog.local \
    --users=50 \
    --spawn-rate=10 \
    --run-time=300s \
    --html="$RESULTS_DIR/report.html" \
    --csv="$RESULTS_DIR/load_test" \
    --headless

echo
echo "✅ Load test completed!"
echo "📈 Report generated: $RESULTS_DIR/report.html"
echo "📊 Raw data: $RESULTS_DIR/load_test_*.csv"