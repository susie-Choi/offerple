# This Week: RoKRAT Detection - Getting Started

## Goal
**Collect first RoKRAT samples and build basic steganography detector**

## Day 1: VirusTotal Setup & Sample Collection

### Step 1: Get VirusTotal API Access
```bash
# Sign up for VirusTotal account
# https://www.virustotal.com/gui/join-us

# Get API key from:
# https://www.virustotal.com/gui/my-apikey

# Add to .env
echo "VIRUSTOTAL_API_KEY=your_key_here" >> .env
```

### Step 2: Search for RoKRAT Samples
```python
# scripts/collect_rokrat_samples.py

import requests
import json
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class RoKRATCollector:
    def __init__(self):
        self.api_key = os.getenv('VIRUSTOTAL_API_KEY')
        self.base_url = "https://www.virustotal.com/api/v3"
        self.headers = {"x-apikey": self.api_key}
    
    def search_rokrat(self):
        """Search for RoKRAT samples on VirusTotal"""
        
        # Search queries
        queries = [
            'tag:rokrat',
            'tag:apt37',
            'tag:scarcruft',
            'tag:group123',
            'rokrat steganography',
            'north korea apt'
        ]
        
        all_samples = []
        
        for query in queries:
            print(f"Searching: {query}")
            
            url = f"{self.base_url}/intelligence/search"
            params = {
                'query': query,
                'limit': 40  # Free tier limit
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                samples = data.get('data', [])
                print(f"  Found {len(samples)} samples")
                all_samples.extend(samples)
            else:
                print(f"  Error: {response.status_code}")
        
        return all_samples
    
    def get_sample_details(self, file_hash):
        """Get detailed analysis of a sample"""
        url = f"{self.base_url}/files/{file_hash}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def download_sample(self, file_hash, output_dir='data/apt_samples'):
        """Download sample file (requires premium API)"""
        # Note: Free tier doesn't allow downloads
        # Alternative: Use Hybrid Analysis, Malware Bazaar
        
        url = f"{self.base_url}/files/{file_hash}/download"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            output_path = Path(output_dir) / f"{file_hash}.bin"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded: {output_path}")
            return output_path
        else:
            print(f"Download failed: {response.status_code}")
            return None

# Run collection
collector = RoKRATCollector()
samples = collector.search_rokrat()

print(f"\nTotal samples found: {len(samples)}")

# Save metadata
output_file = Path('data/apt_samples/rokrat_metadata.json')
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, 'w') as f:
    json.dump(samples, f, indent=2)

print(f"Metadata saved to: {output_file}")
```

### Step 3: Alternative Sources (If VirusTotal Limited)
```python
# Malware Bazaar (free, no API key needed)
class MalwareBazaarCollector:
    def search_rokrat(self):
        url = "https://mb-api.abuse.ch/api/v1/"
        
        data = {
            'query': 'get_taginfo',
            'tag': 'RoKRAT',
            'limit': 100
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            return response.json()
        return None

# Hybrid Analysis (free tier available)
class HybridAnalysisCollector:
    def search_rokrat(self):
        # Similar to VirusTotal
        # https://www.hybrid-analysis.com/
        pass
```

## Day 2: Analyze RoKRAT Steganography

### Step 1: Extract Images from Samples
```python
# scripts/extract_apt_images.py

import zipfile
import rarfile
from pathlib import Path
from PIL import Image

class APTImageExtractor:
    def __init__(self):
        self.image_extensions = {'.bmp', '.png', '.jpg', '.jpeg', '.gif'}
    
    def extract_from_sample(self, sample_path):
        """Extract images from APT sample"""
        images = []
        
        # If it's an archive
        if sample_path.suffix == '.zip':
            images = self.extract_from_zip(sample_path)
        elif sample_path.suffix == '.rar':
            images = self.extract_from_rar(sample_path)
        
        # If it's an image itself
        elif sample_path.suffix in self.image_extensions:
            images = [sample_path]
        
        return images
    
    def extract_from_zip(self, zip_path):
        images = []
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for file_info in zf.filelist:
                if Path(file_info.filename).suffix in self.image_extensions:
                    # Extract image
                    extracted = zf.extract(file_info, 'temp_extract')
                    images.append(Path(extracted))
        
        return images

# Test
extractor = APTImageExtractor()
# Test on collected samples
```

### Step 2: Build Steganography Detector
```python
# scripts/detect_steganography.py

import numpy as np
from PIL import Image
from scipy import stats

class SteganographyDetector:
    """Detect LSB steganography in images"""
    
    def analyze_lsb_entropy(self, image_path):
        """Analyze LSB entropy for steganography detection"""
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Extract LSBs
        lsbs = img_array & 1
        
        # Calculate entropy
        entropy = self.calculate_entropy(lsbs.flatten())
        
        # Normal images have low LSB entropy (~0.5)
        # Steganography increases entropy (>0.7)
        
        return {
            'entropy': entropy,
            'suspicious': entropy > 0.7,
            'confidence': min((entropy - 0.5) / 0.3, 1.0) if entropy > 0.5 else 0
        }
    
    def calculate_entropy(self, data):
        """Calculate Shannon entropy"""
        value, counts = np.unique(data, return_counts=True)
        probabilities = counts / len(data)
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        return entropy
    
    def chi_square_test(self, image_path):
        """Chi-square test for LSB steganography"""
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Analyze LSB distribution
        lsbs = img_array & 1
        
        # Expected: 50% zeros, 50% ones
        observed = np.bincount(lsbs.flatten(), minlength=2)
        expected = np.array([len(lsbs.flatten()) / 2] * 2)
        
        # Chi-square test
        chi2, p_value = stats.chisquare(observed, expected)
        
        return {
            'chi2': chi2,
            'p_value': p_value,
            'suspicious': p_value < 0.05  # Significant deviation
        }
    
    def detect(self, image_path):
        """Combined steganography detection"""
        results = {
            'image': str(image_path),
            'lsb_entropy': self.analyze_lsb_entropy(image_path),
            'chi_square': self.chi_square_test(image_path)
        }
        
        # Overall suspicion score
        suspicion_score = (
            results['lsb_entropy']['confidence'] * 0.6 +
            (1 - results['chi_square']['p_value']) * 0.4
        )
        
        results['suspicion_score'] = suspicion_score
        results['likely_steganography'] = suspicion_score > 0.7
        
        return results

# Test
detector = SteganographyDetector()

# Test on known RoKRAT images
test_image = 'data/apt_samples/rokrat_image.bmp'
result = detector.detect(test_image)

print(f"Suspicion score: {result['suspicion_score']:.2f}")
print(f"Likely steganography: {result['likely_steganography']}")
```

## Day 3: Extract C&C Addresses

### C&C Server Extractor
```python
# scripts/extract_cc_servers.py

import re
from PIL import Image
import numpy as np

class CCServerExtractor:
    """Extract C&C server addresses from steganography"""
    
    def extract_lsb_payload(self, image_path):
        """Extract LSB-encoded payload"""
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Extract LSBs
        lsbs = img_array & 1
        
        # Convert to bytes
        lsb_bits = lsbs.flatten()
        
        # Group into bytes
        payload_bytes = []
        for i in range(0, len(lsb_bits), 8):
            if i + 8 <= len(lsb_bits):
                byte_bits = lsb_bits[i:i+8]
                byte_value = int(''.join(map(str, byte_bits)), 2)
                payload_bytes.append(byte_value)
        
        # Convert to string
        try:
            payload = bytes(payload_bytes).decode('utf-8', errors='ignore')
            return payload
        except:
            return None
    
    def extract_cc_addresses(self, payload):
        """Extract C&C server addresses from payload"""
        if not payload:
            return []
        
        # Patterns for C&C addresses
        patterns = [
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',  # IP addresses
            r'https?://[^\s]+',  # URLs
            r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Domains
        ]
        
        cc_addresses = []
        for pattern in patterns:
            matches = re.findall(pattern, payload)
            cc_addresses.extend(matches)
        
        return list(set(cc_addresses))  # Remove duplicates
    
    def extract(self, image_path):
        """Extract C&C addresses from image"""
        # Extract payload
        payload = self.extract_lsb_payload(image_path)
        
        if not payload:
            return []
        
        # Extract C&C addresses
        cc_addresses = self.extract_cc_addresses(payload)
        
        return {
            'payload_length': len(payload),
            'cc_addresses': cc_addresses,
            'payload_preview': payload[:200]  # First 200 chars
        }

# Test
extractor = CCServerExtractor()
result = extractor.extract('data/apt_samples/rokrat_image.bmp')

print(f"C&C addresses found: {result['cc_addresses']}")
```

## Day 4: Build RoKRAT Signature Database

### Signature Generator
```python
# scripts/generate_rokrat_signatures.py

import json
from pathlib import Path
import hashlib

class RoKRATSignatureGenerator:
    def __init__(self):
        self.signatures = {
            'file_hashes': [],
            'cc_servers': [],
            'lsb_patterns': [],
            'code_patterns': [],
            'behavioral_patterns': []
        }
    
    def generate_from_samples(self, sample_dir):
        """Generate signatures from RoKRAT samples"""
        sample_dir = Path(sample_dir)
        
        for sample_file in sample_dir.glob('*'):
            print(f"Analyzing: {sample_file.name}")
            
            # File hash
            file_hash = self.calculate_hash(sample_file)
            self.signatures['file_hashes'].append(file_hash)
            
            # Extract images
            images = self.extract_images(sample_file)
            
            for img in images:
                # Steganography analysis
                stego_result = detector.detect(img)
                
                if stego_result['likely_steganography']:
                    # Extract C&C
                    cc_result = extractor.extract(img)
                    self.signatures['cc_servers'].extend(cc_result['cc_addresses'])
                    
                    # LSB pattern
                    lsb_pattern = self.extract_lsb_pattern(img)
                    self.signatures['lsb_patterns'].append(lsb_pattern)
        
        # Remove duplicates
        self.signatures['cc_servers'] = list(set(self.signatures['cc_servers']))
        
        return self.signatures
    
    def calculate_hash(self, file_path):
        """Calculate SHA256 hash"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def save_signatures(self, output_file='data/signatures/rokrat_signatures.json'):
        """Save signatures to file"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.signatures, f, indent=2)
        
        print(f"Signatures saved to: {output_path}")
        print(f"  File hashes: {len(self.signatures['file_hashes'])}")
        print(f"  C&C servers: {len(self.signatures['cc_servers'])}")
        print(f"  LSB patterns: {len(self.signatures['lsb_patterns'])}")

# Generate signatures
generator = RoKRATSignatureGenerator()
signatures = generator.generate_from_samples('data/apt_samples')
generator.save_signatures()
```

## Day 5: Test Detection System

### Integration Test
```python
# scripts/test_rokrat_detection.py

class RoKRATDetectionSystem:
    def __init__(self):
        self.stego_detector = SteganographyDetector()
        self.cc_extractor = CCServerExtractor()
        self.signatures = self.load_signatures()
    
    def load_signatures(self):
        with open('data/signatures/rokrat_signatures.json') as f:
            return json.load(f)
    
    def detect(self, package_or_file):
        """Detect RoKRAT in package or file"""
        results = {
            'file': str(package_or_file),
            'detections': []
        }
        
        # 1. File hash check
        file_hash = self.calculate_hash(package_or_file)
        if file_hash in self.signatures['file_hashes']:
            results['detections'].append({
                'type': 'file_hash_match',
                'confidence': 1.0,
                'details': 'Known RoKRAT sample'
            })
        
        # 2. Steganography detection
        if self.is_image(package_or_file):
            stego_result = self.stego_detector.detect(package_or_file)
            
            if stego_result['likely_steganography']:
                results['detections'].append({
                    'type': 'steganography',
                    'confidence': stego_result['suspicion_score'],
                    'details': stego_result
                })
                
                # 3. C&C extraction
                cc_result = self.cc_extractor.extract(package_or_file)
                
                for cc_addr in cc_result['cc_addresses']:
                    if cc_addr in self.signatures['cc_servers']:
                        results['detections'].append({
                            'type': 'known_cc_server',
                            'confidence': 1.0,
                            'details': f'Known RoKRAT C&C: {cc_addr}'
                        })
        
        # Overall risk score
        if results['detections']:
            max_confidence = max(d['confidence'] for d in results['detections'])
            results['risk_score'] = max_confidence
            results['classification'] = self.classify_risk(max_confidence)
        else:
            results['risk_score'] = 0.0
            results['classification'] = 'CLEAN'
        
        return results
    
    def classify_risk(self, score):
        if score >= 0.9:
            return 'CONFIRMED_ROKRAT'
        elif score >= 0.7:
            return 'LIKELY_APT'
        elif score >= 0.5:
            return 'SUSPICIOUS'
        else:
            return 'LOW_RISK'

# Test on known samples
detector = RoKRATDetectionSystem()

# Test 1: Known RoKRAT sample
test1 = detector.detect('data/apt_samples/known_rokrat.bmp')
print(f"Test 1: {test1['classification']} (score: {test1['risk_score']:.2f})")

# Test 2: Clean image
test2 = detector.detect('data/clean_samples/normal_image.png')
print(f"Test 2: {test2['classification']} (score: {test2['risk_score']:.2f})")

# Calculate accuracy
print(f"\nAccuracy on known samples: {calculate_accuracy()}")
```

## Day 6-7: Documentation & Planning

### Document Findings
```python
# Create research log
research_log = {
    'week_1_summary': {
        'samples_collected': 30,
        'steganography_detected': 15,
        'cc_servers_extracted': 8,
        'signatures_generated': 30,
        'detection_accuracy': 0.93
    },
    'key_findings': [
        'RoKRAT primarily uses BMP files for steganography',
        'LSB entropy > 0.75 is strong indicator',
        'C&C addresses often use dynamic DNS',
        'Some samples use multi-layer encoding'
    ],
    'next_steps': [
        'Collect more samples (target: 50)',
        'Test on legitimate packages',
        'Build scanning infrastructure',
        'Plan large-scale scan'
    ]
}

# Save log
with open('data/research_log_week1.json', 'w') as f:
    json.dump(research_log, f, indent=2)
```

### Plan Next Week
```markdown
# Week 2 Plan

## Goals
1. Collect 20 more RoKRAT samples (total: 50)
2. Test detection on 1,000 legitimate packages
3. Calculate false positive rate
4. Build scanning infrastructure

## Tasks
- [ ] Expand sample collection (Hybrid Analysis, Malware Bazaar)
- [ ] Download top 1,000 PyPI packages
- [ ] Scan for APT indicators
- [ ] Manual verification of findings
- [ ] Refine detection thresholds
```

## End of Week Checklist

- [ ] VirusTotal API set up
- [ ] 10-30 RoKRAT samples collected
- [ ] Steganography detector working
- [ ] C&C extractor working
- [ ] Signature database created
- [ ] Detection system tested
- [ ] Accuracy > 90% on known samples
- [ ] Research log documented

## Success Criteria

✅ **Minimum**: 10 RoKRAT samples, basic detector working
✅ **Good**: 20 samples, 90% accuracy, C&C extraction working
✅ **Excellent**: 30+ samples, 95% accuracy, comprehensive signatures

## Resources

### APT Intelligence Sources
- [MITRE ATT&CK - APT37](https://attack.mitre.org/groups/G0067/)
- [AhnLab ASEC Blog](https://asec.ahnlab.com/en/)
- [KISA Alerts](https://www.krcert.or.kr/krcert/main.do)
- [Malware Bazaar](https://bazaar.abuse.ch/)

### Tools
- [VirusTotal](https://www.virustotal.com/)
- [Hybrid Analysis](https://www.hybrid-analysis.com/)
- [Stegdetect](http://www.outguess.org/detection.php)

### Papers
- "RoKRAT: The Return of the Konni APT" (Talos Intelligence)
- "Group123: Tracking a North Korean APT" (Cisco Talos)
- "APT37: The Overlooked North Korean Actor" (FireEye)

---

**Let's catch some APT malware! 🎯**
