# Multimodal Attack Vector Dataset Collection Guide

## Overview

Practical guide for collecting image-based attack vector dataset for ROTA multimodal extension.

## Data Sources & Collection Methods

### 1. Public Security Databases

#### GitHub Security Advisory Database
```python
import requests
from datetime import datetime

class GitHubAdvisoryCollector:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.github.com/graphql"
    
    def search_image_related_advisories(self):
        """Search for advisories mentioning visual attacks"""
        query = """
        query {
          securityAdvisories(first: 100, 
            orderBy: {field: PUBLISHED_AT, direction: DESC}) {
            nodes {
              summary
              description
              publishedAt
              references {
                url
              }
              vulnerabilities(first: 10) {
                nodes {
                  package {
                    name
                    ecosystem
                  }
                }
              }
            }
          }
        }
        """
        
        keywords = [
            'malicious image', 'fake badge', 'visual phishing',
            'steganography', 'QR code', 'logo', 'screenshot'
        ]
        
        # Filter advisories containing image-related keywords
        results = []
        for advisory in self._execute_query(query):
            if any(kw in advisory['description'].lower() for kw in keywords):
                results.append(advisory)
        
        return results
```

#### Sonatype OSS Index
```python
class SonatypeCollector:
    def collect_malicious_packages(self):
        """Collect known malicious packages from Sonatype"""
        url = "https://ossindex.sonatype.org/api/v3/component-report"
        
        # Known malicious package lists
        sources = [
            'https://github.com/datadog/guarddog/blob/main/guarddog/analyzer/metadata/resources/typosquatting.json',
            'https://github.com/lxyeternal/pypi_malregistry'
        ]
        
        malicious_packages = []
        for source in sources:
            packages = self._fetch_package_list(source)
            malicious_packages.extend(packages)
        
        return malicious_packages
```

### 2. Academic Paper Mining

#### ArXiv & Security Conference Papers
```python
class AcademicPaperMiner:
    def search_papers(self):
        """Search for papers on supply chain attacks"""
        queries = [
            'supply chain attack visual',
            'typosquatting image',
            'malicious package detection',
            'software supply chain security'
        ]
        
        papers = []
        for query in queries:
            # ArXiv API
            arxiv_results = self._search_arxiv(query)
            papers.extend(arxiv_results)
            
            # Google Scholar
            scholar_results = self._search_scholar(query)
            papers.extend(scholar_results)
        
        return papers
    
    def extract_case_studies(self, papers):
        """Extract case studies with image evidence"""
        case_studies = []
        
        for paper in papers:
            # Download PDF
            pdf_path = self._download_pdf(paper.url)
            
            # Extract images
            images = self._extract_images_from_pdf(pdf_path)
            
            # Extract captions and context
            for img in images:
                context = self._extract_image_context(pdf_path, img)
                if self._is_malicious_example(context):
                    case_studies.append({
                        'image': img,
                        'context': context,
                        'paper': paper.title,
                        'year': paper.year
                    })
        
        return case_studies
```

### 3. Security Blog Scraping

#### Automated Blog Monitoring
```python
class SecurityBlogScraper:
    def __init__(self):
        self.blogs = [
            'https://blog.sonatype.com',
            'https://snyk.io/blog',
            'https://www.reversinglabs.com/blog',
            'https://blog.phylum.io',
            'https://checkmarx.com/blog',
            'https://jfrog.com/blog'
        ]
    
    def scrape_all_blogs(self):
        """Scrape security blogs for malicious package reports"""
        incidents = []
        
        for blog_url in self.blogs:
            posts = self._get_recent_posts(blog_url, days=365)
            
            for post in posts:
                if self._is_supply_chain_related(post):
                    # Extract images
                    images = self._extract_images(post.content)
                    
                    # Extract package names
                    packages = self._extract_package_names(post.content)
                    
                    incidents.append({
                        'source': blog_url,
                        'title': post.title,
                        'date': post.date,
                        'images': images,
                        'packages': packages,
                        'url': post.url
                    })
        
        return incidents
    
    def _is_supply_chain_related(self, post):
        """Check if post is about supply chain attacks"""
        keywords = [
            'malicious package', 'typosquatting', 'dependency confusion',
            'supply chain attack', 'npm attack', 'pypi attack'
        ]
        return any(kw in post.title.lower() or kw in post.content.lower() 
                   for kw in keywords)
```

### 4. Package Repository Monitoring

#### Real-time Package Monitoring
```python
class PackageMonitor:
    def monitor_new_packages(self, ecosystem='pypi'):
        """Monitor newly published packages for suspicious images"""
        if ecosystem == 'pypi':
            feed_url = 'https://pypi.org/rss/packages.xml'
        elif ecosystem == 'npm':
            feed_url = 'https://registry.npmjs.org/-/rss'
        
        while True:
            new_packages = self._fetch_new_packages(feed_url)
            
            for package in new_packages:
                # Check for typosquatting
                if self._is_potential_typosquat(package.name):
                    # Collect all images
                    images = self._collect_package_images(package)
                    
                    # Analyze for suspicious patterns
                    for img in images:
                        risk = self._quick_risk_check(img, package)
                        if risk > 0.7:
                            self._flag_for_review(package, img, risk)
            
            time.sleep(300)  # Check every 5 minutes
```

### 5. Synthetic Data Generation

#### Fake Badge Generator
```python
from PIL import Image, ImageDraw, ImageFont
import random

class FakeBadgeGenerator:
    def __init__(self):
        self.legitimate_badges = self._collect_real_badges()
        self.suspicious_domains = [
            'bit.ly', 'tinyurl.com', 'goo.gl',
            'github.com.evil.com', '192.168.1.1'
        ]
    
    def generate_fake_badge(self, badge_type='security'):
        """Generate fake security badge"""
        # Start with legitimate badge template
        template = random.choice(self.legitimate_badges[badge_type])
        
        # Modify URL to suspicious domain
        fake_url = random.choice(self.suspicious_domains)
        
        # Create badge image
        img = Image.new('RGB', (120, 20), color='green')
        draw = ImageDraw.Draw(img)
        
        # Add text
        font = ImageFont.truetype('arial.ttf', 12)
        draw.text((10, 5), f"Security: Verified", fill='white', font=font)
        
        # Add metadata
        metadata = {
            'url': fake_url,
            'type': 'fake_badge',
            'legitimate_template': template.name
        }
        
        return img, metadata
    
    def generate_dataset(self, count=1000):
        """Generate dataset of fake badges"""
        dataset = []
        
        badge_types = ['security', 'build', 'coverage', 'downloads']
        
        for i in range(count):
            badge_type = random.choice(badge_types)
            img, metadata = self.generate_fake_badge(badge_type)
            
            # Save image
            img_path = f'data/synthetic/fake_badges/{i:05d}.png'
            img.save(img_path)
            
            dataset.append({
                'image_path': img_path,
                'label': 'malicious',
                'type': 'fake_badge',
                'metadata': metadata
            })
        
        return dataset
```

#### Steganography Injector
```python
from stegano import lsb
import numpy as np

class SteganographyDataGenerator:
    def inject_payload(self, clean_image_path, payload_type='text'):
        """Inject hidden payload into clean image"""
        # Load clean image
        clean_img = Image.open(clean_image_path)
        
        # Generate payload
        if payload_type == 'text':
            payload = self._generate_malicious_text()
        elif payload_type == 'url':
            payload = self._generate_malicious_url()
        elif payload_type == 'code':
            payload = self._generate_malicious_code()
        
        # LSB steganography
        stego_img = lsb.hide(clean_image_path, payload)
        
        return stego_img, payload
    
    def generate_dataset(self, clean_images, count=5000):
        """Generate steganography dataset"""
        dataset = []
        
        for i in range(count):
            clean_img = random.choice(clean_images)
            payload_type = random.choice(['text', 'url', 'code'])
            
            stego_img, payload = self.inject_payload(clean_img, payload_type)
            
            # Save
            stego_path = f'data/synthetic/steganography/{i:05d}.png'
            stego_img.save(stego_path)
            
            dataset.append({
                'image_path': stego_path,
                'label': 'malicious',
                'type': 'steganography',
                'payload': payload,
                'payload_type': payload_type,
                'clean_image': clean_img
            })
        
        return dataset
```

#### Malicious QR Code Generator
```python
import qrcode

class MaliciousQRGenerator:
    def __init__(self):
        self.suspicious_patterns = [
            'http://bit.ly/{random}',
            'http://192.168.1.1/malware',
            'http://github.com.evil.com',
            'http://pypi.org.phishing.com',
            'http://npmjs.com-secure.ru'
        ]
    
    def generate_malicious_qr(self):
        """Generate QR code with suspicious URL"""
        # Generate suspicious URL
        pattern = random.choice(self.suspicious_patterns)
        if '{random}' in pattern:
            pattern = pattern.replace('{random}', 
                                     ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8)))
        
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(pattern)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        return img, pattern
    
    def generate_dataset(self, count=500):
        """Generate malicious QR code dataset"""
        dataset = []
        
        for i in range(count):
            img, url = self.generate_malicious_qr()
            
            # Save
            img_path = f'data/synthetic/malicious_qr/{i:05d}.png'
            img.save(img_path)
            
            dataset.append({
                'image_path': img_path,
                'label': 'malicious',
                'type': 'malicious_qr',
                'url': url
            })
        
        return dataset
```

### 6. Legitimate Image Collection

#### Baseline Dataset
```python
class LegitimateImageCollector:
    def collect_from_top_packages(self, count=50000):
        """Collect legitimate images from popular packages"""
        # Get top packages
        top_packages = self._get_top_packages('pypi', count=1000)
        
        legitimate_images = []
        
        for package in top_packages:
            try:
                # Get package repository
                repo_url = self._get_repo_url(package)
                
                # Clone or download
                repo_path = self._download_repo(repo_url)
                
                # Extract images
                images = self._extract_images(repo_path)
                
                for img in images:
                    legitimate_images.append({
                        'image_path': img.path,
                        'label': 'legitimate',
                        'package': package.name,
                        'location': img.relative_path,
                        'type': self._classify_image_type(img)
                    })
                
                if len(legitimate_images) >= count:
                    break
                    
            except Exception as e:
                print(f"Error processing {package.name}: {e}")
                continue
        
        return legitimate_images
    
    def _classify_image_type(self, img):
        """Classify legitimate image type"""
        path = img.relative_path.lower()
        
        if 'readme' in path or 'docs' in path:
            return 'documentation'
        elif 'logo' in path or 'icon' in path:
            return 'branding'
        elif 'screenshot' in path or 'demo' in path:
            return 'demo'
        elif 'badge' in path:
            return 'badge'
        else:
            return 'other'
```

## Dataset Organization

### Directory Structure
```
data/
├── raw/
│   ├── legitimate/
│   │   ├── pypi/
│   │   │   ├── flask/
│   │   │   │   ├── logo.png
│   │   │   │   ├── screenshot.png
│   │   │   │   └── metadata.json
│   │   │   └── django/
│   │   └── npm/
│   └── malicious/
│       ├── real/
│       │   ├── incident_001/
│       │   │   ├── fake_badge.png
│       │   │   ├── metadata.json
│       │   │   └── source.txt
│       │   └── incident_002/
│       └── synthetic/
│           ├── fake_badges/
│           ├── steganography/
│           └── malicious_qr/
├── processed/
│   ├── train/
│   ├── val/
│   └── test/
└── metadata/
    ├── dataset_stats.json
    └── collection_log.json
```

### Metadata Format
```json
{
  "image_id": "img_00001",
  "image_path": "data/raw/malicious/real/incident_001/fake_badge.png",
  "label": "malicious",
  "type": "fake_badge",
  "source": "github_advisory",
  "package_name": "malicious-package-name",
  "ecosystem": "pypi",
  "incident_date": "2023-08-15",
  "collected_at": "2024-01-20",
  "verified": true,
  "notes": "Fake security badge with suspicious URL"
}
```

## Data Collection Pipeline

### Full Pipeline Script
```python
class DataCollectionPipeline:
    def __init__(self):
        self.collectors = {
            'github_advisory': GitHubAdvisoryCollector(),
            'security_blogs': SecurityBlogScraper(),
            'academic_papers': AcademicPaperMiner(),
            'package_monitor': PackageMonitor(),
            'synthetic_badges': FakeBadgeGenerator(),
            'synthetic_stego': SteganographyDataGenerator(),
            'synthetic_qr': MaliciousQRGenerator(),
            'legitimate': LegitimateImageCollector()
        }
    
    def run_full_collection(self):
        """Run complete data collection pipeline"""
        print("Starting data collection pipeline...")
        
        # Phase 1: Collect real malicious images
        print("\n[Phase 1] Collecting real malicious images...")
        real_malicious = []
        real_malicious.extend(self.collectors['github_advisory'].collect())
        real_malicious.extend(self.collectors['security_blogs'].scrape_all_blogs())
        real_malicious.extend(self.collectors['academic_papers'].extract_case_studies())
        print(f"Collected {len(real_malicious)} real malicious images")
        
        # Phase 2: Generate synthetic malicious images
        print("\n[Phase 2] Generating synthetic malicious images...")
        synthetic_malicious = []
        synthetic_malicious.extend(self.collectors['synthetic_badges'].generate_dataset(1000))
        synthetic_malicious.extend(self.collectors['synthetic_stego'].generate_dataset(5000))
        synthetic_malicious.extend(self.collectors['synthetic_qr'].generate_dataset(500))
        print(f"Generated {len(synthetic_malicious)} synthetic malicious images")
        
        # Phase 3: Collect legitimate images
        print("\n[Phase 3] Collecting legitimate images...")
        legitimate = self.collectors['legitimate'].collect_from_top_packages(50000)
        print(f"Collected {len(legitimate)} legitimate images")
        
        # Phase 4: Split dataset
        print("\n[Phase 4] Splitting dataset...")
        train, val, test = self._split_dataset(
            real_malicious + synthetic_malicious + legitimate
        )
        
        # Phase 5: Save metadata
        print("\n[Phase 5] Saving metadata...")
        self._save_metadata(train, val, test)
        
        print("\n✓ Data collection complete!")
        print(f"  Train: {len(train)} images")
        print(f"  Val: {len(val)} images")
        print(f"  Test: {len(test)} images")
        
        return train, val, test
```

## Ethical Considerations

### Responsible Data Collection
1. **No Active Attacks**: Never deploy actual malicious packages
2. **Disclosure**: Clearly mark honeypot packages
3. **Privacy**: Anonymize any personal information
4. **Coordination**: Work with PyPI/npm security teams
5. **Responsible Disclosure**: Report found vulnerabilities privately

### Legal Compliance
- Respect robots.txt when scraping
- Follow API terms of service
- Obtain permission for copyrighted images
- Comply with GDPR/privacy regulations

## Next Steps

1. **Week 1-2**: Implement collectors for real malicious images
2. **Week 3-4**: Generate synthetic dataset
3. **Week 5-6**: Collect legitimate baseline
4. **Week 7-8**: Quality control and validation
5. **Week 9-10**: Dataset documentation and release

## Expected Dataset Statistics

| Category | Target Count | Source |
|----------|-------------|--------|
| Real Malicious | 300 | Security reports, papers |
| Synthetic Malicious | 16,500 | Generated |
| Legitimate | 50,000 | Top packages |
| **Total** | **66,800** | Mixed |

**Class Balance**: 
- Malicious: 25% (16,800)
- Legitimate: 75% (50,000)

This imbalance reflects real-world distribution where most images are legitimate.
