"""Database operations for weather data storage."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class WeatherDatabase:
    """SQLite database for weather data."""

    def __init__(self, db_path: str = "./data/weather.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """Create database tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            # Current weather observations
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    feels_like REAL,
                    humidity INTEGER NOT NULL,
                    pressure REAL NOT NULL,
                    wind_speed REAL NOT NULL,
                    wind_direction INTEGER,
                    cloud_cover INTEGER NOT NULL,
                    visibility REAL,
                    conditions TEXT NOT NULL,
                    precipitation_prob INTEGER,
                    precipitation_amount REAL,
                    uv_index INTEGER,
                    source TEXT NOT NULL,
                    raw_data TEXT
                )
            """
            )

            # Forecasts (to compare accuracy later)
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    forecast_for TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    conditions TEXT NOT NULL,
                    precipitation_prob INTEGER,
                    source TEXT NOT NULL,
                    raw_data TEXT
                )
            """
            )

            # Anomalies
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    value REAL NOT NULL,
                    expected_value REAL NOT NULL,
                    deviation REAL NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL
                )
            """
            )

            # ML predictions
            await db.execute(
                """          CREATE TABLE IF NOT EXISTS ml_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    predicted_value REAL NOT NULL,
                    confidence_interval_low REAL NOT NULL,
                    confidence_interval_high REAL NOT NULL,
                    model_confidence REAL NOT NULL,
                    model_version TEXT NOT NULL
                )
            """
            )

            # Create indexes
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_obs_timestamp ON observations(timestamp)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_forecast_for ON forecasts(forecast_for)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_anomaly_timestamp ON anomalies(timestamp)"
            )

            await db.commit()
        logger.info(f"Database initialized at {self.db_path}")

    async def insert_observation(self, data: dict[str, Any]) -> None:
        """Insert a weather observation."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO observations (
                    timestamp, temperature, feels_like, humidity, pressure,
                    wind_speed, wind_direction, cloud_cover, visibility,
                    conditions, precipitation_prob, precipitation_amount,
                    uv_index, source, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data["timestamp"],
                    data["temperature"],
                    data.get("feels_like"),
                    data["humidity"],
                    data["pressure"],
                    data["wind_speed"],
                    data.get("wind_direction"),
                    data["cloud_cover"],
                    data.get("visibility"),
                    data["conditions"],
                    data.get("precipitation_prob"),
                    data.get("precipitation_amount"),
                    data.get("uv_index"),
                    data["source"],
                    json.dumps(data.get("raw_data", {})),
                ),
            )
            await db.commit()

    async def insert_forecast(self, created_at: str, forecast_for: str, data: dict[str, Any]) -> None:
        """Insert a forecast."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO forecasts (
                    created_at, forecast_for, temperature, conditions,
                    precipitation_prob, source, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    created_at,
                    forecast_for,
                    data["temperature"],
                    data["conditions"],
                    data.get("precipitation_prob"),
                    data["source"],
                    json.dumps(data.get("raw_data", {})),
                ),
            )
            await db.commit()

    async def insert_anomaly(self, data: dict[str, Any]) -> None:
        """Insert an anomaly."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO anomalies (
                    timestamp, metric, value, expected_value, deviation,
                    severity, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data["timestamp"],
                    data["metric"],
                    data["value"],
                    data["expected_value"],
                    data["deviation"],
                    data["severity"],
                    data["description"],
                ),
            )
            await db.commit()

    async def get_observations(
        self, days: int = 7, metric: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Get historical observations."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM observations WHERE timestamp > ? ORDER BY timestamp DESC"
            async with db.execute(query, (cutoff,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_trends(self, metric: str, days: int = 30) -> dict[str, Any]:
        """Calculate trend data for a metric."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = f"SELECT timestamp, {metric} FROM observations WHERE timestamp > ? ORDER BY timestamp ASC"
            async with db.execute(query, (cutoff,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_anomalies(self, days: int = 7) -> list[dict[str, Any]]:
        """Get recent anomalies."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM anomalies WHERE timestamp > ? ORDER BY timestamp DESC"
            async with db.execute(query, (cutoff,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def cleanup_old_data(self, retention_days: int = 365) -> int:
        """Delete old data beyond retention period."""
        cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM observations WHERE timestamp < ?", (cutoff,)
            )
            deleted = cursor.rowcount
            await db.execute("DELETE FROM forecasts WHERE created_at < ?", (cutoff,))
            await db.execute("DELETE FROM anomalies WHERE timestamp < ?", (cutoff,))
            await db.commit()
            logger.info(f"Cleaned up {deleted} old records")
            return deleted

    async def get_last_update(self) -> Optional[datetime]:
        """Get timestamp of last observation."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT MAX(timestamp) as last_time FROM observations"
            ) as cursor:
                row = await cursor.fetchone()
                if row and row["last_time"]:
                    return datetime.fromisoformat(row["last_time"])
                return None
