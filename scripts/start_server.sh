#!/bin/bash

# Define log and PID directory
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
LOG_DIR="$SCRIPT_DIR/../logs"
PID_FILE="$LOG_DIR/corecache.pid"
LOG_FILE="$LOG_DIR/corecache.log"

# Create log directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory..."
    mkdir -p "$LOG_DIR"
fi

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

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
REQUIREMENTS_PATH="$SCRIPT_DIR/../requirements.txt"

echo "Using requirements file at: $REQUIREMENTS_PATH"
pip install -r "$REQUIREMENTS_PATH"

# Check if both arguments are provided
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 --zooKeeperHost <zooKeeperHost> --zooKeeperPort <zooKeeperPort>"
    exit 1
fi

# Extract arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --zooKeeperHost)
            zooKeeperHost="$2"
            shift # past argument
            shift # past value
            ;;
        --zooKeeperPort)
            zooKeeperPort="$2"
            shift # past argument
            shift # past value
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if the required arguments are set
if [ -z "$zooKeeperHost" ] || [ -z "$zooKeeperPort" ]; then
    echo "Both --zooKeeperHost and --zooKeeperPort must be provided."
    exit 1
fi

# Run the main.py script in the background
echo "Starting CoreCache with ZooKeeper host $zooKeeperHost and port $zooKeeperPort"
nohup python ../main.py --zooKeeperHost "$zooKeeperHost" --zooKeeperPort "$zooKeeperPort" > "$LOG_FILE" 2>&1 &

# Save the PID of the background process
echo $! > "$PID_FILE"