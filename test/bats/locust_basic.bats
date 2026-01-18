#!/usr/bin/env bats

@test "locust.sh exists and is executable" {
    [ -f "locust.sh" ]
    [ -x "locust.sh" ]
}

@test "locust.sh shows help when --help is passed" {
    run ./locust.sh --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Usage:" ]]
    [[ "$output" =~ "Options:" ]]
    [[ "$output" =~ "--host" ]]
}

@test "locust.sh shows version info" {
    run ./locust.sh --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Version:" ]]
}

@test "locust.sh checks prerequisites" {
    run ./locust.sh --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Checking prerequisites" ]]
    [[ "$output" =~ "Prerequisites check completed" ]]
}

@test "locust.sh validates Python installation" {
    run ./locust.sh --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Python3" ]]
}

@test "locust.sh validates locustfile.py exists" {
    run ./locust.sh --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Locust file" ]]
}

@test "locust.sh handles missing routes.json gracefully" {
    # Backup existing routes.json if it exists
    if [ -f "routes.json" ]; then
        mv routes.json routes.json.backup
    fi
    
    run ./locust.sh --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Route file 'routes.json' not found" ]]
    
    # Restore backup if it existed
    if [ -f "routes.json.backup" ]; then
        mv routes.json.backup routes.json
    fi
}

@test "locust.sh validates routes.json format when present" {
    # Create valid routes.json
    echo '{"home": {"urls": ["/"], "methods": ["GET"], "controller": "HomeController@index"}}' > routes.json
    
    run ./locust.sh --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Route file JSON syntax is valid" ]]
    
    rm -f routes.json
}

@test "locust.sh rejects invalid routes.json" {
    # Create invalid JSON
    echo '{ invalid json }' > routes.json
    
    run ./locust.sh --check-only
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Route file has invalid JSON" ]]
    
    rm -f routes.json
}

@test "locust.sh handles invalid command line options" {
    run ./locust.sh --invalid-option
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Unknown option" ]]
}

@test "locust.sh sets default values correctly" {
    run ./locust.sh --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "http://localhost:8080" ]]
    [[ "$output" =~ "8089" ]]
    [[ "$output" =~ "50" ]]
}

@test "locust.sh accepts custom host parameter" {
    run ./locust.sh --host https://example.com --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Target Host: https://example.com" ]]
}

@test "locust.sh accepts custom port parameter" {
    run ./locust.sh --port 9090 --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Web Interface: http://localhost:9090" ]]
}

@test "locust.sh accepts custom users parameter" {
    run ./locust.sh --users 100 --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Default Users: 100" ]]
}

@test "locust.sh accepts custom spawn rate parameter" {
    run ./locust.sh --spawn-rate 10 --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Default Spawn Rate: 10" ]]
}

@test "locust.sh accepts tags parameter" {
    run ./locust.sh --tags admin --check-only
    [ "$status" -eq 0 ]
    # The script may not show tags in check-only mode, but should not error
}

@test "locust.sh accepts exclude-tags parameter" {
    run ./locust.sh --exclude-tags admin --check-only
    [ "$status" -eq 0 ]
    # The script may not show exclude-tags in check-only mode, but should not error
}

@test "locust.sh validates virtual environment creation" {
    # Clean up any existing venv
    rm -rf venv
    
    run ./locust.sh --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Setting up virtual environment" ]]
}

@test "locust.sh handles existing virtual environment" {
    # Create venv first
    python3 -m venv venv
    
    run ./locust.sh --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Virtual environment already exists" ]]
}

@test "locust.sh validates locustfile.py syntax" {
    run ./locust.sh --check-only
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Locust file syntax is valid" ]]
}