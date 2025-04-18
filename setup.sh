#!/bin/bash


source env.sh

while [[ $# -gt 0 ]]; do
    case $1 in
        -form )
            form="$2"
            shift 2
            ;;
        * )
            echo "Usage: bash $0 [-form <local/docker>]"
            exit 1
            ;;
    esac
done 


if [ -z "$form" ]; then
    form="local"
fi


if [ "$form" != "local" ] && [ "$form" != "docker" ]; then
    echo "Invalid form: $form. Valid forms are: local, docker."
    exit 1
fi

if [ "$form" == "docker" ]; then
    docker build . -t cosched
    docker run -it cosched
    exit 0
fi

if [ "$form" == "local" ]; then
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        source venv/bin/activate
        pip3 install -r requirements.txt
    fi
fi