"""Dataset statistics calculator."""
from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np


logger = logging.getLogger(__name__)


class DatasetStatistics:
    """Calculate comprehensive statistics for CVE dataset."""
    
    def __init__(self):
        """Initialize statistics calculator."""
        pass
    
    def calculate(self, cve_records: List[Dict]) -> Dict:
        """Calculate comprehensive statistics.
        
        Args:
            cve_records: List of CVE records
        
        Returns:
            Statistics dict
        """
        logger.info(f"Calculating statistics for {len(cve_records)} CVEs...")
        
        stats = {
            "total_cves": len(cve_records),
            "cvss_distribution": self._calculate_cvss_distribution(cve_records),
            "severity_distribution": self._calculate_severity_distribution(cve_records),
            "vulnerability_type_distribution": self._calculate_vuln_type_distribution(cve_records),
            "project_distribution": self._calculate_project_distribution(cve_records),
            "temporal_distribution": self._calculate_temporal_distribution(cve_records),
            "cwe_distribution": self._calculate_cwe_distribution(cve_records),
        }
        
        logger.info("Statistics calculation complete")
        return stats
    
    def _calculate_cvss_distribution(self, cve_records: List[Dict]) -> Dict:
        """Calculate CVSS score distribution.
        
        Args:
            cve_records: List of CVE records
        
        Returns:
            CVSS distribution dict
        """
        scores = [
            cve.get("cvss_score")
            for cve in cve_records
            if cve.get("cvss_score") is not None
        ]
        
        if not scores:
            return {}
        
        return {
            "min": float(np.min(scores)),
            "max": float(np.max(scores)),
            "mean": float(np.mean(scores)),
            "median": float(np.median(scores)),
            "std": float(np.std(scores)),
            "q25": float(np.percentile(scores, 25)),
            "q75": float(np.percentile(scores, 75)),
            "histogram": self._create_histogram(scores, bins=10),
        }
    
    def _calculate_severity_distribution(self, cve_records: List[Dict]) -> Dict:
        """Calculate severity distribution.
        
        Args:
            cve_records: List of CVE records
        
        Returns:
            Severity distribution dict
        """
        severities = [
            cve.get("severity")
            for cve in cve_records
            if cve.get("severity")
        ]
        
        counts = Counter(severities)
        total = sum(counts.values())
        
        return {
            "counts": dict(counts),
            "percentages": {
                sev: count / total * 100
                for sev, count in counts.items()
            } if total > 0 else {},
        }
    
    def _calculate_vuln_type_distribution(self, cve_records: List[Dict]) -> Dict:
        """Calculate vulnerability type distribution.
        
        Args:
            cve_records: List of CVE records
        
        Returns:
            Vulnerability type distribution dict
        """
        vuln_types = [
            cve.get("vulnerability_type")
            for cve in cve_records
            if cve.get("vulnerability_type")
        ]
        
        counts = Counter(vuln_types)
        total = sum(counts.values())
        
        return {
            "counts": dict(counts),
            "percentages": {
                vtype: count / total * 100
                for vtype, count in counts.items()
            } if total > 0 else {},
            "top_10": dict(counts.most_common(10)),
        }
    
    def _calculate_project_distribution(self, cve_records: List[Dict]) -> Dict:
        """Calculate project distribution.
        
        Args:
            cve_records: List of CVE records
        
        Returns:
            Project distribution dict
        """
        projects = [
            cve.get("project")
            for cve in cve_records
            if cve.get("project")
        ]
        
        counts = Counter(projects)
        total = sum(counts.values())
        
        return {
            "unique_projects": len(counts),
            "counts": dict(counts),
            "percentages": {
                proj: count / total * 100
                for proj, count in counts.items()
            } if total > 0 else {},
            "top_10": dict(counts.most_common(10)),
            "bottom_10": dict(counts.most_common()[:-11:-1]),
        }
    
    def _calculate_temporal_distribution(self, cve_records: List[Dict]) -> Dict:
        """Calculate temporal distribution.
        
        Args:
            cve_records: List of CVE records
        
        Returns:
            Temporal distribution dict
        """
        dates = []
        for cve in cve_records:
            pub_date = cve.get("published_date")
            if pub_date:
                try:
                    date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                    dates.append(date)
                except:
                    pass
        
        if not dates:
            return {}
        
        dates.sort()
        
        # Year distribution
        years = [d.year for d in dates]
        year_counts = Counter(years)
        
        # Month distribution
        months = [d.month for d in dates]
        month_counts = Counter(months)
        
        # Calculate time span
        time_span_days = (dates[-1] - dates[0]).days
        
        return {
            "earliest": dates[0].isoformat(),
            "latest": dates[-1].isoformat(),
            "time_span_days": time_span_days,
            "time_span_years": time_span_days / 365.25,
            "by_year": dict(sorted(year_counts.items())),
            "by_month": dict(sorted(month_counts.items())),
            "cves_per_year": len(dates) / (time_span_days / 365.25) if time_span_days > 0 else 0,
        }
    
    def _calculate_cwe_distribution(self, cve_records: List[Dict]) -> Dict:
        """Calculate CWE distribution.
        
        Args:
            cve_records: List of CVE records
        
        Returns:
            CWE distribution dict
        """
        all_cwes = []
        for cve in cve_records:
            cwes = cve.get("cwe_ids", [])
            all_cwes.extend(cwes)
        
        counts = Counter(all_cwes)
        total = sum(counts.values())
        
        return {
            "unique_cwes": len(counts),
            "total_cwe_mentions": total,
            "counts": dict(counts),
            "top_20": dict(counts.most_common(20)),
        }
    
    def _create_histogram(
        self,
        values: List[float],
        bins: int = 10,
    ) -> Dict:
        """Create histogram from values.
        
        Args:
            values: List of numeric values
            bins: Number of bins
        
        Returns:
            Histogram dict with bins and counts
        """
        hist, bin_edges = np.histogram(values, bins=bins)
        
        return {
            "bins": [
                {
                    "min": float(bin_edges[i]),
                    "max": float(bin_edges[i + 1]),
                    "count": int(hist[i]),
                }
                for i in range(len(hist))
            ],
        }
    
    def save(self, stats: Dict, output_file: Path) -> None:
        """Save statistics to file.
        
        Args:
            stats: Statistics dict
            output_file: Output file path
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Statistics saved to: {output_file}")
    
    def print_summary(self, stats: Dict) -> None:
        """Print statistics summary.
        
        Args:
            stats: Statistics dict
        """
        print("\n" + "=" * 80)
        print("Dataset Statistics Summary")
        print("=" * 80)
        
        print(f"\nTotal CVEs: {stats['total_cves']}")
        
        # CVSS
        cvss = stats.get("cvss_distribution", {})
        if cvss:
            print(f"\nCVSS Scores:")
            print(f"  Range: {cvss['min']:.1f} - {cvss['max']:.1f}")
            print(f"  Mean: {cvss['mean']:.2f} ± {cvss['std']:.2f}")
            print(f"  Median: {cvss['median']:.1f}")
        
        # Severity
        severity = stats.get("severity_distribution", {})
        if severity.get("counts"):
            print(f"\nSeverity Distribution:")
            for sev, count in sorted(
                severity["counts"].items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                pct = severity["percentages"].get(sev, 0)
                print(f"  {sev}: {count} ({pct:.1f}%)")
        
        # Vulnerability Types
        vuln_types = stats.get("vulnerability_type_distribution", {})
        if vuln_types.get("top_10"):
            print(f"\nTop Vulnerability Types:")
            for vtype, count in list(vuln_types["top_10"].items())[:5]:
                pct = vuln_types["percentages"].get(vtype, 0)
                print(f"  {vtype}: {count} ({pct:.1f}%)")
        
        # Projects
        projects = stats.get("project_distribution", {})
        if projects.get("top_10"):
            print(f"\nTop Projects:")
            for proj, count in list(projects["top_10"].items())[:5]:
                pct = projects["percentages"].get(proj, 0)
                print(f"  {proj}: {count} ({pct:.1f}%)")
        
        # Temporal
        temporal = stats.get("temporal_distribution", {})
        if temporal:
            print(f"\nTemporal Distribution:")
            print(f"  Time Span: {temporal.get('time_span_years', 0):.1f} years")
            print(f"  CVEs per Year: {temporal.get('cves_per_year', 0):.1f}")
            if temporal.get("by_year"):
                print(f"  Years: {min(temporal['by_year'].keys())} - {max(temporal['by_year'].keys())}")
        
        # CWE
        cwe = stats.get("cwe_distribution", {})
        if cwe:
            print(f"\nCWE Distribution:")
            print(f"  Unique CWEs: {cwe.get('unique_cwes', 0)}")
            if cwe.get("top_20"):
                print(f"  Top 5 CWEs:")
                for cwe_id, count in list(cwe["top_20"].items())[:5]:
                    print(f"    {cwe_id}: {count}")
        
        print("\n" + "=" * 80)
