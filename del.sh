#!/bin/bash

# Specify the folder paths
folder_paths=("/app/static/" "/app/temp/")

# Iterate through each folder path
for folder_path in "${folder_paths[@]}"; do
    # Change to the specified folder
    cd "$folder_path" || exit

    # Delete files older than 5 minutes
    find . -type f -mmin +5 -exec rm {} \;

    # Optional: Print a message indicating the operation is complete for each folder
    echo "Files older than 5 minutes deleted in $folder_path"
done
