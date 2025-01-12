#!/bin/bash

# Usage: status-update.sh <file> <item> <old_status> <new_status> <description>
# Example: status-update.sh .cursor/docs/refactor/implement-operational-logging/PRD.md 4.3.2 🕔 ✅ "Add logging to core components"

file="$1"
item="$2"
old_status="$3"
new_status="$4"
description="$5"

if [ "$old_status" = "🕔" ] && [ "$new_status" = "✅" ]; then
    action="Complete"
elif [ "$old_status" = "✅" ] && [ "$new_status" = "🕔" ]; then
    action="Reopen"
else
    echo "Error: Invalid status transition from $old_status to $new_status"
    echo "Only 🕔->✅ and ✅->🕔 transitions are supported"
    exit 1
fi

# Create commit message using the template format
commit_msg="Status Update: $new_status $action: $description
File: $file
Item: $item"

# Stage the file
git add "$file"

# Commit with the generated message (following COMMIT.template format)
echo "$commit_msg" | git commit -F -

exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Error: Git commit failed"
    exit $exit_code
fi 