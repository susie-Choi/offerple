"""Script to build and publish ROTA to PyPI.

Usage:
    python scripts/publish_to_pypi.py --test  # Upload to TestPyPI
    python scripts/publish_to_pypi.py         # Upload to PyPI
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result.returncode == 0


def clean_build():
    """Clean previous build artifacts."""
    print("🧹 Cleaning build artifacts...")
    
    # Remove build directories
    for pattern in ["build", "dist", "*.egg-info"]:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
                print(f"   Removed {path}")
            elif path.is_file():
                path.unlink()
                print(f"   Removed {path}")


def build_package():
    """Build the package."""
    print("📦 Building package...")
    
    if not run_command([sys.executable, "-m", "build"]):
        print("❌ Build failed")
        return False
    
    print("✅ Package built successfully")
    return True


def check_package():
    """Check the built package."""
    print("🔍 Checking package...")
    
    if not run_command([sys.executable, "-m", "twine", "check", "dist/*"]):
        print("❌ Package check failed")
        return False
    
    print("✅ Package check passed")
    return True


def upload_package(test=False):
    """Upload package to PyPI or TestPyPI."""
    if test:
        print("🚀 Uploading to TestPyPI...")
        repository = "--repository testpypi"
    else:
        print("🚀 Uploading to PyPI...")
        repository = ""
    
    cmd = [sys.executable, "-m", "twine", "upload"]
    if repository:
        cmd.extend(repository.split())
    cmd.append("dist/*")
    
    if not run_command(cmd):
        print("❌ Upload failed")
        return False
    
    if test:
        print("✅ Successfully uploaded to TestPyPI!")
        print("   Install with: pip install -i https://test.pypi.org/simple/ rota")
    else:
        print("✅ Successfully uploaded to PyPI!")
        print("   Install with: pip install rota")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Publish ROTA to PyPI")
    parser.add_argument("--test", action="store_true", 
                       help="Upload to TestPyPI instead of PyPI")
    parser.add_argument("--skip-build", action="store_true",
                       help="Skip building, just upload existing dist/")
    parser.add_argument("--skip-check", action="store_true",
                       help="Skip package checking")
    
    args = parser.parse_args()
    
    # Check if required tools are installed
    required_tools = ["build", "twine"]
    for tool in required_tools:
        if not run_command([sys.executable, "-m", tool, "--help"], check=False):
            print(f"❌ {tool} is not installed. Install with: pip install {tool}")
            return 1
    
    if not args.skip_build:
        # Clean and build
        clean_build()
        if not build_package():
            return 1
    
    if not args.skip_check:
        # Check package
        if not check_package():
            return 1
    
    # Upload
    if not upload_package(test=args.test):
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())