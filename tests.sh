#!/bin/bash

source env.sh


cd test_fail
rm -rf logs
mkdir -p logs

iterations=$1
if [ -z "$iterations" ]; then
    iterations=1
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
        python3 "$test_file" >> logs/${test_file}.log 2>&1
        
    done
    echo "<=================================================================================>" >> logs/${test_file}.log
    fi
done
