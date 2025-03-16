#!/bin/bash

# Script to scrape only the newly added universities and update the vector database
# without reprocessing existing university data

echo "====================================================================="
echo "Starting targeted scraping for 50 newly added universities"
echo "====================================================================="

# Array of new universities (50 institutions - Batch 3)
universities=(
  "University of Windsor"
  "Georgian College"
  "Fanshawe College"
  "Kwantlen Polytechnic University"
  "Northern Alberta Institute of Technology"
  "Southern Alberta Institute of Technology"
  "Mohawk College"
  "Centennial College"
  "George Brown College"
  "Durham College"
  "University of Lethbridge"
  "Trinity Western University"
  "University of Northern British Columbia"
  "Nipissing University"
  "Ontario Tech University"
  "University of the Fraser Valley"
  "Laurentian University"
  "Royal Roads University"
  "OCAD University"
  "Red Deer Polytechnic"
  "Douglas College"
  "Mount Saint Vincent University"
  "Saint Mary's University"
  "Université de Sherbrooke"
  "Camosun College"
  "Université de Moncton"
  "Saskatchewan Polytechnic"
  "Redeemer University"
  "Langara College"
  "Nova Scotia Community College"
  "Lambton College"
  "College of the North Atlantic"
  "Niagara College"
  "Confederation College"
  "Holland College"
  "Northern College"
  "Medicine Hat College"
  "St. Clair College"
  "Lakeland College"
  "University of King's College"
  "Bow Valley College"
  "Lethbridge College"
  "Okanagan College"
  "College of New Caledonia"
  "New Brunswick Community College"
  "Selkirk College"
  "St. Lawrence College"
  "Aurora College"
  "Nunavut Arctic College"
  "Yukon University"
)

# Restart API to ensure clean state
echo "Restarting API to ensure clean state..."
./start-kevin.sh -a restart -s api

# First, let's verify all universities are in the config file
echo "Verifying all universities are in config.yaml..."
cat > verify_config.py << 'EOF'
#!/usr/bin/env python3
import yaml
import sys

def verify_universities(university_list):
    # Load config
    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Get all university names from config
    config_universities = [u.get('name') for u in config.get('universities', [])]
    
    # Check each university in our list
    missing = []
    found = []
    
    for uni in university_list:
        if uni in config_universities:
            found.append(uni)
        else:
            # Try with similar names
            similar = [c_uni for c_uni in config_universities if uni.lower() in c_uni.lower() or c_uni.lower() in uni.lower()]
            if similar:
                print(f"Warning: '{uni}' not found exactly, but similar names exist: {similar}")
                found.append(uni)
            else:
                missing.append(uni)
    
    print(f"Found {len(found)} universities in config:")
    for uni in found:
        print(f"  - {uni}")
    
    if missing:
        print(f"\nMissing {len(missing)} universities from config:")
        for uni in missing:
            print(f"  - {uni}")
        return False
    
    return True

if __name__ == "__main__":
    universities = sys.argv[1:]
    if not universities:
        print("No universities provided to verify")
        sys.exit(1)
    
    if not verify_universities(universities):
        print("Some universities are missing from config.yaml")
        sys.exit(1)
EOF

# Make the verification script executable
chmod +x verify_config.py

# Run verification
if ! python verify_config.py "${universities[@]}"; then
    echo "Please check that all universities are correctly added to config.yaml"
    echo "Fix any missing universities before continuing"
    exit 1
fi

# Create a Python script to handle the scraping and saving documents
echo "Creating Python helper script for scraping and saving..."
cat > scrape_and_save.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
import os
import yaml
import json
import hashlib
import time
import random
import traceback
import signal
from datetime import datetime
from src.data.scraper import WebScraper
from langchain_core.documents import Document
from bs4 import BeautifulSoup

# Ensure data/raw directory exists
RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

# Setup timeout handling
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Scraping timed out")

def sanitize_filename(name):
    """Create a safe filename from a university name"""
    return name.lower().replace(" ", "_").replace("'", "").replace(",", "").replace("&", "and").replace("+", "plus")

def save_document_to_file(doc, university_name):
    """Save a document to a text file in the data/raw directory"""
    # Create a unique filename using a hash of the URL
    url = doc.get('url', 'unknown')
    url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
    file_name = f"{sanitize_filename(university_name)}_{url_hash}.txt"
    file_path = os.path.join(RAW_DIR, file_name)
    
    # Check if file already exists (to avoid duplicates)
    if os.path.exists(file_path):
        return None
    
    # Prepare metadata
    metadata = {
        "source": url,
        "university": university_name,
        "scraped_at": datetime.now().isoformat(),
    }
    
    # Combine metadata and content
    content = doc.get('content', '')
    if not content:
        return None
        
    # Clean content (basic HTML cleanup if needed)
    if "<html" in content.lower():
        soup = BeautifulSoup(content, 'html.parser')
        content = soup.get_text()
    
    # Format the file with metadata header and content
    file_content = f"""---
source: {url}
university: {university_name}
scraped_at: {datetime.now().isoformat()}
---

{content}
"""
    
    # Write to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(file_content)
    
    print(f"Saved document to {file_path}")
    return file_path

async def find_university_in_config(university_name, config):
    """Find a university in config, with fuzzy matching if needed"""
    # First try exact match
    universities = config.get('universities', [])
    university = next((u for u in universities if u.get('name') == university_name), None)
    
    if university:
        return university
    
    # Try case-insensitive match
    university = next((u for u in universities if u.get('name').lower() == university_name.lower()), None)
    
    if university:
        print(f"Found case-insensitive match for '{university_name}': '{university['name']}'")
        return university
    
    # Try substring match as last resort
    matches = [(u, u.get('name')) for u in universities if university_name.lower() in u.get('name', '').lower() 
               or u.get('name', '').lower() in university_name.lower()]
    
    if matches:
        closest = matches[0]
        print(f"Using fuzzy match for '{university_name}': '{closest[1]}'")
        return closest[0]
    
    return None

async def scrape_university_async(university_name, config_path="config.yaml", max_pages=10, max_retries=3):
    """Scrape a university and save documents to disk with page limit for large batches"""
    for retry in range(max_retries):
        try:
            # Load config
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Initialize scraper with reduced page limit for bulk scraping
            scraper = WebScraper(config_path, max_pages=max_pages, quiet_mode=False)
            
            # Find the university in the configuration with improved matching
            university = await find_university_in_config(university_name, config)
            
            if not university:
                print(f"ERROR: University '{university_name}' not found in config, even with fuzzy matching")
                return 0
            
            print(f"Scraping {university.get('name')}...")
            print(f"URL: {university.get('base_url')}")
            print(f"Focus URLs: {university.get('focus_urls')}")
            
            # Scrape the university
            documents = await scraper.scrape_university(university)
            
            print(f"Scraped {len(documents)} documents from {university_name}")
            
            # Save documents to files
            saved_files = []
            for doc in documents:
                file_path = save_document_to_file(doc, university_name)
                if file_path:
                    saved_files.append(file_path)
            
            print(f"Saved {len(saved_files)}/{len(documents)} documents from {university_name}")
            return len(saved_files)
        except TimeoutError:
            print(f"Scraping timed out for {university_name}")
            return 0
        except Exception as e:
            print(f"Error details: {type(e).__name__}: {str(e)}")
            print("Traceback:")
            traceback.print_exc()
            
            if retry < max_retries - 1:
                print(f"Error scraping {university_name}, retrying ({retry+1}/{max_retries})")
                # Add exponential backoff with jitter
                sleep_time = (2 ** retry) + random.random()
                print(f"Waiting {sleep_time:.2f}s before retry...")
                time.sleep(sleep_time)
            else:
                print(f"Failed to scrape {university_name} after {max_retries} attempts")
                return 0

async def main():
    if len(sys.argv) < 2:
        print("Please provide a university name")
        return
    
    university_name = sys.argv[1]
    
    # Set up timeout (20 minutes)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(1200)  # 1200 seconds = 20 minutes
    
    try:
        # For batch processing, use a smaller page limit per university
        max_pages = 10  # Reduced for large batches
        result = await scrape_university_async(university_name, max_pages=max_pages)
        
        # Turn off the alarm
        signal.alarm(0)
        
        # Return success or failure to bash script
        sys.exit(0 if result > 0 else 1)
    except TimeoutError:
        print(f"ERROR: Scraping of {university_name} timed out after 20 minutes")
        sys.exit(2)
    finally:
        # Ensure alarm is cancelled
        signal.alarm(0)

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Make the helper script executable
chmod +x scrape_and_save.py

# Create a progress counter
total_universities=${#universities[@]}
current=0
successful=0
failed=0

# Update frequency - process this many universities before saving progress
batch_size=10
current_batch=0

# Create a log directory for detailed logs
mkdir -p logs/scraping
echo "University scraping logs will be saved in logs/scraping/"

# Scrape each university using the helper script
for university in "${universities[@]}"; do
  current=$((current + 1))
  echo ""
  echo "====================================================================="
  echo "[$current/$total_universities] Scraping $university..."
  echo "====================================================================="
  
  log_file="logs/scraping/${university// /_}.log"
  
  # Run the scraper (using Python's internal timeout instead of 'timeout' command)
  python scrape_and_save.py "$university" > >(tee -a "$log_file") 2>&1
  exit_code=$?
  
  if [ $exit_code -eq 0 ]; then
    successful=$((successful + 1))
    echo "SUCCESS: Scraped $university successfully"
  else
    failed=$((failed + 1))
    if [ $exit_code -eq 2 ]; then
      echo "WARNING: Scraping timed out for $university (timeout exceeded)"
    else
      echo "WARNING: Scraping failed for $university with exit code $exit_code"
    fi
  fi
  
  # Progress report
  echo "Progress: $successful successful, $failed failed, $((total_universities - current)) remaining"
  
  # Add a small delay to ensure processes don't overlap and to prevent rate limiting
  sleep_time=$((5 + RANDOM % 5))  # Random sleep between 5-10 seconds
  echo "Waiting ${sleep_time}s before next university..."
  sleep $sleep_time
  
  # Periodically update the vector database to avoid losing progress
  current_batch=$((current_batch + 1))
  if [ $current_batch -eq $batch_size ] && [ $current -lt $total_universities ]; then
    echo ""
    echo "====================================================================="
    echo "Intermediate update: Processing documents scraped so far..."
    echo "====================================================================="
    
    # Create and run the training script
    cat > train_intermediate.py << 'EOF'
#!/usr/bin/env python3
import os
import yaml
from src.core.document_processor import DocumentProcessor
from src.models.trainer import Trainer

def train_model(config_path="config.yaml"):
    """Train the model using all documents in the data/raw directory"""
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize the document processor
    doc_processor = DocumentProcessor(config)
    
    # Get all documents
    documents = doc_processor.get_all_documents()
    print(f"Loaded {len(documents)} documents for training")
    
    # Initialize the trainer
    trainer = Trainer(doc_processor)
    
    # Train the model
    trainer.train()
    
    print("Training completed successfully")

if __name__ == "__main__":
    train_model()
EOF
    chmod +x train_intermediate.py
    python train_intermediate.py
    rm train_intermediate.py
    
    current_batch=0
    echo "Continuing with remaining universities..."
  fi
done

echo ""
echo "====================================================================="
echo "Summary of scraping results:"
echo "====================================================================="
echo "Total universities: $total_universities"
echo "Successfully scraped: $successful"
echo "Failed to scrape: $failed"
echo "See detailed logs in logs/scraping/ directory"

# Now create a training script that processes all documents
echo "Creating Python helper script for final training..."
cat > train_all.py << 'EOF'
#!/usr/bin/env python3
import os
import yaml
from src.core.document_processor import DocumentProcessor
from src.models.trainer import Trainer

def train_model(config_path="config.yaml"):
    """Train the model using all documents in the data/raw directory"""
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize the document processor
    doc_processor = DocumentProcessor(config)
    
    # Get all documents
    documents = doc_processor.get_all_documents()
    print(f"Loaded {len(documents)} documents for training")
    
    # Initialize the trainer
    trainer = Trainer(doc_processor)
    
    # Train the model
    trainer.train()
    
    print("Training completed successfully")

if __name__ == "__main__":
    train_model()
EOF

# Make the training helper script executable
chmod +x train_all.py

# Update the vector database with new data if any scraping was successful
if [ $successful -gt 0 ]; then
  echo ""
  echo "====================================================================="
  echo "Training model using all documents in data/raw directory..."
  echo "====================================================================="
  python train_all.py
  
  echo ""
  echo "====================================================================="
  echo "Process complete! $successful of $total_universities universities have been added to the vector database."
  echo "====================================================================="
else
  echo ""
  echo "====================================================================="
  echo "ERROR: No universities were successfully scraped. Skipping training."
  echo "Please check the logs in logs/scraping/ directory for details."
  echo "====================================================================="
fi

# Clean up temporary scripts
rm scrape_and_save.py train_all.py verify_config.py 