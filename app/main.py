"""Main FastAPI application for AI weather forecasting."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.database import WeatherDatabase
from app.models import (
    AccuracyMetrics,
    CurrentWeatherResponse,
    ForecastResponse,
    HealthResponse,
)
from app.services import (
    AISummaryService,
    AnomalyDetector,
    MLPredictor,
    SmartHomeAdvisor,
    TrendAnalysis,
    WeatherAggregator,
)

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Location
    latitude: float
    longitude: float
    location_name: str

    # LLM Configuration
    llm_provider: str = "ollama"  # "ollama" or "openai"
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    
    # OpenAI-compatible settings (optional)
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-3.5-turbo"

    # Database
    database_path: str = "./data/weather.db"

    # Update intervals
    update_interval: int = 10  # minutes
    ml_retrain_interval: int = 24  # hours
    history_retention_days: int = 365

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"


# Global instances
settings = Settings()
db = WeatherDatabase(settings.database_path)
aggregator: Optional[WeatherAggregator] = None
ai_summary: Optional[AISummaryService] = None
anomal_detector: Optional[AnomalyDetector] = None
ml_predictor: Optional[MLPredictor] = None
recommendations: Optional[SmartHomeAdvisor] = None
trends: Optional[TrendAnalysis] = None
scheduler: Optional[AsyncIOScheduler] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    global aggregator, ai_summary, anomal_detector, ml_predictor, recommendations, trends, scheduler

    logger.info("Starting Weather Forecast Service...")

    # Initialize database
    await db.initialize()

    # Initialize services
    aggregator = WeatherAggregator(
        settings.latitude, settings.longitude, settings.location_name
    )
    
    # Initialize AI summary service based on provider
    if settings.llm_provider == "ollama":
        ai_summary = AISummaryService(
            provider="ollama",
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )
        logger.info(f"Using Ollama at {settings.ollama_base_url} with model {settings.ollama_model}")
    else:
        ai_summary = AISummaryService(
            provider="openai",
            model=settings.openai_model,
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
        )
        logger.info(f"Using OpenAI-compatible API with model {settings.openai_model}")
    
    anomal_detector = AnomalyDetector(db)
    ml_predictor = MLPredictor(db)
    recommendations = SmartHomeAdvisor()
    trends = TrendAnalysis(db)

    # Start scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        update_weather, "interval", minutes=settings.update_interval, id="weather_update"
    )
    scheduler.add_job(
        retrain_ml_models,
        "interval",
        hours=settings.ml_retrain_interval,
        id="ml_retrain",
    )
    scheduler.add_job(
        cleanup_old_data, "interval", days=1, id="cleanup"
    )
    scheduler.start()

    # Initial update
    await update_weather()

    logger.info("Weather Forecast Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Weather Forecast Service...")
    if scheduler:
        scheduler.shutdown()
    if aggregator:
        await aggregator.close()


app = FastAPI(
    title="AI Weather Forecast",
    description="Multi-source weather aggregation with AI insights and ML predictions",
    version="1.0.0",
    lifespan=lifespan,
)

# Setup static files and templates
Path("app/static").mkdir(parents=True, exist_ok=True)
Path("app/templates").mkdir(parents=True, exist_ok=True)

# Uncomment when static files exist
# app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# Background tasks
async def update_weather() -> None:
    """Update weather data from all sources."""
    try:
        logger.info("Updating weather data...")

        # Get current conditions
        current, sources = await aggregator.get_current_conditions()

        # Store observation
        await db.insert_observation(
            {
                "timestamp": datetime.now().isoformat(),
                "temperature": current.temperature,
                "feels_like": current.feels_like,
                "humidity": current.humidity,
                "pressure": current.pressure,
                "wind_speed": current.wind_speed,
                "wind_direction": current.wind_direction,
                "cloud_cover": current.cloud_cover,
                "visibility": current.visibility,
                "conditions": current.conditions,
                "precipitation_prob": current.precipitation_prob,
                "precipitation_amount": current.precipitation_amount,
                "uv_index": current.uv_index,
                "source": ",".join(sources),
            }
        )

        # Detect anomalies
        anomalies = await anomal_detector.detect_anomalies(current)
        for anomaly in anomalies:
            await db.insert_anomaly(
                {
                    "timestamp": anomaly.timestamp.isoformat(),
                    "metric": anomaly.metric,
                    "value": anomaly.value,
                    "expected_value": anomaly.expected_value,
                    "deviation": anomaly.deviation,
                    "severity": anomaly.severity,
                    "description": anomaly.description,
                }
            )

        logger.info(f"Weather update complete. Sources: {', '.join(sources)}")

    except Exception as e:
        logger.error(f"Weather update failed: {e}")


async def retrain_ml_models() -> None:
    """Retrain ML models on updated historical data."""
    try:
        logger.info("Retraining ML models...")
        success = await ml_predictor.train_models()
        if success:
            logger.info("ML models retrained successfully")
        else:
            logger.warning("ML model retraining skipped (insufficient data)")
    except Exception as e:
        logger.error(f"ML retraining failed: {e}")


async def cleanup_old_data() -> None:
    """Clean up old data beyond retention period."""
    try:
        deleted = await db.cleanup_old_data(settings.history_retention_days)
        logger.info(f"Cleaned up {deleted} old records")
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")


# API Endpoints


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/current", response_model=CurrentWeatherResponse)
async def get_current_weather():
    """Get current weather with AI insights."""
    try:
        # Get current conditions
        current, sources = await aggregator.get_current_conditions()

        # Get anomalies
        anomalies = await anomal_detector.detect_anomalies(current)

        # Generate AI summary
        summary = await ai_summary.generate_summary(current, anomalies=anomalies)

        # Get recommendations
        hourly = await aggregator.get_hourly_forecast(hours=6)
        recs = await recommendations.generate_recommendations(
            current, hourly=hourly, anomalies=anomalies
        )

        return CurrentWeatherResponse(
            location=settings.location_name,
            latitude=settings.latitude,
            longitude=settings.longitude,
            timestamp=datetime.now(),
            conditions=current,
            sources_used=sources,
            ai_summary=summary,
            recommendations=recs,
        )

    except Exception as e:
        logger.error(f"Get current weather failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast", response_model=ForecastResponse)
async def get_forecast():
    """Get full forecast with trends and predictions."""
    try:
        # Get all data
        current, sources = await aggregator.get_current_conditions()
        hourly = await aggregator.get_hourly_forecast(hours=48)
        daily = await aggregator.get_daily_forecast(days=7)

        # Analyze trends
        trend_data = await trends.analyze_trends()

        # Detect anomalies
        anomalies = await anomal_detector.detect_anomalies(current)

        # ML predictions
        ml_predictions = await ml_predictor.predict(metric="temperature", hours_ahead=24)

        # AI summary
        summary = await ai_summary.generate_summary(
            current, hourly=hourly, daily=daily, anomalies=anomalies
        )

        # Recommendations
        recs = await recommendations.generate_recommendations(
            current, hourly=hourly, daily=daily, anomalies=anomalies
        )

        return ForecastResponse(
            location=settings.location_name,
            latitude=settings.latitude,
            longitude=settings.longitude,
            timestamp=datetime.now(),
            current=current,
            hourly=hourly,
            daily=daily,
            trends=trend_data,
            anomalies=anomalies,
            ml_predictions=ml_predictions,
            ai_summary=summary,
            recommendations=recs,
        )

    except Exception as e:
        logger.error(f"Get forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/historical")
async def get_historical(days: int = 7):
    """Get historical weather data."""
    try:
        observations = await db.get_observations(days=days)
        return {"observations": observations, "count": len(observations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trends")
async def get_trends():
    """Get trend analysis."""
    try:
        trend_data = await trends.analyze_trends()
        return {"trends": trend_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/anomalies")
async def get_anomalies(days: int = 7):
    """Get detected anomalies."""
    try:
        anomalies = await db.get_anomalies(days=days)
        return {"anomalies": anomalies, "count": len(anomalies)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommendations")
async def get_recommendations():
    """Get smart home recommendations."""
    try:
        current, _ = await aggregator.get_current_conditions()
        hourly = await aggregator.get_hourly_forecast(hours=6)
        daily = await aggregator.get_daily_forecast(days=1)
        anomalies = await anomal_detector.detect_anomalies(current)

        recs = await recommendations.generate_recommendations(
            current, hourly=hourly, daily=daily, anomalies=anomalies
        )

        return {"recommendations": recs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhook/forecast")
async def webhook_forecast():
    """Webhook endpoint for N8n integration."""
    try:
        # Return current + forecast for N8n workflows
        current, sources = await aggregator.get_current_conditions()
        hourly = await aggregator.get_hourly_forecast(hours=24)
        anomalies = await anomal_detector.detect_anomalies(current)
        summary = await ai_summary.generate_summary(current, hourly=hourly, anomalies=anomalies)
        recs = await recommendations.generate_recommendations(current, hourly=hourly, anomalies=anomalies)

        return {
            "timestamp": datetime.now().isoformat(),
            "location": settings.location_name,
            "current": current.model_dump(),
            "hourly_forecast": [h.model_dump() for h in hourly[:6]],  # Next 6 hours
            "ai_summary": summary.model_dump(),
            "recommendations": [r.model_dump() for r in recs],
            "anomalies": [a.model_dump() for a in anomalies],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/train")
async def manual_train():
    """Manually trigger ML model training."""
    try:
        success = await ml_predictor.train_models()
        return {"success": success, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    errors = []
    services = {}

    # Check database
    try:
        last_update = await db.get_last_update()
        services["database"] = True
    except Exception as e:
        services["database"] = False
        errors.append(f"Database error: {str(e)}")
        last_update = None

    # Check aggregator
    try:
        if aggregator:
            services["weather_aggregator"] = True
        else:
            services["weather_aggregator"] = False
            errors.append("Weather aggregator not initialized")
    except Exception as e:
        services["weather_aggregator"] = False
        errors.append(f"Aggregator error: {str(e)}")

    # Determine overall status
    if not errors:
        status = "healthy"
    elif services.get("database") and services.get("weather_aggregator"):
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        services=services,
        database_connected=services.get("database", False),
        last_update=last_update,
        errors=errors,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=True,
    )
