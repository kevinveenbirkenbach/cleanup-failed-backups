#!/bin/bash

# Get the absolute path of the directory where the current script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Define the path to the original cleanup script using the script directory path
CLEANUP_SCRIPT="$SCRIPT_DIR/cleanup.sh"

# Path to the main directory
MAIN_DIRECTORY="/Backups"

# Check if the cleanup script exists
if [ ! -f "$CLEANUP_SCRIPT" ]; then
    echo "Error: The script $CLEANUP_SCRIPT does not exist."
    exit 1
fi

# Iterate through each subdirectory in the main directory
for BACKUP_FOLDER_PATH in "$MAIN_DIRECTORY"/*; do

    # Extract the base name (folder name) from the path
    BACKUP_FOLDER=$(basename "$BACKUP_FOLDER_PATH")

    # Check if the 'backup-docker-to-local' directory exists
    if [ -d "$BACKUP_FOLDER_PATH/backup-docker-to-local" ]; then
        echo "Running cleanup script for folder: $BACKUP_FOLDER"

        # Call the cleanup script
        "$CLEANUP_SCRIPT" "$BACKUP_FOLDER"
    else
        echo "Directory $BACKUP_FOLDER_PATH/backup-docker-to-local not found."
    fi
done