# ROTA Multimodal Extension - Quick Start Guide

## TL;DR

Extending ROTA to detect **image-based attack vectors** in software supply chains:
- Fake security badges
- Steganography in package assets
- Malicious QR codes
- Visual phishing in documentation

## The Dataset Problem

**Challenge**: No public dataset of malicious images in package ecosystems exists.

**Solution**: Multi-pronged approach

### 1. Real Malicious Images (Target: 300)

**Sources**:
```bash
# GitHub Security Advisories
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d '{"query": "securityAdvisories(first: 100) { ... }"}'

# Security Blogs
- Sonatype: https://blog.sonatype.com
- Snyk: https://snyk.io/blog
- ReversingLabs: https://www.reversinglabs.com/blog

# Academic Papers
- ArXiv: "supply chain attack visual"
- Google Scholar: "typosquatting image"

# Known Malicious Packages
- Guarddog DB: https://github.com/datadog/guarddog
- PyPI Malregistry: https://github.com/lxyeternal/pypi_malregistry
```

### 2. Synthetic Malicious Images (Target: 16,500)

**Generate programmatically**:

```python
# Fake badges (1,000)
from PIL import Image, ImageDraw
img = Image.new('RGB', (120, 20), 'green')
draw.text((10, 5), "Security: Verified", fill='white')
# But link to: bit.ly/malicious

# Steganography (5,000)
from stegano import lsb
stego_img = lsb.hide('clean.png', 'malicious_payload')

# Malicious QR codes (500)
import qrcode
qr = qrcode.make('http://github.com.evil.com')
```

### 3. Legitimate Images (Target: 50,000)

**From popular packages**:
```python
# Top 1000 PyPI packages
top_packages = requests.get('https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.json')

for package in top_packages:
    # Clone repo
    # Extract images from README, docs, assets
    # Label as legitimate
```

## Quick Start

### Step 1: Setup
```bash
# Clone ROTA
git clone https://github.com/susie-Choi/rota.git
cd rota

# Install dependencies
pip install pillow qrcode stegano pyzbar opencv-python

# Add API keys to .env
echo "GITHUB_TOKEN=your_token" >> .env
echo "GEMINI_API_KEY=your_key" >> .env
```

### Step 2: Collect Dataset
```bash
# Start with synthetic data (no API needed)
python scripts/collect_image_dataset.py --mode synthetic

# Then collect legitimate images
python scripts/collect_image_dataset.py --mode legitimate --target-count 1000

# Finally, mine real malicious images
python scripts/collect_image_dataset.py --mode malicious
```

### Step 3: Zero-Shot Detection (No Training Needed!)
```python
from rota.oracle.multimodal import MultimodalOracle

oracle = MultimodalOracle(use_gpt4v=True)

# Analyze package images
result = oracle.analyze_package_images('suspicious-package')

print(f"Risk Score: {result.risk_score}")
print(f"High-risk images: {result.high_risk_images}")
```

## Dataset Timeline

### Month 1: Foundation
- [x] Design data collection strategy
- [ ] Implement synthetic generators
- [ ] Collect 1,000 legitimate images
- [ ] Mine 50 real malicious images

### Month 2: Expansion
- [ ] Generate 5,000 steganography samples
- [ ] Generate 1,000 fake badges
- [ ] Collect 10,000 legitimate images
- [ ] Mine 100 real malicious images

### Month 3: Completion
- [ ] Reach 50,000 legitimate images
- [ ] Reach 300 real malicious images
- [ ] Complete synthetic generation
- [ ] Quality control and validation

## Alternative: Zero-Shot Approach

**If dataset collection is too slow**, use multimodal LLM directly:

```python
class ZeroShotImageAnalyzer:
    def analyze(self, image, package_context):
        prompt = f"""
        Analyze this image from package '{package_context.name}':
        
        1. Is this image consistent with package purpose?
        2. Are there fake badges or suspicious QR codes?
        3. Does the image URL match the package?
        4. Risk: LOW/MEDIUM/HIGH
        5. Reasoning?
        """
        
        return gpt4v.analyze(image, prompt)
```

**Pros**:
- No training data needed
- Works immediately
- Detects novel attacks

**Cons**:
- Higher API cost (~$0.01/image)
- Slower inference
- Less specialized

## Hybrid Strategy (Recommended)

**Phase 1** (Week 1-4): Zero-shot with GPT-4V
- Start detecting immediately
- Collect edge cases
- Build intuition

**Phase 2** (Week 5-12): Collect dataset
- Real incidents from security reports
- Synthetic generation
- Legitimate baseline

**Phase 3** (Week 13-16): Fine-tune model
- Train on collected dataset
- Specialize for package ecosystems
- Reduce API costs

**Phase 4** (Week 17+): Ensemble
- Combine zero-shot + fine-tuned
- Best of both worlds

## Expected Results

### Detection Rates (Target)
- Fake badges: 85%+ precision
- Steganography: 70%+ detection rate
- Malicious QR: 90%+ precision
- Overall: 80%+ F1 score

### Integration Impact
- 20-30% more threats detected (vs. code-only)
- 15% reduction in false negatives
- Earlier detection of typosquatting

## Cost Estimate

### Data Collection
- GitHub API: Free (with token)
- Security blogs: Free (scraping)
- Academic papers: Free (ArXiv)
- **Total: $0**

### Synthetic Generation
- Compute: Minimal (CPU only)
- Storage: ~15GB
- **Total: $0**

### Zero-Shot Analysis (Optional)
- GPT-4V: $0.01/image
- 10,000 images: $100
- **Total: $100-200/month**

### Fine-tuning (Optional)
- Training: $50-100 (one-time)
- Inference: $0.001/image
- **Total: $50-100 one-time**

## Next Steps

1. **This Week**: Implement synthetic generators
2. **Next Week**: Start collecting legitimate images
3. **Week 3**: Mine real malicious images from security reports
4. **Week 4**: Test zero-shot detection on collected images
5. **Month 2**: Scale up collection to 50,000+ images
6. **Month 3**: Train specialized model
7. **Month 4**: Integrate with ROTA and evaluate

## Resources

### Documentation
- [Full Extension Plan](multimodal-extension-plan.md)
- [Dataset Collection Guide](dataset-collection-guide.md)
- [Collection Script](../scripts/collect_image_dataset.py)

### External Resources
- [Guarddog Malicious Package DB](https://github.com/datadog/guarddog)
- [PyPI Malregistry](https://github.com/lxyeternal/pypi_malregistry)
- [Sonatype Blog](https://blog.sonatype.com)
- [Snyk Blog](https://snyk.io/blog)

### Papers
- "Towards Measuring Supply Chain Attacks on Package Managers" (NDSS 2020)
- "Small World with High Risks: A Study of Security Threats in the npm Ecosystem" (USENIX 2019)
- "Backstabber's Knife Collection: A Review of Open Source Software Supply Chain Attacks" (DIMVA 2020)

## FAQ

**Q: Can I start without collecting data?**
A: Yes! Use zero-shot GPT-4V detection immediately.

**Q: How long to collect 50,000 images?**
A: 2-3 months with automated scripts.

**Q: What if I can't find real malicious images?**
A: Synthetic data + zero-shot LLM is sufficient for research.

**Q: Is this legal/ethical?**
A: Yes, as long as you:
- Don't deploy actual malicious packages
- Respect robots.txt when scraping
- Follow API terms of service
- Report found vulnerabilities responsibly

**Q: What's the minimum viable dataset?**
A: 1,000 legitimate + 100 synthetic malicious = enough for proof-of-concept

## Contact

Questions? Open an issue or reach out:
- GitHub: [susie-Choi/rota](https://github.com/susie-Choi/rota)
- Issues: [GitHub Issues](https://github.com/susie-Choi/rota/issues)

---

**Status**: Planning phase
**Last Updated**: 2025-11-06
**Next Milestone**: Implement synthetic generators (Week 1)
