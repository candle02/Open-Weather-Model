"""Smart home automation recommendations based on weather."""

import logging
from datetime import datetime, timedelta
from typing import Literal

from app.models import (
    Anomaly,
    DailyForecast,
    HourlyForecast,
    SmartHomeRecommendation,
    WeatherConditions,
)

logger = logging.getLogger(__name__)


class SmartHomeAdvisor:
    """Generate smart home automation recommendations."""

    async def generate_recommendations(
        self,
        current: WeatherConditions,
        hourly: list[HourlyForecast] | None = None,
        daily: list[DailyForecast] | None = None,
        anomalies: list[Anomaly] | None = None,
    ) -> list[SmartHomeRecommendation]:
        """Generate automation recommendations based on weather."""
        recommendations = []

        # Temperature-based recommendations
        recommendations.extend(self._temperature_recommendations(current, hourly))

        # Precipitation recommendations
        recommendations.extend(self._precipitation_recommendations(current, hourly))

        # Wind recommendations
        recommendations.extend(self._wind_recommendations(current))

        # Sun/UV recommendations
        recommendations.extend(self._sun_recommendations(current))

        # Anomaly-based recommendations
        if anomalies:
            recommendations.extend(self._anomaly_recommendations(anomalies))

        # Sort by priority
        recommendations.sort(key=lambda r: {"high": 0, "medium": 1, "low": 2}[r.priority])

        return recommendations

    def _temperature_recommendations(
        self, current: WeatherConditions, hourly: list[HourlyForecast] | None
    ) -> list[SmartHomeRecommendation]:
        """Temperature-based recommendations."""
        recs = []
        now = datetime.now()

        # Extreme heat
        if current.temperature > 85:
            recs.append(
                SmartHomeRecommendation(
                    trigger_time=now,
                    action="Pre-cool home before peak heat",
                    reason=f"Temperature is {current.temperature:.1f}°F and rising",
                    priority="high",
                    automation_example="""
automation:
  - alias: "Pre-cool before heat"
    trigger:
      - platform: numeric_state
        entity_id: sensor.outdoor_temperature
        above: 85
    action:
      - service: climate.set_temperature
        data:
          entity_id: climate.thermostat
          temperature: 72
""",
                )
            )

        # Freezing temps
        if current.temperature < 32:
            recs.append(
                SmartHomeRecommendation(
                    trigger_time=now,
                    action="Protect outdoor plants and pipes",
                    reason=f"Freezing temperature: {current.temperature:.1f}°F",
                    priority="high",
                    automation_example="""
automation:
  - alias: "Freeze warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.outdoor_temperature
        below: 32
    action:
      - service: notify.mobile_app
        data:
          message: "Freezing temps! Protect plants and pipes"
""",
                )
            )

        # Check hourly for temperature swings
        if hourly and len(hourly) >= 6:
            temps = [h.conditions.temperature for h in hourly[:6]]
            temp_range = max(temps) - min(temps)

            if temp_range > 20:
                recs.append(
                    SmartHomeRecommendation(
                        trigger_time=now + timedelta(hours=3),
                        action="Adjust thermostat for temperature swing",
                        reason=f"Expected {temp_range:.1f}°F temperature change in next 6 hours",
                        priority="medium",
                        automation_example=None,
                    )
                )

        return recs

    def _precipitation_recommendations(
        self, current: WeatherConditions, hourly: list[HourlyForecast] | None
    ) -> list[SmartHomeRecommendation]:
        """Precipitation-based recommendations."""
        recs = []
        now = datetime.now()

        # Check for rain in next few hours
        if hourly:
            for i, h in enumerate(hourly[:3]):
                if h.conditions.precipitation_prob and h.conditions.precipitation_prob > 70:
                    recs.append(
                        SmartHomeRecommendation(
                            trigger_time=h.timestamp - timedelta(minutes=30),
                            action="Close windows and retract awnings",
                            reason=f"Rain likely in {i+1} hour(s) ({h.conditions.precipitation_prob}% chance)",
                            priority="high" if i == 0 else "medium",
                            automation_example="""
automation:
  - alias: "Close windows before rain"
    trigger:
      - platform: numeric_state
        entity_id: sensor.rain_probability
        above: 70
    action:
      - service: cover.close_cover
        entity_id: cover.window_1
      - service: notify.mobile_app
        data:
          message: "Rain coming - windows closing"
""",
                        )
                    )
                    break  # Only add one rain recommendation

        return recs

    def _wind_recommendations(self, current: WeatherConditions) -> list[SmartHomeRecommendation]:
        """Wind-based recommendations."""
        recs = []
        now = datetime.now()

        # High winds
        if current.wind_speed > 20:
            recs.append(
                SmartHomeRecommendation(
                    trigger_time=now,
                    action="Secure outdoor furniture and close awnings",
                    reason=f"High winds at {current.wind_speed:.1f} mph",
                    priority="high" if current.wind_speed > 30 else "medium",
                    automation_example="""
automation:
  - alias: "High wind warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.wind_speed
        above: 20
    action:
      - service: cover.close_cover
        entity_id: cover.awning
      - service: notify.mobile_app
        data:
          message: "High winds - secure outdoor items"
""",
                )
            )

        return recs

    def _sun_recommendations(self, current: WeatherConditions) -> list[SmartHomeRecommendation]:
        """Sun/UV-based recommendations."""
        recs = []
        now = datetime.now()

        # Clear day - good for solar
        if current.cloud_cover < 30 and 6 <= now.hour < 18:
            recs.append(
                SmartHomeRecommendation(
                    trigger_time=now,
                    action="Optimize for solar energy generation",
                    reason=f"Clear skies with {current.cloud_cover}% cloud cover",
                    priority="low",
                    automation_example="""
automation:
  - alias: "Solar optimization"
    trigger:
      - platform: numeric_state
        entity_id: sensor.cloud_cover
        below: 30
    condition:
      - condition: time
        after: '06:00:00'
        before: '18:00:00'
    action:
      - service: switch.turn_on
        entity_id: switch.solar_battery_charging
""",
                )
            )

        # High UV
        if current.uv_index and current.uv_index > 7:
            recs.append(
                SmartHomeRecommendation(
                    trigger_time=now,
                    action="Close blinds to reduce UV exposure",
                    reason=f"High UV index: {current.uv_index}",
                    priority="medium",
                    automation_example=None,
                )
            )

        return recs

    def _anomaly_recommendations(self, anomalies: list[Anomaly]) -> list[SmartHomeRecommendation]:
        """Recommendations based on detected anomalies."""
        recs = []
        now = datetime.now()

        # High severity anomalies
        critical = [a for a in anomalies if a.severity in ["high", "critical"]]

        if critical:
            recs.append(
                SmartHomeRecommendation(
                    trigger_time=now,
                    action="Monitor unusual weather conditions",
                    reason=f"Unusual weather detected: {critical[0].description}",
                    priority="high",
                    automation_example=None,
                )
            )

        return recs
