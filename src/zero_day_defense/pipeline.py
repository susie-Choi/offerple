"""Data collection pipeline orchestration."""
from __future__ import annotations

import json
from typing import Dict, Iterable, List

from tqdm import tqdm

from .config import DataCollectionConfig, PackageDescriptor
from .data_sources.github import GitHubDataSource
from .data_sources.maven import MavenCentralDataSource
from .data_sources.base import SourceResult
from .data_sources.npm import NPMDataSource
from .data_sources.pypi import PyPIDataSource


class DataCollectionPipeline:
    """Run data collection across multiple ecosystems."""

    def __init__(self, config: DataCollectionConfig) -> None:
        self.config = config
        self.sources = {
            "pypi": PyPIDataSource(
                timeout=config.request_timeout,
                rate_limit_sleep=config.rate_limit_sleep,
            ),
            "npm": NPMDataSource(
                timeout=config.request_timeout,
                rate_limit_sleep=config.rate_limit_sleep,
            ),
            "maven": MavenCentralDataSource(
                timeout=config.request_timeout,
                rate_limit_sleep=config.rate_limit_sleep,
            ),
            "github": GitHubDataSource(
                token=config.github_token,
                timeout=config.request_timeout,
                rate_limit_sleep=config.rate_limit_sleep,
            ),
        }

    def run(self) -> List[SourceResult]:
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        results: List[SourceResult] = []
        for package in tqdm(self.config.packages, desc="Collecting", unit="package"):
            results.extend(self._collect_for_package(package))
        self._write_results(results)
        return results

    def _collect_for_package(self, package: PackageDescriptor) -> List[SourceResult]:
        outputs: List[SourceResult] = []
        if package.ecosystem in {"pypi", "npm", "maven"}:
            outputs.append(
                self.sources[package.ecosystem].collect(package.name, cutoff=self.config.cutoff_date)
            )
        if package.repo_url:
            outputs.append(
                self.sources["github"].collect(package.repo_url, cutoff=self.config.cutoff_date)
            )
        return outputs

    def _write_results(self, results: Iterable[SourceResult]) -> None:
        grouped: Dict[str, List[SourceResult]] = {}
        for result in results:
            grouped.setdefault(result.package, []).append(result)
        for package, package_results in grouped.items():
            file_path = self.config.output_dir / f"{package.replace('/', '_')}.jsonl"
            with file_path.open("w", encoding="utf-8") as fp:
                for result in package_results:
                    fp.write(json.dumps(self._serialize_result(result)) + "\n")

    @staticmethod
    def _serialize_result(result: SourceResult) -> Dict[str, object]:
        return {
            "source": result.source,
            "package": result.package,
            "collected_at": result.collected_at.isoformat(),
            "payload": result.payload,
        }


def create_pipeline(config: DataCollectionConfig) -> DataCollectionPipeline:
    return DataCollectionPipeline(config)


__all__ = ["DataCollectionPipeline", "create_pipeline"]
