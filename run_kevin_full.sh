#!/bin/bash
echo "Starting Kevin Web Scraper and Web Interface"
echo "First, running the web scraper to update the knowledge base..."
source kevin/bin/activate
kevin --mode scrape
echo "Now starting the web interface..."
kevin
