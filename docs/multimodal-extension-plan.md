# ROTA Multimodal Extension: Image-based Attack Vector Detection

## Executive Summary

Extending ROTA from code-only analysis to **multimodal LLM attack vector detection** that includes image-based threats. This addresses emerging security risks from:
- Malicious images in documentation
- Steganography in package assets
- Visual social engineering in README files
- Adversarial images targeting ML models
- QR codes and embedded payloads

## Research Motivation

### Current Gap
Existing vulnerability detection focuses on code analysis, missing:
- **Visual phishing**: Fake badges, misleading screenshots
- **Steganography**: Hidden payloads in images
- **Supply chain attacks**: Compromised logos/assets
- **ML model attacks**: Adversarial images in datasets
- **Documentation attacks**: Malicious images in docs

### Real-World Examples
1. **npm package with malicious QR code** (2023): QR code in README linked to phishing site
2. **PyPI typosquatting with fake badges** (2022): Fake security badges to appear legitimate
3. **Steganography in package assets** (2021): Hidden malware in image files
4. **Adversarial images in ML datasets** (ongoing): Poisoned training data

## Architecture Extension

### Current ROTA Architecture
```
SPOKES (Data) → HUB (Neo4j) → ORACLE (LLM) → AXLE (Eval)
```

### Extended Multimodal Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                  MULTIMODAL ORACLE                           │
│  (Text + Code + Image Analysis)                              │
└────────────┬────────────────────────────────┬────────────────┘
             │                                │
    ┌────────▼────────┐              ┌───────▼────────┐
    │  CODE ANALYZER  │              │ IMAGE ANALYZER │
    │  (Existing)     │              │    (NEW)       │
    └────────┬────────┘              └───────┬────────┘
             │                                │
             └────────────┬───────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
    │ SPOKES  │      │   HUB   │     │  AXLE   │
    │ (Data)  │─────▶│ (Neo4j) │◀────│ (Eval)  │
    └─────────┘      └─────────┘     └─────────┘
```

## New Components

### 1. Image Collector (Spokes Extension)

**Purpose**: Collect images from package repositories

**Data Sources**:
- README images (badges, screenshots, diagrams)
- Documentation images
- Package assets (logos, icons)
- Example images in repos
- ML dataset images (if applicable)

**Implementation**:
```python
class ImageCollector:
    def collect_package_images(self, repo_url):
        """Collect all images from package repository"""
        images = {
            'readme_images': self._extract_readme_images(),
            'doc_images': self._extract_doc_images(),
            'asset_images': self._extract_asset_images(),
            'example_images': self._extract_example_images()
        }
        return images
    
    def download_and_store(self, image_url, package_name):
        """Download image and store with metadata"""
        image_data = requests.get(image_url).content
        metadata = {
            'package': package_name,
            'url': image_url,
            'size': len(image_data),
            'format': self._detect_format(image_data),
            'collected_at': datetime.now()
        }
        # Store in data/raw/images/{package_name}/
```

### 2. Image Analyzer (New Oracle Component)

**Purpose**: Analyze images for security threats using multimodal LLMs

**Analysis Types**:

#### A. Visual Phishing Detection
```python
class VisualPhishingDetector:
    def analyze_badges(self, image):
        """Detect fake security badges"""
        prompt = """
        Analyze this badge image:
        1. Is it a legitimate security badge?
        2. Does the URL match the claimed service?
        3. Are there visual inconsistencies?
        4. Risk score: 0-1
        """
        return multimodal_llm.analyze(image, prompt)
```

#### B. Steganography Detection
```python
class SteganographyDetector:
    def detect_hidden_payload(self, image):
        """Detect hidden data in images"""
        # Statistical analysis
        lsb_analysis = self._analyze_lsb(image)
        entropy_analysis = self._analyze_entropy(image)
        
        # Visual analysis with LLM
        prompt = """
        Analyze this image for steganography:
        1. Are there unusual patterns?
        2. Is entropy distribution normal?
        3. Likelihood of hidden data: 0-1
        """
        return multimodal_llm.analyze(image, prompt)
```

#### C. QR Code Analysis
```python
class QRCodeAnalyzer:
    def analyze_qr_codes(self, image):
        """Extract and analyze QR codes"""
        qr_codes = self._extract_qr_codes(image)
        
        for qr in qr_codes:
            url = qr.decode()
            risk = self._analyze_url_risk(url)
            
            # Check if URL matches package context
            if not self._is_legitimate_url(url, package_context):
                return {'risk': 'HIGH', 'reason': 'Suspicious QR code'}
```

#### D. Adversarial Image Detection
```python
class AdversarialImageDetector:
    def detect_adversarial(self, image):
        """Detect adversarial perturbations"""
        # Gradient-based detection
        gradients = self._compute_gradients(image)
        
        # Statistical anomaly detection
        if self._is_anomalous(gradients):
            return {'risk': 'HIGH', 'type': 'adversarial'}
```

### 3. Multimodal Hub Extension

**Neo4j Schema Extension**:
```cypher
// New node types
(Image {url, format, size, hash, collected_at})
(VisualThreat {type, severity, description})

// New relationships
(Package)-[:HAS_IMAGE]->(Image)
(Image)-[:CONTAINS_THREAT]->(VisualThreat)
(Image)-[:SIMILAR_TO]->(Image)  // Visual similarity
```

### 4. Integrated Multimodal Oracle

**Risk Score Fusion**:
```python
class MultimodalOracle:
    def assess_risk(self, package_name):
        # Existing code analysis
        code_risk = self.code_analyzer.analyze(package_name)
        
        # NEW: Image analysis
        image_risk = self.image_analyzer.analyze(package_name)
        
        # Fusion
        overall_risk = (
            code_risk * 0.7 +      # Code still primary
            image_risk * 0.3       # Image as secondary signal
        )
        
        # Boost for high-risk images
        if image_risk > 0.8:
            overall_risk += 0.15
        
        return {
            'overall_risk': overall_risk,
            'code_risk': code_risk,
            'image_risk': image_risk,
            'high_risk_images': self._get_high_risk_images()
        }
```

## Implementation Plan

### Phase 1: Data Collection (2 weeks)
- [ ] Implement ImageCollector
- [ ] Collect images from top 1000 PyPI packages
- [ ] Store images with metadata
- [ ] Build image index in Neo4j

### Phase 2: Basic Image Analysis (3 weeks)
- [ ] Implement VisualPhishingDetector
- [ ] Implement QRCodeAnalyzer
- [ ] Test on known malicious packages
- [ ] Validate detection accuracy

### Phase 3: Advanced Analysis (3 weeks)
- [ ] Implement SteganographyDetector
- [ ] Implement AdversarialImageDetector
- [ ] Integrate with multimodal LLM (GPT-4V, Claude 3)
- [ ] Build visual similarity graph

### Phase 4: Integration (2 weeks)
- [ ] Extend Neo4j schema
- [ ] Implement MultimodalOracle
- [ ] Update risk scoring formula
- [ ] Build multimodal dashboard

### Phase 5: Evaluation (2 weeks)
- [ ] Historical validation with known cases
- [ ] Ablation study (with/without image analysis)
- [ ] Performance benchmarking
- [ ] False positive analysis

## Technical Stack

### New Dependencies
```python
# Image processing
pillow>=10.0.0
opencv-python>=4.8.0

# Steganography detection
stegano>=0.11.0
numpy>=1.24.0

# QR code processing
pyzbar>=0.1.9
qrcode>=7.4.0

# Multimodal LLM
openai>=1.0.0  # GPT-4V
anthropic>=0.8.0  # Claude 3

# Image similarity
imagehash>=4.3.0
scikit-image>=0.21.0
```

### Storage Requirements
- Images: ~10GB for 10,000 packages
- Image embeddings: ~5GB
- Total: ~15GB additional storage

### API Costs
- GPT-4V: ~$0.01 per image
- Claude 3 Opus: ~$0.015 per image
- Estimated cost for 10,000 packages: $100-150

## Evaluation Metrics

### Image-Specific Metrics
- **Visual Phishing Detection Rate**: % of fake badges detected
- **Steganography Detection Rate**: % of hidden payloads found
- **QR Code Risk Assessment Accuracy**: Precision/Recall
- **False Positive Rate**: % of legitimate images flagged

### Integrated Metrics
- **Multimodal Precision@K**: With vs. without image analysis
- **Lead Time Improvement**: Earlier detection with visual signals
- **Risk Score Correlation**: Image risk vs. actual vulnerabilities

## Research Contributions

### Novel Aspects
1. **First multimodal approach** to supply chain security
2. **Visual threat taxonomy** for package ecosystems
3. **Cross-modal risk fusion** methodology
4. **Historical validation** with real-world cases

### Paper Outline
**Title**: "Multimodal LLM-based Threat Detection: Beyond Code Analysis in Software Supply Chains"

**Sections**:
1. Introduction: Visual threats in package ecosystems
2. Related Work: Code analysis vs. multimodal analysis
3. Methodology: Image collection, analysis, fusion
4. Experiments: Historical validation, ablation study
5. Results: Detection rates, lead time, case studies
6. Discussion: Limitations, future work
7. Conclusion

**Target Venues**:
- USENIX Security (multimodal security)
- ACM CCS (supply chain security)
- IEEE S&P (ML security)

## Dataset Construction Strategy

### Challenge: Lack of Labeled Attack Image Dataset

**Problem**: Unlike CVE databases for code vulnerabilities, there's no public dataset of malicious images in package ecosystems.

**Solution**: Multi-pronged data collection strategy

### 1. Historical Incident Mining

**Sources**:
- **GitHub Security Advisories**: Search for "malicious image", "fake badge", "phishing"
- **npm/PyPI Security Reports**: Official security incident reports
- **Security Blogs**: Snyk, Sonatype, ReversingLabs blog posts
- **Academic Papers**: Papers on supply chain attacks
- **CVE Descriptions**: Search for image-related vulnerabilities

**Implementation**:
```python
class HistoricalIncidentCollector:
    def collect_from_github_advisories(self):
        """Search GitHub Security Database"""
        query = "malicious image OR fake badge OR visual phishing"
        advisories = github_api.search_advisories(query)
        
        for advisory in advisories:
            if advisory.has_image_evidence():
                self._archive_malicious_image(advisory)
    
    def collect_from_security_blogs(self):
        """Scrape security research blogs"""
        sources = [
            'https://blog.sonatype.com',
            'https://snyk.io/blog',
            'https://www.reversinglabs.com/blog'
        ]
        # Search for posts about visual attacks
```

**Expected Yield**: 50-100 real malicious images

### 2. Synthetic Attack Generation

**Approach**: Generate synthetic malicious images for training

#### A. Fake Badge Generation
```python
class FakeBadgeGenerator:
    def generate_fake_badges(self, count=1000):
        """Generate fake security badges"""
        legitimate_badges = self._collect_real_badges()
        
        for badge in legitimate_badges:
            # Modify URL to suspicious domain
            fake_badge = badge.copy()
            fake_badge.url = self._generate_suspicious_url()
            
            # Slight visual modifications
            fake_badge = self._add_visual_noise(fake_badge)
            
            yield fake_badge
```

#### B. Steganography Injection
```python
class SteganographyInjector:
    def inject_payload(self, clean_image, payload):
        """Inject hidden payload into clean image"""
        # LSB steganography
        stego_image = self._lsb_inject(clean_image, payload)
        
        # DCT-based steganography
        stego_image_dct = self._dct_inject(clean_image, payload)
        
        return [stego_image, stego_image_dct]
```

#### C. Malicious QR Code Generation
```python
class MaliciousQRGenerator:
    def generate_malicious_qr(self, count=500):
        """Generate QR codes with suspicious URLs"""
        suspicious_patterns = [
            'bit.ly/[random]',  # URL shorteners
            'typosquatted-domain.com',
            'github.com.evil.com',  # Homograph attack
            'IP addresses',
            'non-HTTPS URLs'
        ]
        
        for pattern in suspicious_patterns:
            qr_code = qrcode.make(pattern)
            yield qr_code
```

**Expected Yield**: 5,000-10,000 synthetic malicious images

### 3. Typosquatting Package Analysis

**Approach**: Analyze known typosquatting packages for visual deception

```python
class TyposquattingImageCollector:
    def collect_from_known_typosquatters(self):
        """Collect images from known malicious packages"""
        # Datasets of typosquatting packages
        sources = [
            'https://github.com/datadog/guarddog',  # Malicious package DB
            'https://github.com/pypa/warehouse/issues',  # PyPI reports
            'https://github.com/npm/security-wg'  # npm security reports
        ]
        
        for package in self._get_malicious_packages(sources):
            images = self._extract_all_images(package)
            self._label_as_malicious(images, package.reason)
```

**Expected Yield**: 200-500 real malicious package images

### 4. Crowdsourced Labeling

**Approach**: Collect legitimate images and use weak supervision

```python
class WeakSupervisionLabeler:
    def label_with_heuristics(self, image, context):
        """Use heuristics for weak labeling"""
        risk_signals = []
        
        # Heuristic 1: Badge URL mismatch
        if self._is_badge(image):
            if not self._url_matches_context(image.url, context):
                risk_signals.append('url_mismatch')
        
        # Heuristic 2: Unusual entropy
        if self._has_high_entropy(image):
            risk_signals.append('high_entropy')
        
        # Heuristic 3: QR code to suspicious domain
        if self._contains_qr(image):
            url = self._decode_qr(image)
            if self._is_suspicious_url(url):
                risk_signals.append('suspicious_qr')
        
        return risk_signals
```

**Expected Yield**: 100,000+ weakly labeled images

### 5. Adversarial Image Generation

**Approach**: Generate adversarial examples for ML model testing

```python
class AdversarialImageGenerator:
    def generate_adversarial(self, clean_images, target_model):
        """Generate adversarial perturbations"""
        # FGSM attack
        fgsm_images = self._fgsm_attack(clean_images, target_model)
        
        # PGD attack
        pgd_images = self._pgd_attack(clean_images, target_model)
        
        # C&W attack
        cw_images = self._cw_attack(clean_images, target_model)
        
        return fgsm_images + pgd_images + cw_images
```

**Expected Yield**: 10,000+ adversarial images

### 6. Honeypot Package Deployment

**Approach**: Deploy honeypot packages to attract attackers

```python
class HoneypotPackage:
    def deploy_honeypot(self):
        """Deploy honeypot package to collect attack attempts"""
        # Create attractive target (popular name typo)
        package_name = self._generate_typosquat_name('requests')
        
        # Monitor for malicious image uploads
        self._monitor_image_uploads()
        
        # Collect and analyze attack patterns
        self._analyze_attack_images()
```

**Expected Yield**: 50-200 real attack attempts (over 6 months)

**Ethical Considerations**: 
- Clear disclosure in package description
- No actual functionality to avoid user harm
- Coordinate with PyPI security team

## Dataset Composition (Target)

### Training Set
| Category | Real | Synthetic | Total |
|----------|------|-----------|-------|
| Fake Badges | 50 | 1,000 | 1,050 |
| Steganography | 20 | 5,000 | 5,020 |
| Malicious QR | 30 | 500 | 530 |
| Adversarial | 0 | 10,000 | 10,000 |
| Typosquatting | 200 | 0 | 200 |
| **Total Malicious** | **300** | **16,500** | **16,800** |
| Legitimate | 50,000 | 0 | 50,000 |
| **Grand Total** | **50,300** | **16,500** | **66,800** |

### Validation Set
- 50 real malicious images (held out from training)
- 5,000 legitimate images
- Focus on recent incidents (2023-2024)

### Test Set (Historical Validation)
- Known incidents with timestamps
- Log4Shell-style case studies
- Temporal split to prevent data leakage

## Alternative Approach: Zero-Shot Detection

**If dataset is insufficient**, use zero-shot multimodal LLM:

```python
class ZeroShotImageAnalyzer:
    def analyze_without_training(self, image, context):
        """Use GPT-4V/Claude 3 without fine-tuning"""
        prompt = f"""
        Analyze this image from package '{context.package_name}':
        
        Context:
        - Package description: {context.description}
        - Official website: {context.website}
        - Image location: {context.image_location}
        
        Questions:
        1. Is this image consistent with the package purpose?
        2. Are there any suspicious elements (fake badges, QR codes)?
        3. Does the image URL match the package context?
        4. Risk assessment: LOW/MEDIUM/HIGH
        5. Reasoning: Why?
        """
        
        return gpt4v.analyze(image, prompt)
```

**Advantages**:
- No training data needed
- Leverages LLM's general knowledge
- Can detect novel attack patterns

**Disadvantages**:
- Higher API costs
- Slower inference
- Less specialized

## Hybrid Strategy (Recommended)

**Combine multiple approaches**:

1. **Phase 1**: Zero-shot detection with GPT-4V (no training needed)
2. **Phase 2**: Collect real incidents + generate synthetic data
3. **Phase 3**: Fine-tune specialized model on collected dataset
4. **Phase 4**: Ensemble (zero-shot + fine-tuned)

```python
class HybridImageAnalyzer:
    def analyze(self, image, context):
        # Zero-shot analysis
        zero_shot_result = self.zero_shot_analyzer.analyze(image, context)
        
        # Fine-tuned model (if available)
        if self.fine_tuned_model:
            finetuned_result = self.fine_tuned_model.predict(image)
            
            # Ensemble
            final_risk = (
                zero_shot_result.risk * 0.6 +
                finetuned_result.risk * 0.4
            )
        else:
            final_risk = zero_shot_result.risk
        
        return final_risk
```

## Data Collection Timeline

### Month 1: Foundation
- [ ] Collect 50,000 legitimate images from top packages
- [ ] Mine 50-100 real malicious images from security reports
- [ ] Generate 1,000 synthetic fake badges

### Month 2: Expansion
- [ ] Generate 5,000 steganography samples
- [ ] Generate 500 malicious QR codes
- [ ] Analyze 200 typosquatting packages

### Month 3: Advanced
- [ ] Generate 10,000 adversarial images
- [ ] Deploy honeypot packages
- [ ] Implement weak supervision labeling

### Month 4: Validation
- [ ] Curate test set with known incidents
- [ ] Validate dataset quality
- [ ] Prepare for model training

## Case Studies for Validation

### Case 1: npm Package with Malicious QR Code
- **Package**: [To be identified from security reports]
- **Date**: 2023-08
- **Attack**: QR code in README linked to phishing
- **Validation**: Can we detect suspicious QR code?
- **Data Source**: npm security advisories

### Case 2: PyPI Typosquatting with Fake Badges
- **Package**: [To be identified from PyPI reports]
- **Date**: 2022-11
- **Attack**: Fake security badges to appear legitimate
- **Validation**: Can we detect fake badges?
- **Data Source**: PyPI security reports

### Case 3: Steganography in Package Assets
- **Package**: [To be identified from academic papers]
- **Date**: 2021-06
- **Attack**: Hidden malware in logo image
- **Validation**: Can we detect hidden payload?
- **Data Source**: Security research papers

## Limitations and Future Work

### Current Limitations
1. **Image coverage**: Not all packages have images
2. **False positives**: Legitimate images may trigger alerts
3. **Computational cost**: Image analysis is expensive
4. **Evasion**: Attackers can adapt to detection

### Future Enhancements
1. **Video analysis**: Analyze demo videos
2. **Audio analysis**: Analyze podcast/tutorial audio
3. **3D model analysis**: Analyze CAD files, 3D assets
4. **Real-time monitoring**: Continuous image scanning
5. **Adversarial robustness**: Defend against evasion

## Timeline

**Total Duration**: 12 weeks

- Week 1-2: Data collection
- Week 3-5: Basic analysis
- Week 6-8: Advanced analysis
- Week 9-10: Integration
- Week 11-12: Evaluation

**Milestones**:
- Week 2: 1000 packages with images collected
- Week 5: Visual phishing detector working
- Week 8: Steganography detector working
- Week 10: Multimodal oracle integrated
- Week 12: Paper draft ready

## Success Criteria

### Minimum Viable Product (MVP)
- [ ] Collect images from 1000+ packages
- [ ] Detect visual phishing (badges, screenshots)
- [ ] Detect QR code risks
- [ ] Integrate with existing ROTA
- [ ] Validate with 3+ real-world cases

### Research Publication
- [ ] Novel multimodal methodology
- [ ] Historical validation results
- [ ] Ablation study showing improvement
- [ ] Open-source implementation
- [ ] Accepted at top-tier venue

## Conclusion

Extending ROTA to multimodal analysis addresses a critical gap in supply chain security. By analyzing images alongside code, we can detect visual threats that traditional tools miss. This extension maintains ROTA's core philosophy of **proactive defense** while expanding the threat surface coverage.

**Key Innovation**: First system to combine code analysis, behavioral signals, and visual threat detection for comprehensive supply chain security.

**Expected Impact**: 
- Detect 20-30% more threats (visual attacks)
- Reduce false negatives in typosquatting detection
- Enable new research direction in multimodal security
