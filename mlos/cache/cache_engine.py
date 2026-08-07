"""
Multi-Stage Cache Engine for ML-OS.

Caches dataset profiling, feature engineering, preprocessing, cross-validation,
and HPO results based on dataset fingerprints.

Author: Antigravity
License: MIT
"""

from pathlib import Path
from typing import Any

import joblib


class CacheEngine:
    """
    Caches intermediate AutoML stages in .mlos/cache/.
    """

    def __init__(self, workspace_root: Path | str = "."):
        self.workspace_root = Path(workspace_root)
        self.cache_dir = self.workspace_root / ".mlos" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Any | None:
        """Retrieve cached item by key."""
        target = self.cache_dir / f"{key}.cache"
        if target.exists():
            try:
                return joblib.load(target)
            except Exception:
                return None
        return None

    def set(self, key: str, value: Any) -> None:
        """Store item in cache by key."""
        target = self.cache_dir / f"{key}.cache"
        try:
            joblib.dump(value, target)
        except Exception:
            pass

    def clear(self) -> None:
        """Clear all cached items."""
        for item in self.cache_dir.glob("*.cache"):
            try:
                item.unlink()
            except Exception:
                pass
