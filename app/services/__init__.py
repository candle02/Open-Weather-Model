"""Weather forecast services."""

from app.services.aggregator import WeatherAggregator
from app.services.ai_summary import AISummaryService
from app.services.anomaly import AnomalyDetector
from app.services.ml_predict import MLPredictor
from app.services.recommendations import SmartHomeAdvisor
from app.services.trends import TrendAnalysis

__all__ = [
    "WeatherAggregator",
    "AISummaryService",
    "AnomalyDetector",
    "MLPredictor",
    "SmartHomeAdvisor",
    "TrendAnalysis",
]
