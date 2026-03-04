"""Custom ML predictions using Prophet for time series forecasting."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from app.database import WeatherDatabase
from app.models import MLPrediction
from prophet import Prophet

logger = logging.getLogger(__name__)


class MLPredictor:
    """Custom ML predictions for weather metrics."""

    def __init__(self, db: WeatherDatabase, models_dir: str = "./models"):
        self.db = db
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.model_version = "v1.0"

    async def train_models(self) -> bool:
        """Train Prophet models on historical data."""
        try:
            # Get historical data (need at least 14 days for Prophet)
            observations = await self.db.get_observations(days=60)

            if len(observations) < 14:
                logger.warning("Insufficient data to train ML models (need 14+ days)")
                return False

            # Train model for temperature
            await self._train_temperature_model(observations)

            logger.info("ML models trained successfully")
            return True

        except Exception as e:
            logger.error(f"ML model training failed: {e}")
            return False

    async def predict(self, metric: str = "temperature", hours_ahead: int = 24) -> list[MLPrediction]:
        """Generate ML predictions."""
        try:
            # Check if we have enough data
            observations = await self.db.get_observations(days=30)
            if len(observations) < 14:
                logger.warning("Insufficient data for ML predictions")
                return []

            # Generate predictions based on metric
            if metric == "temperature":
                return await self._predict_temperature(observations, hours_ahead)
            else:
                logger.warning(f"Predictions not yet implemented for {metric}")
                return []

        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return []

    async def _train_temperature_model(self, observations: list[dict]) -> None:
        """Train Prophet model for temperature."""
        # Prepare data for Prophet
        df = pd.DataFrame(observations)
        df["ds"] = pd.to_datetime(df["timestamp"])
        df["y"] = df["temperature"]
        df = df[["ds", "y"]].dropna()

        if len(df) < 14:
            raise ValueError("Need at least 14 days of data")

        # Train Prophet model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,  # Not enough data
            changepoint_prior_scale=0.05,
        )

        # Suppress Prophet's verbose output
        import logging as prophet_logging

        prophet_logging.getLogger("prophet").setLevel(prophet_logging.WARNING)

        model.fit(df)

        # Save model
        model_path = self.models_dir / "temperature_model.json"
        import json

        with open(model_path, "w") as f:
            json.dump(model.to_json(), f)

        logger.info(f"Temperature model trained and saved to {model_path}")

    async def _predict_temperature(
        self, observations: list[dict], hours_ahead: int
    ) -> list[MLPrediction]:
        """Predict temperature using Prophet."""
        # Prepare data
        df = pd.DataFrame(observations)
        df["ds"] = pd.to_datetime(df["timestamp"])
        df["y"] = df["temperature"]
        df = df[["ds", "y"]].dropna()

        # Train quick model (or load if exists)
        model_path = self.models_dir / "temperature_model.json"

        import logging as prophet_logging

        prophet_logging.getLogger("prophet").setLevel(prophet_logging.WARNING)

        if model_path.exists():
            # Load existing model
            import json

            with open(model_path) as f:
                model = Prophet.from_json(json.load(f))
        else:
            # Train new model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=False,
            )
            model.fit(df)

        # Make predictions
        future = model.make_future_dataframe(periods=hours_ahead, freq="h")
        forecast = model.predict(future)

        # Extract predictions for future hours
        predictions = []
        now = datetime.now()

        # Get only future predictions
        future_forecast = forecast[forecast["ds"] > now].head(hours_ahead)

        for _, row in future_forecast.iterrows():
            # Calculate model confidence based on interval width
            interval_width = row["yhat_upper"] - row["yhat_lower"]
            # Normalize to 0-1 (narrower interval = higher confidence)
            confidence = max(0.0, min(1.0, 1 - (interval_width / 50)))

            predictions.append(
                MLPrediction(
                    timestamp=row["ds"].to_pydatetime(),
                    metric="temperature",
                    predicted_value=row["yhat"],
                    confidence_interval_low=row["yhat_lower"],
                    confidence_interval_high=row["yhat_upper"],
                    model_confidence=confidence,
                    model_version=self.model_version,
                )
            )

        return predictions
