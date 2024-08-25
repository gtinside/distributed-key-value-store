#!/bin/bash

# Check if process by name CoreCache is running
if pgrep -f "CoreCache" > /dev/null; then
    echo "Process 'CoreCache' is already running. Exiting."
    exit 1
fi

# Check if Python 3.9 or above is installed
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if [[ -z "$PYTHON_VERSION" ]]; then
    echo "Python 3.9 or above is not installed. Exiting."
    exit 1
fi

# Compare the Python versions
if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo "Python version is below 3.9. Exiting."
    exit 1
fi

# Check if virtualenv is installed, if not install it
if ! command -v virtualenv &> /dev/null; then
    echo "virtualenv not found, installing..."
    python3 -m pip install --upgrade pip
    python3 -m pip install virtualenv
fi

# Create a virtual environment and install requirements
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m virtualenv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Installing dependencies..."
pip install -r requirements.txt

# Check if both arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <zooKeeperHost> <zooKeeperPort>"
    exit 1
fi

# Run the main.py with the provided arguments
echo "Starting CoreCache"
python main.py

# Deactivate virtual environment after script execution
deactivate
