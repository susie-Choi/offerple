"""
Collect ALL CVEs from NVD API 2.0 (1999-2024).

This script collects the complete CVE dataset and saves to JSONL.
Estimated: 240,000+ CVEs, will take several days with API rate limits.

Usage:
    python scripts/collection/collect_all_cves.py
    
    # With API key (10x faster):
    export NVD_API_KEY=your_key
    python scripts/collection/collect_all_cves.py
"""
import os
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
import requests
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NVD API configuration
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
API_KEY = os.getenv("NVD_API_KEY")
RESULTS_PER_PAGE = 2000  # Max allowed by NVD API

# Rate limiting
if API_KEY:
    RATE_LIMIT_SLEEP = 0.6  # 50 requests per 30 seconds
    logger.info("Using NVD API key - 50 requests per 30 seconds")
else:
    RATE_LIMIT_SLEEP = 6.0  # 5 requests per 30 seconds
    logger.warning("No API key - 5 requests per 30 seconds (10x slower)")
    logger.warning("Get API key at: https://nvd.nist.gov/developers/request-an-api-key")

# Output
OUTPUT_DIR = Path("data/raw/cve")
OUTPUT_FILE = OUTPUT_DIR / "all_cves_complete.jsonl"
CHECKPOINT_FILE = OUTPUT_DIR / "collection_checkpoint.json"


def load_checkpoint():
    """Load collection progress from checkpoint."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {'start_index': 0, 'collected': 0}


def save_checkpoint(start_index, collected):
    """Save collection progress."""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({
            'start_index': start_index,
            'collected': collected,
            'last_update': datetime.now().isoformat()
        }, f)


def fetch_cves(start_index=0):
    """Fetch CVEs from NVD API with pagination."""
    headers = {}
    if API_KEY:
        headers['apiKey'] = API_KEY
    
    params = {
        'startIndex': start_index,
        'resultsPerPage': RESULTS_PER_PAGE
    }
    
    try:
        response = requests.get(
            NVD_API_URL,
            params=params,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None


def collect_all_cves():
    """Collect all CVEs from NVD."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    start_index = checkpoint['start_index']
    total_collected = checkpoint['collected']
    
    logger.info("=" * 80)
    logger.info("NVD CVE Complete Collection")
    logger.info("=" * 80)
    
    if start_index > 0:
        logger.info(f"Resuming from index {start_index:,} ({total_collected:,} already collected)")
    
    # Open output file in append mode
    mode = 'a' if start_index > 0 else 'w'
    output_file = open(OUTPUT_FILE, mode, encoding='utf-8')
    
    try:
        # First request to get total count
        logger.info("Fetching total CVE count...")
        data = fetch_cves(0)
        
        if not data:
            logger.error("Failed to fetch initial data")
            return
        
        total_results = data.get('totalResults', 0)
        logger.info(f"Total CVEs in NVD: {total_results:,}")
        
        if total_collected >= total_results:
            logger.info("Collection already complete!")
            return
        
        # Calculate estimates
        remaining = total_results - total_collected
        requests_needed = (remaining + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
        estimated_time = requests_needed * RATE_LIMIT_SLEEP
        estimated_hours = estimated_time / 3600
        
        logger.info(f"Remaining: {remaining:,} CVEs")
        logger.info(f"Requests needed: {requests_needed:,}")
        logger.info(f"Estimated time: {estimated_hours:.1f} hours")
        logger.info("=" * 80)
        
        # Progress bar
        pbar = tqdm(
            total=total_results,
            initial=total_collected,
            desc="Collecting CVEs",
            unit="CVE"
        )
        
        current_index = start_index
        consecutive_errors = 0
        
        while current_index < total_results:
            # Fetch batch
            data = fetch_cves(current_index)
            
            if not data:
                consecutive_errors += 1
                if consecutive_errors >= 5:
                    logger.error("Too many consecutive errors, stopping")
                    break
                
                logger.warning(f"Error fetching batch, retrying in 30s...")
                time.sleep(30)
                continue
            
            consecutive_errors = 0
            vulnerabilities = data.get('vulnerabilities', [])
            
            if not vulnerabilities:
                logger.warning(f"No vulnerabilities at index {current_index}")
                break
            
            # Save each CVE
            for vuln in vulnerabilities:
                record = {
                    'source': 'nvd_cve',
                    'collected_at': datetime.now(timezone.utc).isoformat(),
                    'payload': {
                        'vulnerabilities': [vuln],
                        'total_results': 1
                    }
                }
                output_file.write(json.dumps(record, ensure_ascii=False) + '\n')
                total_collected += 1
                pbar.update(1)
            
            # Update progress
            current_index += len(vulnerabilities)
            
            # Save checkpoint every 10,000 CVEs
            if total_collected % 10000 == 0:
                save_checkpoint(current_index, total_collected)
                output_file.flush()
                logger.info(f"Checkpoint saved: {total_collected:,} CVEs collected")
            
            # Rate limiting
            time.sleep(RATE_LIMIT_SLEEP)
        
        pbar.close()
        
        # Final checkpoint
        save_checkpoint(current_index, total_collected)
        
        logger.info("=" * 80)
        logger.info("Collection Complete!")
        logger.info(f"Total collected: {total_collected:,} CVEs")
        logger.info(f"Output file: {OUTPUT_FILE}")
        logger.info(f"File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.warning("\nCollection interrupted by user")
        save_checkpoint(current_index, total_collected)
        logger.info(f"Progress saved: {total_collected:,} CVEs collected")
        logger.info("Run again to resume from checkpoint")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        save_checkpoint(current_index, total_collected)
        
    finally:
        output_file.close()


def main():
    """Main entry point."""
    logger.info("Starting NVD CVE collection...")
    logger.info("This will take several hours/days depending on API key")
    logger.info("Press Ctrl+C to pause (progress will be saved)")
    logger.info("")
    
    collect_all_cves()


if __name__ == "__main__":
    main()
