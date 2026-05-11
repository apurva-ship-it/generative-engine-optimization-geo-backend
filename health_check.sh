#!/usr/bin/env bash

# Simple health check script for CI environments without Python interpreter.
# Usage: ./health_check.sh http://localhost:8000/health

URL=${1:-http://localhost:8000/health}

if command -v curl >/dev/null 2>&1; then
  response=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
  if [ "$response" -eq 200 ]; then
    echo "Health check passed (HTTP $response)"
    exit 0
  else
    echo "Health check failed (HTTP $response)"
    exit 1
  fi
else
  echo "curl is not installed. Please install curl to run the health check."
  exit 1
fi
