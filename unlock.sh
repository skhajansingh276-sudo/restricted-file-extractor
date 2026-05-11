#!/bin/bash

# Check if a URL was provided
if [ -z "$1" ]; then
    echo "Usage: ./unlock.sh <GOOGLE_DOC_URL>"
    exit 1
fi

# Path to this script's directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Run the python script using the venv's python directly
# This avoids needing to manually 'source' the venv
"$DIR/venv/bin/python3" "$DIR/drive_unlocker.py" "$1"
