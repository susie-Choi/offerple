"""Command-line interface for ROTA (Real-time Operational Threat Assessment)."""
import argparse
import sys
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="rota",
        description="ROTA - Real-time Operational Threat Assessment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rota collect --source cve --output data/cve.jsonl
  rota predict --repo django/django --commit abc123
  rota validate --dataset data/cves.jsonl --output results/
  
For more information, visit: https://github.com/susie-Choi/rota
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect security data")
    collect_parser.add_argument("--source", choices=["cve", "github", "epss", "exploits"], 
                               required=True, help="Data source to collect from")
    collect_parser.add_argument("--output", type=Path, required=True, 
                               help="Output file path")
    collect_parser.add_argument("--config", type=Path, 
                               help="Configuration file path")
    
    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Predict vulnerability risk")
    predict_parser.add_argument("--repo", required=True, 
                               help="Repository in format owner/repo")
    predict_parser.add_argument("--commit", 
                               help="Specific commit SHA to analyze")
    predict_parser.add_argument("--output", type=Path, 
                               help="Output file for results")
    predict_parser.add_argument("--fast", action="store_true", 
                               help="Use fast prediction mode")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Run historical validation")
    validate_parser.add_argument("--dataset", type=Path, required=True, 
                                help="Path to CVE dataset")
    validate_parser.add_argument("--output", type=Path, required=True, 
                                help="Output directory for results")
    validate_parser.add_argument("--max-cves", type=int, 
                                help="Maximum number of CVEs to validate")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == "collect":
            return collect_main(args)
        elif args.command == "predict":
            return predict_main(args)
        elif args.command == "validate":
            return validate_main(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def collect_main(args):
    """Handle collect command."""
    print(f"🔍 Collecting {args.source} data to {args.output}")
    
    if args.source == "cve":
        from .scripts.collect_cve_data import main as collect_cve
        return collect_cve([str(args.output)])
    elif args.source == "github":
        print("GitHub data collection - use specific scripts for now")
        return 0
    elif args.source == "epss":
        from .scripts.collect_epss import main as collect_epss
        return collect_epss([str(args.output)])
    elif args.source == "exploits":
        from .scripts.collect_exploits import main as collect_exploits
        return collect_exploits([str(args.output)])
    
    return 0


def predict_main(args):
    """Handle predict command."""
    print(f"🎯 Analyzing repository: {args.repo}")
    
    if args.commit:
        print(f"   Specific commit: {args.commit}")
    
    if args.fast:
        from .prediction.signal_collectors.github_signals_fast import analyze_code_push
        result = analyze_code_push(args.repo, args.commit or "HEAD")
    else:
        print("Full prediction mode - not implemented yet")
        return 1
    
    if args.output:
        import json
        with args.output.open("w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"✅ Results saved to {args.output}")
    else:
        import json
        print(json.dumps(result, indent=2, default=str))
    
    return 0


def validate_main(args):
    """Handle validate command."""
    print(f"📊 Running historical validation")
    print(f"   Dataset: {args.dataset}")
    print(f"   Output: {args.output}")
    
    # Import and run validation
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
    
    try:
        from run_historical_validation import main as run_validation
        
        # Convert args to list format expected by the script
        script_args = [
            str(args.dataset),
            "--output-dir", str(args.output)
        ]
        
        if args.max_cves:
            script_args.extend(["--max-cves", str(args.max_cves)])
        
        return run_validation(script_args)
    except ImportError:
        print("❌ Validation script not found")
        return 1


if __name__ == "__main__":
    sys.exit(main())