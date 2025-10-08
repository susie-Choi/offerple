"""Configuration models and helpers for the Zero-Day Defense data pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import yaml


@dataclass(frozen=True)
class PackageDescriptor:
    """Describe a software package that should be monitored.

    Attributes:
        ecosystem: The package ecosystem, e.g. ``pypi``, ``npm``, ``maven``.
        name: The package identifier in the given ecosystem.
        repo_url: Optional source repository URL (GitHub preferred).
        metadata: Arbitrary metadata the pipeline should preserve in outputs.
    """

    ecosystem: str
    name: str
    repo_url: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class DataCollectionConfig:
    """Configuration for data collection runs."""

    cutoff_date: datetime
    output_dir: Path
    packages: List[PackageDescriptor]
    request_timeout: float = 15.0
    github_token: Optional[str] = None
    rate_limit_sleep: float = 1.0

    @staticmethod
    def from_dict(raw: dict, *, base_path: Optional[Path] = None) -> "DataCollectionConfig":
        cutoff_date = datetime.fromisoformat(raw["cutoff_date"])
        output_dir = Path(raw["output_dir"])
        if base_path is not None:
            output_dir = (base_path / output_dir).resolve()

        packages: Iterable[PackageDescriptor] = (
            PackageDescriptor(**pkg) for pkg in raw.get("packages", [])
        )
        return DataCollectionConfig(
            cutoff_date=cutoff_date,
            output_dir=output_dir,
            packages=list(packages),
            request_timeout=float(raw.get("request_timeout", 15.0)),
            github_token=raw.get("github_token"),
            rate_limit_sleep=float(raw.get("rate_limit_sleep", 1.0)),
        )


def load_config(path: Path) -> DataCollectionConfig:
    """Load configuration from a YAML file."""

    with path.open("r", encoding="utf-8") as fp:
        raw = yaml.safe_load(fp)
    return DataCollectionConfig.from_dict(raw, base_path=path.parent)


__all__ = ["PackageDescriptor", "DataCollectionConfig", "load_config"]
