"""
LEGACY: TrackBiasAnalyzer (copied from keibabook src/utils/track_bias.py)
This file is a preserved legacy copy for reference; calculations should now happen
in the keiba-ai migration project. Keep for audit and reference.
"""
from typing import Dict, List, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TrackBiasAnalyzer:
    """Legacy TrackBiasAnalyzer preserved in migration repository."""
    def __init__(self):
        pass

    def calculate_bias_index(self, race_result: Dict[str, Any]) -> Dict[str, Any]:
        # Note: Copy of the original implementation retained for reference only.
        horses = race_result.get('horses', [])
        return {
            'inner_outer_bias': 0.0,
            'pace_bias': 0.0,
            'last_3f_bias': 50.0,
            'overall_bias_score': 0.0,
            'bias_type': 'データ不足',
            'confidence': 0.0
        }


def get_latest_bias() -> dict:
    # Minimal shim for legacy reference
    return None
