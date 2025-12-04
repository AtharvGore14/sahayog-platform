#!/bin/bash

echo "========================================"
echo "Starting Automated Waste Financial Ledger Backend"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Checking Python installation..."
python3 --version

echo ""
echo "Checking dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo ""
echo "Starting backend server..."
echo "Server will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo "========================================"
echo ""

python3 run_server.py

