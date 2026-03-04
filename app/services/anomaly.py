"""Weather anomaly detection."""

import logging
from datetime import datetime
from typing import Literal

import numpy as np
from app.database import WeatherDatabase
from app.models import Anomaly, WeatherConditions
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detect unusual weather patterns."""

    def __init__(self, db: WeatherDatabase):
        self.db = db

    async def detect_anomalies(self, current: WeatherConditions) -> list[Anomaly]:
        """Detect anomalies in current weather."""
        anomalies = []

        # Statistical anomalies
        stat_anomalies = await self._statistical_detection(current)
        anomalies.extend(stat_anomalies)

        # ML-based anomalies (if enough data)
        ml_anomalies = await self._ml_detection(current)
        if ml_anomalies:
            anomalies.extend(ml_anomalies)

        return anomalies

    async def _statistical_detection(self, current: WeatherConditions) -> list[Anomaly]:
        """Detect anomalies using statistical methods (z-score)."""
        anomalies = []

        # Check each metric
        metrics = {
            "temperature": current.temperature,
            "humidity": current.humidity,
            "pressure": current.pressure,
            "wind_speed": current.wind_speed,
        }

        for metric, value in metrics.items():
            try:
                # Get historical data
                data = await self.db.get_trends(metric, days=30)
                if len(data) < 7:
                    continue

                values = [float(row[metric]) for row in data if row[metric] is not None]
                mean = np.mean(values)
                std = np.std(values)

                if std == 0:
                    continue

                # Calculate z-score
                z_score = abs((value - mean) / std)

                # Detect anomaly if beyond 2.5 standard deviations
                if z_score > 2.5:
                    severity = self._calculate_severity(z_score)
                    description = self._generate_description(
                        metric, value, mean, z_score
                    )

                    anomalies.append(
                        Anomaly(
                            timestamp=datetime.now(),
                            metric=metric,
                            value=value,
                            expected_value=mean,
                            deviation=z_score,
                            severity=severity,
                            description=description,
                        )
                    )

            except Exception as e:
                logger.warning(f"Statistical detection failed for {metric}: {e}")

        return anomalies

    async def _ml_detection(self, current: WeatherConditions) -> list[Anomaly]:
        """Detect anomalies using Isolation Forest."""
        try:
            # Get historical data
            observations = await self.db.get_observations(days=30)

            if len(observations) < 50:
                logger.debug("Insufficient data for ML anomaly detection")
                return []

            # Prepare features
            features = []
            for obs in observations:
                features.append(
                    [
                        obs["temperature"],
                        obs["humidity"],
                        obs["pressure"],
                        obs["wind_speed"],
                    ]
                )

            # Current values
            current_features = [
                current.temperature,
                current.humidity,
                current.pressure,
                current.wind_speed,
            ]

            # Train Isolation Forest
            clf = IsolationForest(contamination=0.1, random_state=42)
            clf.fit(features)

            # Predict
            prediction = clf.predict([current_features])[0]

            # -1 means anomaly
            if prediction == -1:
                anomaly_score = clf.score_samples([current_features])[0]
                severity = "high" if anomaly_score < -0.5 else "medium"

                return [
                    Anomaly(
                        timestamp=datetime.now(),
                        metric="multivariate",
                        value=0,  # Not applicable for multivariate
                        expected_value=0,
                        deviation=abs(anomaly_score),
                        severity=severity,
                        description="Unusual combination of weather conditions detected by ML model",
                    )
                ]

            return []

        except Exception as e:
            logger.warning(f"ML anomaly detection failed: {e}")
            return []

    def _calculate_severity(self, z_score: float) -> Literal["low", "medium", "high", "critical"]:
        """Calculate anomaly severity based on z-score."""
        if z_score > 4:
            return "critical"
        elif z_score > 3.5:
            return "high"
        elif z_score > 3:
            return "medium"
        else:
            return "low"

    def _generate_description(self, metric: str, value: float, expected: float, z_score: float) -> str:
        """Generate human-readable anomaly description."""
        direction = "higher" if value > expected else "lower"
        percentage = abs((value - expected) / expected) * 100

        metric_names = {
            "temperature": "Temperature",
            "humidity": "Humidity",
            "pressure": "Pressure",
            "wind_speed": "Wind speed",
        }

        name = metric_names.get(metric, metric)
        return f"{name} is {direction} than usual by {percentage:.1f}% ({z_score:.1f} std devs)"
