#!/bin/bash

source env.sh


cd test_fail

for test_file in *.py; do
    if [ -f "$test_file" ]; then
        echo "Running test: $test_file"
        python3 "$test_file"
        echo "--------------------------------------------------"
    fi
done
