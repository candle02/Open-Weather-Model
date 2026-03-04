"""Pydantic models for weather forecasting service."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class WeatherConditions(BaseModel):
    """Current weather conditions."""

    temperature: float = Field(..., description="Temperature in Fahrenheit")
    feels_like: Optional[float] = Field(None, description="Feels like temperature")
    humidity: int = Field(..., ge=0, le=100, description="Humidity percentage")
    pressure: float = Field(..., description="Atmospheric pressure in hPa")
    wind_speed: float = Field(..., ge=0, description="Wind speed in mph")
    wind_direction: Optional[int] = Field(
        None, ge=0, le=360, description="Wind direction in degrees"
    )
    cloud_cover: int = Field(..., ge=0, le=100, description="Cloud cover percentage")
    visibility: Optional[float] = Field(None, description="Visibility in miles")
    conditions: str = Field(..., description="Weather conditions text")
    precipitation_prob: Optional[int] = Field(
        None, ge=0, le=100, description="Precipitation probability percentage"
    )
    precipitation_amount: Optional[float] = Field(
        None, ge=0, description="Precipitation amount in inches"
    )
    uv_index: Optional[int] = Field(None, ge=0, description="UV index")


class HourlyForecast(BaseModel):
    """Hourly forecast data."""

    timestamp: datetime
    conditions: WeatherConditions
    source: str = Field(..., description="Data source (e.g., weather.gov, open-meteo)")


class DailyForecast(BaseModel):
    """Daily forecast data."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    temp_high: float
    temp_low: float
    conditions: str
    precipitation_prob: int = Field(ge=0, le=100)
    summary: str
    source: str


class TrendData(BaseModel):
    """Weather trend analysis."""

    metric: str = Field(..., description="Metric being analyzed (e.g., temperature)")
    current_value: float
    avg_7day: float = Field(..., description="7-day moving average")
    avg_30day: float = Field(..., description="30-day moving average")
    change_7day: float = Field(..., description="Change from 7 days ago")
    change_30day: float = Field(..., description="Change from 30 days ago")
    trend: Literal["increasing", "decreasing", "stable"] = Field(
        ..., description="Overall trend direction"
    )
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")


class Anomaly(BaseModel):
    """Detected weather anomaly."""

    timestamp: datetime
    metric: str
    value: float
    expected_value: float
    deviation: float = Field(..., description="Standard deviations from normal")
    severity: Literal["low", "medium", "high", "critical"]
    description: str


class SmartHomeRecommendation(BaseModel):
    """Smart home automation recommendation."""

    trigger_time: datetime
    action: str = Field(..., description="Recommended action")
    reason: str = Field(..., description="Why this action is recommended")
    priority: Literal["low", "medium", "high"]
    automation_example: Optional[str] = Field(
        None, description="Example Home Assistant automation YAML"
    )


class MLPrediction(BaseModel):
    """Custom ML prediction."""

    timestamp: datetime
    metric: str
    predicted_value: float
    confidence_interval_low: float
    confidence_interval_high: float
    model_confidence: float = Field(ge=0, le=1)
    model_version: str


class AISummary(BaseModel):
    """AI-generated weather summary."""

    summary: str = Field(..., description="Natural language weather summary")
    key_points: list[str] = Field(
        default_factory=list, description="Key points to note"
    )
    warnings: list[str] = Field(default_factory=list, description="Weather warnings")
    generated_at: datetime = Field(default_factory=datetime.now)


class CurrentWeatherResponse(BaseModel):
    """Complete current weather response."""

    location: str
    latitude: float
    longitude: float
    timestamp: datetime
    conditions: WeatherConditions
    sources_used: list[str] = Field(
        default_factory=list, description="APIs that provided data"
    )
    ai_summary: Optional[AISummary] = None
    recommendations: list[SmartHomeRecommendation] = Field(default_factory=list)


class ForecastResponse(BaseModel):
    """Complete forecast response."""

    location: str
    latitude: float
    longitude: float
    timestamp: datetime
    current: WeatherConditions
    hourly: list[HourlyForecast] = Field(default_factory=list)
    daily: list[DailyForecast] = Field(default_factory=list)
    trends: list[TrendData] = Field(default_factory=list)
    anomalies: list[Anomaly] = Field(default_factory=list)
    ml_predictions: list[MLPrediction] = Field(default_factory=list)
    ai_summary: Optional[AISummary] = None
    recommendations: list[SmartHomeRecommendation] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime = Field(default_factory=datetime.now)
    services: dict[str, bool] = Field(
        default_factory=dict, description="Status of individual services"
    )
    database_connected: bool
    last_update: Optional[datetime] = None
    errors: list[str] = Field(default_factory=list)


class AccuracyMetrics(BaseModel):
    """Forecast accuracy metrics."""

    metric: str
    source: str
    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Square Error")
    mape: float = Field(..., description="Mean Absolute Percentage Error")
    samples: int = Field(..., description="Number of samples evaluated")
    period_days: int = Field(..., description="Evaluation period in days")
