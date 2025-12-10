"""
DEPRECATION: UpsetDetector migrated to keiba-ai

This module used to implement the UpsetDetector logic, but that functionality has
been migrated to keiba-ai. The full implementation was copied to
`migration/to_keiba_ai/src/utils/upset_detector.py` for reference.

This shim preserves a light-weight API so the main application doesn't break if
older callers still import `UpsetDetector`. It logs a deprecation warning and
returns an empty result set by default. For production usage, please run the
UpsetDetector logic inside keiba-ai and call it via an API or adapter.
"""
from typing import Dict, List, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UpsetDetector:
    """Shim for the migrated UpsetDetector.

    Behavior:
    - logs a warning when instantiated
    - `detect_upset_horses` returns an empty list to avoid unexpected runtime errors
      while preserving backward compatibility of imports.
    """

    def __init__(self):
        logger.warning("UpsetDetector is deprecated and has been migrated to keiba-ai. Use the keiba-ai service or the migration adapter.")

    def detect_upset_horses(self, race_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Preserve signature; do not run real detection in this shim
        return []

