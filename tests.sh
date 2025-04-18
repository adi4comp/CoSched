#!/bin/bash

source env.sh


cd test_fail
rm -rf logs
mkdir -p logs

while [[ $# -gt 0 ]]; do
    case $1 in
        -policy)
            policy="$2"
            shift 2
            ;;
        -iter)
            iterations="$2"
            shift 2
            ;;
        *)
            echo "Usage: bash $0 [-policy <name>] [-iter <number>]"
            exit 1
            ;;
    esac
done

if [ -z "$policy" ]; then
    policy="random"
fi

if [ -z "$iterations"]; then
    iterations=1
fi

if [ "$policy" != "random" ] && [ "$policy" != "priority" ] && [ "$policy" != "interactive" ]; then
    echo "Invalid policy: $policy. Valid policies are: random, priority, interactive."
    exit 1
fi

for test_file in *.py; do
    if [ -f "$test_file" ]; then
    echo "-----------------------------------------------------------------------------"
    echo "Running test: $test_file"
    for ((i=1; i<=iterations; i++)); do
        echo "" >> logs/${test_file}.log
        echo "<=================================================================================>" >> logs/${test_file}.log
        echo "Running test: $test_file, iteration: $i" >> logs/${test_file}.log
        echo "Running test: $test_file, iteration: $i"
        python3 "$test_file" --$policy >> logs/${test_file}.log 2>&1
        
    done
    echo "<=================================================================================>" >> logs/${test_file}.log
    error_count=$(grep -c "There is/are [0-9]\+ error in the above interleaving" logs/${test_file}.log)
    if [ "$error_count" -gt 0 ]; then
        echo ""
        echo "[Tests Summary] There is/are $error_count/$iterations schedules with error in the generated interleavings (Check the error log)"
        echo "" >> logs/${test_file}.log
        echo "[Tests Summary] There is/are $error_count/$iterations schedules with error in the generated interleavings" >> logs/${test_file}.log
    else
        echo ""
        echo "No errors found in the $iterations generated interleavings"
        echo "" >> logs/${test_file}.log
        echo "No errors found in the $iterations generated interleavings" >> logs/${test_file}.log
    fi
    fi
done
