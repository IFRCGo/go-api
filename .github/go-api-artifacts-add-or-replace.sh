#!/bin/bash

set -e

if ! command -v jq &>/dev/null; then
    echo "jq is not installed."
    exit 1
fi

: "${GITHUB_TOKEN:?GITHUB_TOKEN is required and cannot be empty}"
: "${GITHUB_OWNER:?GITHUB_OWNER is required and cannot be empty}"
: "${GITHUB_REPO:?GITHUB_REPO is required and cannot be empty}"
: "${GITHUB_BRANCH:?GITHUB_BRANCH is required and cannot be empty}"
: "${SOURCE_FILE_PATH:?SOURCE_FILE_PATH is required and cannot be empty}"
: "${DEST_FILE_PATH:?DEST_FILE_PATH is required and cannot be empty}"
: "${COMMIT_MESSAGE:?COMMIT_MESSAGE is required and cannot be empty}"

GITHUB_API_URL="https://api.github.com/repos/$GITHUB_OWNER/$GITHUB_REPO/contents/$DEST_FILE_PATH"

function get_existing_file_sha {
    # Get file SHA if it exists
    FILE_INFO=$(curl -s -H "Authorization: token $GITHUB_TOKEN" $GITHUB_API_URL?ref=$GITHUB_BRANCH)
    echo "$FILE_INFO" | jq -r .sha
}

# Read and encode file
if [ ! -f "$SOURCE_FILE_PATH" ]; then
    echo "File $SOURCE_FILE_PATH not found!"
    exit 1
fi
# NOTE: -w 0 disables line wrapping
ENCODED_CONTENT=$(base64 -w 0 "$SOURCE_FILE_PATH")

EXISTING_FILE_SHA=$(get_existing_file_sha)

# Prepare API payload
if [ "$EXISTING_FILE_SHA" == "null" ]; then
    echo "Creating new file..."
    SHA_PART=""
else
    echo "Updating existing file..."
    SHA_PART=", \"sha\": \"$EXISTING_FILE_SHA\""
fi

# To avoid `Argument list too long` error
TMPFILE=$(mktemp)

if [ -n "$EXISTING_FILE_SHA" ]; then
  cat > "$TMPFILE" <<EOF
{
  "message": "$COMMIT_MESSAGE",
  "content": "$ENCODED_CONTENT",
  "branch": "$GITHUB_BRANCH",
  "sha": "$EXISTING_FILE_SHA"
}
EOF
else
  cat > "$TMPFILE" <<EOF
{
  "message": "$COMMIT_MESSAGE",
  "content": "$ENCODED_CONTENT",
  "branch": "$GITHUB_BRANCH"
}
EOF
fi

curl --fail -X PUT \
    $GITHUB_API_URL \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Content-Type: application/json" \
    -H "Accept: application/vnd.github.v3+json" \
    -d @"$TMPFILE"
