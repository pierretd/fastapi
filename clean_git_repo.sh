#!/bin/bash

# Script to clean up Git repository by removing unnecessary files from tracking
# This only removes them from Git tracking, not from your filesystem

echo "This script will remove unnecessary files from Git tracking."
echo "This will not delete the files from your computer, only from Git."
echo "Press Ctrl+C to cancel or Enter to continue..."
read

# Remove frontend directory from Git tracking (but keep it on filesystem)
echo "Removing frontend directory from Git tracking..."
git ls-files | grep -E "^frontend/" | xargs git rm --cached

# Remove test files from Git tracking (but keep them on filesystem)
echo "Removing test files from Git tracking..."
git ls-files | grep -E "^test_.*\.py$" | xargs git rm --cached

# Remove PID files
echo "Removing PID files from Git tracking..."
git ls-files | grep -E "_pid\.txt$" | xargs git rm --cached

# Remove backup files
echo "Removing backup files from Git tracking..."
git ls-files | grep -E "\.(bak|backup)$" | xargs git rm --cached
git ls-files | grep -E "\.backup[0-9]*$" | xargs git rm --cached
git ls-files | grep -E "copy\..*$" | xargs git rm --cached

# Remove log files
echo "Removing log files from Git tracking..."
git ls-files | grep -E "\.log$" | xargs git rm --cached
git ls-files | grep -E "^server_.*\.log$" | xargs git rm --cached

echo "Done removing files from Git tracking."
echo ""
echo "Files removed from Git tracking but still on your filesystem."
echo "Next steps:"
echo "1. Verify the changes with 'git status'"
echo "2. Commit the changes with 'git commit -m \"Remove unnecessary files from tracking\"'"
echo "3. Push the changes with 'git push'"
echo ""
echo "This will ensure future commits only include essential files for the Render app." 