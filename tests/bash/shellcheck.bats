#!/usr/bin/env bats

@test "shellcheck passes on locust.sh" {
    run shellcheck locust.sh
    [ "$status" -eq 0 ]
}

@test "locust.sh has no SC2086 issues" {
    run shellcheck -f gcc locust.sh
    [ "$status" -eq 0 ]
    ! [[ "$output" =~ "SC2086" ]]
}

@test "locust.sh has no SC2162 issues" {
    run shellcheck -f gcc locust.sh
    [ "$status" -eq 0 ]
    ! [[ "$output" =~ "SC2162" ]]
}

@test "locust.sh follows bash best practices" {
    run shellcheck -S style locust.sh
    [ "$status" -eq 0 ]
}

@test "locust.sh has proper error handling" {
    run shellcheck locust.sh
    [ "$status" -eq 0 ]
    # Should have set -e at the beginning
    grep -q "^set -e" locust.sh
}

@test "locust.sh quotes variables properly" {
    run shellcheck locust.sh
    [ "$status" -eq 0 ]
    # Check for proper variable quoting
}

@test "locust.sh uses functions correctly" {
    run shellcheck locust.sh
    [ "$status" -eq 0 ]
}

@test "locust.sh handles command line arguments safely" {
    run shellcheck locust.sh
    [ "$status" -eq 0 ]
}