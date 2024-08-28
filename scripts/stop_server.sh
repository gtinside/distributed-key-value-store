#!/bin/bash

# Check if the process by name CoreCache is running
if pgrep -f "CoreCache" > /dev/null; then
    echo "Stopping CoreCache process..."

    # Kill the process by name
    pkill -f "CoreCache"
    
    # Optionally, wait a bit to ensure the process is terminated
    sleep 2
    
    # Verify if the process is still running
    if pgrep -f "CoreCache" > /dev/null; then
        echo "Process 'CoreCache' did not stop. Forcefully terminating..."
        pkill -9 -f "CoreCache"
    else
        echo "Process 'CoreCache' stopped successfully."
    fi
else
    echo "No process named 'CoreCache' found."
fi