"""Weather trend analysis."""

import logging
from datetime import datetime, timedelta
from typing import Any, Literal

import numpy as np
from app.database import WeatherDatabase
from app.models import TrendData

logger = logging.getLogger(__name__)


class TrendAnalysis:
    """Analyze weather trends from historical data."""

    def __init__(self, db: WeatherDatabase):
        self.db = db

    async def analyze_trends(self, metrics: list[str] = None) -> list[TrendData]:
        """Analyze trends for specified metrics."""
        if metrics is None:
            metrics = ["temperature", "humidity", "pressure", "wind_speed"]

        trends = []
        for metric in metrics:
            try:
                trend = await self._analyze_metric(metric)
                if trend:
                    trends.append(trend)
            except Exception as e:
                logger.warning(f"Trend analysis failed for {metric}: {e}")

        return trends

    async def _analyze_metric(self, metric: str) -> TrendData | None:
        """Analyze trend for a single metric."""
        # Get 30 days of data
        data = await self.db.get_trends(metric, days=30)

        if len(data) < 7:
            logger.warning(f"Insufficient data for {metric} trend analysis")
            return None

        values = [float(row[metric]) for row in data if row[metric] is not None]

        if not values:
            return None

        # Current value (most recent)
        current_value = values[-1]

        # Moving averages
        avg_7day = np.mean(values[-7:]) if len(values) >= 7 else current_value
        avg_30day = np.mean(values)

        # Calculate changes
        change_7day = current_value - values[-7] if len(values) >= 7 else 0
        change_30day = current_value - values[0] if len(values) > 1 else 0

        # Determine trend direction
        trend_direction = self._determine_trend(values)

        # Calculate confidence based on consistency
        confidence = self._calculate_confidence(values)

        return TrendData(
            metric=metric,
            current_value=current_value,
            avg_7day=avg_7day,
            avg_30day=avg_30day,
            change_7day=change_7day,
            change_30day=change_30day,
            trend=trend_direction,
            confidence=confidence,
        )

    def _determine_trend(
        self, values: list[float]
    ) -> Literal["increasing", "decreasing", "stable"]:
        """Determine overall trend direction."""
        if len(values) < 2:
            return "stable"

        # Simple linear regression
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)

        # Threshold for stability
        threshold = np.std(values) * 0.1

        if slope > threshold:
            return "increasing"
        elif slope < -threshold:
            return "decreasing"
        else:
            return "stable"

    def _calculate_confidence(self, values: list[float]) -> float:
        """Calculate confidence score based on data consistency."""
        if len(values) < 2:
            return 0.5

        # Use coefficient of variation (CV) inverted
        mean = np.mean(values)
        std = np.std(values)

        if mean == 0:
            return 0.5

        cv = std / abs(mean)
        # Normalize to 0-1 range (lower CV = higher confidence)
        confidence = max(0.0, min(1.0, 1 - cv))

        return confidence
