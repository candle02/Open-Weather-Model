"""AI-powered weather summary generation using Ollama or OpenAI-compatible APIs."""

import logging
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.models.openai import OpenAIModel

from app.models import (
    AISummary,
    Anomaly,
    DailyForecast,
    HourlyForecast,
    WeatherConditions,
)

logger = logging.getLogger(__name__)


class AISummaryService:
    """Generate natural language weather summaries using LLM."""

    def __init__(
        self,
        provider: Literal["ollama", "openai"] = "ollama",
        model: str = "llama3.2:3b",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize AI summary service.
        
        Args:
            provider: "ollama" for local Ollama or "openai" for OpenAI-compatible API
            model: Model name (e.g., "llama3.2:3b" for Ollama, "gpt-3.5-turbo" for OpenAI)
            base_url: Base URL for the API (e.g., "http://localhost:11434" for Ollama)
            api_key: API key (only needed for OpenAI-compatible APIs)
        """
        if provider == "ollama":
            self.model = OllamaModel(
                model_name=model,
                base_url=base_url or "http://localhost:11434",
            )
            logger.info(f"Using Ollama model: {model} at {base_url}")
        else:  # openai
            self.model = OpenAIModel(
                model,
                base_url=base_url,
                api_key=api_key,
            )
            logger.info(f"Using OpenAI-compatible model: {model}")
        
        self.agent = Agent(
            self.model,
            system_prompt="""
            You are a friendly weather assistant. Generate concise, helpful weather summaries
            that highlight key information people need to know. Include:
            - Current conditions in plain language
            - Notable changes or trends
            - Practical advice (e.g., "bring an umbrella", "dress warm")
            - Any warnings about unusual weather

            Keep summaries under 3 sentences for brevity.
            """,
        )

    async def generate_summary(
        self,
        current: WeatherConditions,
        hourly: list[HourlyForecast] | None = None,
        daily: list[DailyForecast] | None = None,
        anomalies: list[Anomaly] | None = None,
    ) -> AISummary:
        """Generate comprehensive weather summary."""
        # Build context for LLM
        context = self._build_context(current, hourly, daily, anomalies)

        try:
            # Generate summary
            result = await self.agent.run(f"Summarize this weather data: {context}")
            summary_text = result.data

            # Extract key points
            key_points = await self._extract_key_points(context)

            # Extract warnings
            warnings = await self._extract_warnings(current, anomalies or [])

            return AISummary(
                summary=summary_text,
                key_points=key_points,
                warnings=warnings,
                generated_at=datetime.now(),
            )

        except Exception as e:
            logger.warning(f"AI summary generation failed: {e}")
            # Fallback to simple summary (AI is optional)
            return self._fallback_summary(current)

    def _build_context(self, current: WeatherConditions, hourly: list[HourlyForecast] | None, daily: list[DailyForecast] | None, anomalies: list[Anomaly] | None) -> str:
        """Build context string for LLM."""
        context = f"Current: {current.temperature:.1f}°F, {current.conditions}, "
        context += f"humidity {current.humidity}%, wind {current.wind_speed:.1f} mph. "

        if hourly and len(hourly) > 0:
            next_hour = hourly[0]
            context += f"Next hour: {next_hour.conditions.temperature:.1f}°F, {next_hour.conditions.conditions}. "

        if daily and len(daily) > 0:
            today = daily[0]
            context += f"Today: High {today.temp_high:.1f}°F, Low {today.temp_low:.1f}°F, {today.conditions}. "

        if anomalies:
            context += f"Anomalies detected: {len(anomalies)} unusual patterns. "

        return context

    async def _extract_key_points(self, context: str) -> list[str]:
        """Extract key points from weather data."""
        try:
            prompt = f"List 3 key weather points from: {context}. Return as bullet points."
            result = await self.agent.run(prompt)
            # Parse bullet points
            points = [
                line.strip().lstrip("-*•").strip()
                for line in result.data.split("\n")
                if line.strip()
            ]
            return points[:3]  # Limit to 3
        except Exception as e:
            logger.warning(f"Key points extraction failed: {e}")
            return []

    async def _extract_warnings(self, current: WeatherConditions, anomalies: list[Anomaly]) -> list[str]:
        """Extract weather warnings."""
        warnings = []

        # Temperature extremes
        if current.temperature > 95:
            warnings.append("Extreme heat - stay hydrated and avoid sun")
        elif current.temperature < 32:
            warnings.append("Freezing temperatures - protect pipes and plants")

        # High winds
        if current.wind_speed > 25:
            warnings.append("High winds - secure outdoor items")

        # Poor visibility
        if current.visibility and current.visibility < 1:
            warnings.append("Low visibility - drive carefully")

        # Precipitation
        if current.precipitation_prob and current.precipitation_prob > 70:
            warnings.append("Heavy precipitation likely")

        # Anomaly warnings
        critical_anomalies = [a for a in anomalies if a.severity in ["high", "critical"]]
        if critical_anomalies:
            warnings.append(
                f"Unusual weather detected: {critical_anomalies[0].description}"
            )

        return warnings

    def _fallback_summary(self, current: WeatherConditions) -> AISummary:
        """Generate simple summary when AI fails."""
        summary = (
            f"Currently {current.temperature:.1f}°F with {current.conditions.lower()}. "
            f"Humidity at {current.humidity}% and winds at {current.wind_speed:.1f} mph."
        )

        key_points = [
            f"Temperature: {current.temperature:.1f}°F",
            f"Conditions: {current.conditions}",
            f"Humidity: {current.humidity}%",
        ]

        return AISummary(
            summary=summary, key_points=key_points, warnings=[], generated_at=datetime.now()
        )
