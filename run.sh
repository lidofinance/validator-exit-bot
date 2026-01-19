#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded .env file"
else
    echo "⚠️  Warning: .env file not found"
fi

# Run the bot
cd "$(dirname "$0")"
poetry run python src/main.py

