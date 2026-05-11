#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: ./capture.sh <GOOGLE_DRIVE_URL>"
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Run the Reconstruction Engine (Best for clean PDF content)
"$DIR/venv/bin/python3" "$DIR/drive_pdf_master.py" "$1"
