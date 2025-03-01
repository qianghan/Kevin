#!/bin/bash
# run_scrape_quiet.sh - Run the scraper with minimal logging but keep progress bars

# Check if university argument is provided
if [ "$1" != "" ]; then
  echo "Running scraper for $1 with minimal logging..."
  python src/main.py scrape --quiet --university "$1" "$@"
else
  echo "Running scraper for all universities with minimal logging..."
  python src/main.py scrape --quiet "$@"
fi 