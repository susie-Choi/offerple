# This Week: Getting Started

## Goal
**Set up infrastructure and validate approach with 10 packages**

## Day 1-2: Environment Setup

### Install Dependencies
```bash
# Core dependencies
pip install requests beautifulsoup4 gitpython pillow
pip install openai anthropic  # For VLM APIs
pip install pandas numpy matplotlib seaborn
pip install tqdm python-dotenv

# Optional: For advanced analysis
pip install opencv-python scikit-image
pip install stegano pyzbar qrcode
```

### Set Up API Keys
```bash
# Create .env file
cat > .env << EOF
# OpenAI (for GPT-4V)
OPENAI_API_KEY=your_key_here

# GitHub (for repo access)
GITHUB_TOKEN=your_token_here

# Optional: Anthropic (for Claude)
ANTHROPIC_API_KEY=your_key_here
EOF
```

### Create Project Structure
```bash
mkdir -p data/{raw,processed,results}
mkdir -p data/raw/{images,metadata,repositories}
mkdir -p data/processed/{suspicious,verified,false_positives}
mkdir -p logs
mkdir -p notebooks  # For analysis
```

## Day 3-4: Build Basic Analyzer

### Step 1: Package Metadata Collector
```python
# scripts/collect_package_metadata.py

import requests
import json
from pathlib import Path

class PyPICollector:
    def get_package_info(self, package_name):
        """Get package metadata from PyPI"""
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'name': package_name,
                'version': data['info']['version'],
                'description': data['info']['summary'],
                'home_page': data['info']['home_page'],
                'project_urls': data['info'].get('project_urls', {}),
                'author': data['info']['author'],
                'downloads': self.get_download_stats(package_name)
            }
        return None
    
    def get_top_packages(self, count=1000):
        """Get top N packages by downloads"""
        # Use pypistats or hugovk's top-pypi-packages
        url = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json"
        response = requests.get(url)
        data = response.json()
        
        return [row['project'] for row in data['rows'][:count]]

# Test
collector = PyPICollector()
top_10 = collector.get_top_packages(10)
print(f"Top 10 packages: {top_10}")

for pkg in top_10[:3]:
    info = collector.get_package_info(pkg)
    print(f"\n{pkg}: {info['description']}")
```

### Step 2: Image Extractor
```python
# scripts/extract_images.py

import git
from pathlib import Path
from PIL import Image
import requests
from io import BytesIO

class ImageExtractor:
    def __init__(self, output_dir='data/raw/images'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
    
    def extract_from_repo(self, repo_url, package_name):
        """Clone repo and extract all images"""
        # Clone to temp directory
        repo_path = Path(f'temp_repos/{package_name}')
        
        try:
            if repo_path.exists():
                repo = git.Repo(repo_path)
                repo.remotes.origin.pull()
            else:
                repo = git.Repo.clone_from(repo_url, repo_path)
            
            # Find all images
            images = []
            for file_path in repo_path.rglob('*'):
                if file_path.suffix.lower() in self.image_extensions:
                    images.append({
                        'path': str(file_path),
                        'relative_path': str(file_path.relative_to(repo_path)),
                        'size': file_path.stat().st_size,
                        'extension': file_path.suffix
                    })
            
            return images
            
        except Exception as e:
            print(f"Error extracting images from {repo_url}: {e}")
            return []
    
    def extract_from_readme(self, readme_url):
        """Extract images from README markdown"""
        response = requests.get(readme_url)
        content = response.text
        
        # Find markdown images: ![alt](url)
        import re
        pattern = r'!\[.*?\]\((.*?)\)'
        image_urls = re.findall(pattern, content)
        
        return image_urls

# Test
extractor = ImageExtractor()
# Test with a known package
images = extractor.extract_from_repo('https://github.com/psf/requests', 'requests')
print(f"Found {len(images)} images in requests package")
```

### Step 3: GPT-4V Analyzer
```python
# scripts/analyze_with_gpt4v.py

import openai
import base64
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class GPT4VAnalyzer:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def analyze_image(self, image_path, package_context):
        """Analyze image for security threats"""
        
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        prompt = f"""
Analyze this image from the package '{package_context['name']}' for security threats.

Package context:
- Name: {package_context['name']}
- Description: {package_context.get('description', 'N/A')}
- Official website: {package_context.get('home_page', 'N/A')}

Look for:
1. Fake security badges (check if URL matches package)
2. Malicious QR codes (suspicious URLs)
3. Misleading screenshots or endorsements
4. Signs of steganography (unusual patterns)
5. Typosquatting indicators

Respond in JSON format:
{{
    "risk_score": 0.0-1.0,
    "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
    "threats_detected": ["list of threats"],
    "reasoning": "detailed explanation",
    "suspicious_elements": ["specific elements that are suspicious"]
}}
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content

# Test
analyzer = GPT4VAnalyzer()
# Test with a sample image
result = analyzer.analyze_image(
    'sample_badge.png',
    {'name': 'test-package', 'description': 'Test package'}
)
print(result)
```

## Day 5: Test on 10 Packages

### Create Test Script
```python
# scripts/test_pipeline.py

from collect_package_metadata import PyPICollector
from extract_images import ImageExtractor
from analyze_with_gpt4v import GPT4VAnalyzer
import json
from pathlib import Path
from datetime import datetime

def test_pipeline(num_packages=10):
    """Test complete pipeline on N packages"""
    
    # Initialize
    collector = PyPICollector()
    extractor = ImageExtractor()
    analyzer = GPT4VAnalyzer()
    
    # Get top packages
    packages = collector.get_top_packages(num_packages)
    
    results = []
    total_cost = 0
    
    for pkg_name in packages:
        print(f"\n{'='*60}")
        print(f"Analyzing: {pkg_name}")
        print(f"{'='*60}")
        
        # Get metadata
        metadata = collector.get_package_info(pkg_name)
        if not metadata:
            print(f"  ❌ Could not fetch metadata")
            continue
        
        # Extract images
        repo_url = metadata.get('project_urls', {}).get('Source')
        if not repo_url:
            repo_url = metadata.get('home_page')
        
        if not repo_url:
            print(f"  ❌ No repository URL found")
            continue
        
        images = extractor.extract_from_repo(repo_url, pkg_name)
        print(f"  📸 Found {len(images)} images")
        
        # Analyze each image
        suspicious_images = []
        for img in images[:5]:  # Limit to 5 images per package for testing
            try:
                analysis = analyzer.analyze_image(img['path'], metadata)
                
                # Parse JSON response
                import json
                analysis_data = json.loads(analysis)
                
                if analysis_data['risk_score'] > 0.5:
                    suspicious_images.append({
                        'image': img,
                        'analysis': analysis_data
                    })
                    print(f"  ⚠️  Suspicious: {img['relative_path']} (risk: {analysis_data['risk_score']})")
                
                total_cost += 0.01  # Approximate cost per image
                
            except Exception as e:
                print(f"  ❌ Error analyzing {img['relative_path']}: {e}")
        
        results.append({
            'package': pkg_name,
            'metadata': metadata,
            'total_images': len(images),
            'suspicious_images': suspicious_images
        })
    
    # Save results
    output_file = Path('data/results') / f'test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'num_packages': num_packages,
            'total_cost': total_cost,
            'results': results
        }, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Packages analyzed: {len(results)}")
    print(f"Suspicious images found: {sum(len(r['suspicious_images']) for r in results)}")
    print(f"Estimated cost: ${total_cost:.2f}")
    print(f"Results saved to: {output_file}")
    
    return results

# Run test
if __name__ == '__main__':
    results = test_pipeline(10)
```

### Run Test
```bash
python scripts/test_pipeline.py
```

## Day 6-7: Analyze Results and Plan Next Steps

### Review Test Results
```python
# notebooks/analyze_test_results.ipynb

import json
import pandas as pd
import matplotlib.pyplot as plt

# Load results
with open('data/results/test_run_XXXXXX.json') as f:
    data = json.load(f)

# Create DataFrame
results = []
for pkg in data['results']:
    for img in pkg['suspicious_images']:
        results.append({
            'package': pkg['package'],
            'image': img['image']['relative_path'],
            'risk_score': img['analysis']['risk_score'],
            'risk_level': img['analysis']['risk_level'],
            'threats': ', '.join(img['analysis']['threats_detected'])
        })

df = pd.DataFrame(results)

# Analysis
print(f"Total suspicious images: {len(df)}")
print(f"\nRisk level distribution:")
print(df['risk_level'].value_counts())

print(f"\nMost common threats:")
all_threats = []
for threats in df['threats']:
    all_threats.extend(threats.split(', '))
threat_counts = pd.Series(all_threats).value_counts()
print(threat_counts.head(10))

# Visualize
df['risk_score'].hist(bins=20)
plt.xlabel('Risk Score')
plt.ylabel('Count')
plt.title('Distribution of Risk Scores')
plt.savefig('data/results/risk_score_distribution.png')
```

### Calculate Costs for 100K Packages
```python
# Based on test results
avg_images_per_package = 10  # Adjust based on test
packages_to_analyze = 100000
cost_per_image = 0.01

total_images = packages_to_analyze * avg_images_per_package
total_cost = total_images * cost_per_image

print(f"Estimated for 100K packages:")
print(f"  Total images: {total_images:,}")
print(f"  Total cost: ${total_cost:,.2f}")

# With filtering (only analyze suspicious)
suspicious_rate = 0.05  # 5% of images are suspicious
filtered_cost = total_cost * suspicious_rate

print(f"\nWith pre-filtering:")
print(f"  Images to analyze: {int(total_images * suspicious_rate):,}")
print(f"  Total cost: ${filtered_cost:,.2f}")
```

### Plan Optimization
```python
# Optimization strategies

# 1. Two-stage filtering
# Stage 1: Cheap heuristics (free)
#   - Check badge URLs
#   - Detect QR codes
#   - Check image entropy
# Stage 2: GPT-4V only for suspicious (expensive)

# 2. Batch processing
#   - Process 1000 packages/day
#   - 100 days for 100K packages

# 3. Parallel processing
#   - Use multiprocessing
#   - 32 workers = 32x speedup

# 4. Cost optimization
#   - Use GPT-4V mini (cheaper)
#   - Cache results
#   - Skip duplicate images
```

## End of Week Checklist

- [ ] Environment set up
- [ ] API keys configured
- [ ] Basic pipeline working
- [ ] Tested on 10 packages
- [ ] Found at least 1-2 suspicious images
- [ ] Cost estimation complete
- [ ] Optimization strategy defined
- [ ] Next week plan ready

## Next Week Plan

### Week 2: Pilot Study (1,000 packages)
- [ ] Implement two-stage filtering
- [ ] Add parallel processing
- [ ] Analyze 1,000 packages
- [ ] Manual verification of findings
- [ ] Refine detection criteria

### Week 3-4: Infrastructure Scaling
- [ ] Set up cloud computing (AWS/GCP)
- [ ] Implement distributed processing
- [ ] Add result database (SQLite/PostgreSQL)
- [ ] Create monitoring dashboard

## Questions to Answer This Week

1. **Does the pipeline work?** 
   - Can we successfully analyze packages end-to-end?

2. **Are we finding suspicious images?**
   - At least 1-2 in 10 packages?

3. **What's the false positive rate?**
   - Manual verification needed

4. **What's the actual cost?**
   - Is $1,000-2,000 realistic for 100K packages?

5. **What optimizations are needed?**
   - Two-stage filtering? Parallel processing?

## Success Criteria for This Week

✅ **Minimum**: Pipeline works on 10 packages
✅ **Good**: Found 1-2 suspicious images
✅ **Excellent**: Found 5+ suspicious images with low false positives

## Resources

### Documentation
- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
- [PyPI JSON API](https://warehouse.pypa.io/api-reference/json.html)
- [GitPython](https://gitpython.readthedocs.io/)

### Cost Calculators
- [OpenAI Pricing](https://openai.com/pricing)
- GPT-4V: ~$0.01 per image (varies by size)

### Cloud Credits
- [AWS Educate](https://aws.amazon.com/education/awseducate/)
- [GCP Education](https://cloud.google.com/edu)
- [GitHub Student Pack](https://education.github.com/pack)

## Notes

- Start small, iterate fast
- Manual verification is crucial
- Document everything
- Keep track of costs
- Don't optimize prematurely

**Good luck! 🚀**
