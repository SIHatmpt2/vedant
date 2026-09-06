"""Resilient weighted risk calculation independent of input module availability."""
import logging
from typing import Any
from ..constants import RISK_WEIGHTS, UNCERTAINTY_BY_SIGNALS
logger = logging.getLogger(__name__)


class RiskEngine:
    """Calculate weighted risk with confidence proportional to available evidence."""
    @staticmethod
    def calculate(signals: dict[str, Any]) -> dict[str, Any]:
        """Return score, level, confidence, uncertainty and raw signal breakdown."""
        breakdown = {name: signals.get(name) for name in RISK_WEIGHTS}
        available = {name: float(value) for name, value in breakdown.items() if value is not None}
        weights = sum(RISK_WEIGHTS[name] for name in available)
        if not available:
            result = {"risk_score": 0, "risk_level": "Unknown", "confidence": 0.0, "uncertainty": "critical", "breakdown": breakdown}
        else:
            raw = sum(available[name] * RISK_WEIGHTS[name] for name in available) / weights
            confidence = round(weights, 2)
            # Low confidence tempers rather than inventing evidence.
            adjusted = round(raw * (0.75 + 0.25 * confidence))
            level = "Severe" if adjusted >= 80 else "High" if adjusted >= 60 else "Moderate" if adjusted >= 35 else "Low"
            result = {"risk_score": min(100, adjusted), "risk_level": level, "confidence": confidence, "uncertainty": UNCERTAINTY_BY_SIGNALS[len(available)], "breakdown": breakdown}
        logger.info("risk_calculated", extra={"score": result["risk_score"], "confidence": result["confidence"]})
        return result
