#!/bin/sh
set -e

# If no arguments are passed, keep the container alive
if [ $# -eq 0 ]; then
    echo "Container is running. Use 'docker exec' to run scripts."
    tail -f /dev/null
else
    # Execute the passed command
    exec "$@"
fi