"""Weather data aggregation from multiple free sources."""

import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from app.models import DailyForecast, HourlyForecast, WeatherConditions

logger = logging.getLogger(__name__)

CLOUD_COVER_MAP = {"SKC": 0, "CLR": 0, "FEW": 20, "SCT": 40, "BKN": 70, "OVC": 100}


class WeatherAggregator:
    """Aggregate weather data from multiple free APIs."""

    def __init__(self, latitude: float, longitude: float, location_name: str):
        self.latitude = latitude
        self.longitude = longitude
        self.location_name = location_name
        self.client = httpx.AsyncClient(timeout=30.0)
        self.wttr_client = httpx.AsyncClient(timeout=60.0)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
        await self.wttr_client.aclose()

    async def get_current_conditions(self) -> tuple[WeatherConditions, list[str]]:
        """Get current weather from all sources and ensemble."""
        sources = []
        conditions_list = []

        # Try Open-Meteo
        try:
            om_data = await self._fetch_open_meteo()
            if om_data:
                conditions_list.append(om_data)
                sources.append("open-meteo")
        except Exception as e:
            logger.warning(f"Open-Meteo fetch failed: {e}")

        # Try wttr.in
        try:
            wttr_data = await self._fetch_wttr()
            if wttr_data:
                conditions_list.append(wttr_data)
                sources.append("wttr.in")
        except Exception as e:
            logger.warning(f"wttr.in fetch failed: {e}")

        # Try Weather.gov (US only)
        if self._is_us_location():
            try:
                nws_data = await self._fetch_nws()
                if nws_data:
                    conditions_list.append(nws_data)
                    sources.append("weather.gov")
            except Exception as e:
                logger.warning(f"Weather.gov fetch failed: {e}")

        if not conditions_list:
            raise ValueError("No weather sources available")

        # Ensemble average
        ensembled = self._ensemble_conditions(conditions_list)
        return ensembled, sources

    async def get_hourly_forecast(self, hours: int = 48) -> list[HourlyForecast]:
        """Get hourly forecast."""
        forecasts = []

        # Open-Meteo hourly
        try:
            om_hourly = await self._fetch_open_meteo_hourly(hours)
            forecasts.extend(om_hourly)
        except Exception as e:
            logger.warning(f"Open-Meteo hourly failed: {e}")

        # Weather.gov hourly (US only)
        if self._is_us_location():
            try:
                nws_hourly = await self._fetch_nws_hourly(hours)
                forecasts.extend(nws_hourly)
            except Exception as e:
                logger.warning(f"Weather.gov hourly failed: {e}")

        return forecasts

    async def get_daily_forecast(self, days: int = 7) -> list[DailyForecast]:
        """Get daily forecast."""
        forecasts = []

        # Open-Meteo daily
        try:
            om_daily = await self._fetch_open_meteo_daily(days)
            forecasts.extend(om_daily)
        except Exception as e:
            logger.warning(f"Open-Meteo daily failed: {e}")

        return forecasts

    def _is_us_location(self) -> bool:
        """Check if location is in US (rough approximation)."""
        return (
            24.0 <= self.latitude <= 50.0 and -125.0 <= self.longitude <= -66.0
        )

    async def _fetch_open_meteo(self) -> Optional[WeatherConditions]:
        """Fetch current conditions from Open-Meteo."""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,rain,pressure_msl,cloud_cover,wind_speed_10m,"
            "wind_direction_10m,weather_code",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
        }

        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        current = data["current"]
        return WeatherConditions(
            temperature=current["temperature_2m"],
            feels_like=current["apparent_temperature"],
            humidity=current["relative_humidity_2m"],
            pressure=current["pressure_msl"],
            wind_speed=current["wind_speed_10m"],
            wind_direction=current["wind_direction_10m"],
            cloud_cover=current["cloud_cover"],
            visibility=None,
            conditions=self._wmo_code_to_text(current["weather_code"]),
            precipitation_prob=None,
            precipitation_amount=current.get("precipitation", 0),
            uv_index=None,
        )

    async def _fetch_wttr(self) -> Optional[WeatherConditions]:
        """Fetch current conditions from wttr.in."""
        url = f"https://wttr.in/{self.latitude},{self.longitude}"
        params = {"format": "j1"}

        resp = await self.wttr_client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        current = data["current_condition"][0]
        return WeatherConditions(
            temperature=float(current["temp_F"]),
            feels_like=float(current["FeelsLikeF"]),
            humidity=int(current["humidity"]),
            pressure=float(current["pressure"]),
            wind_speed=float(current["windspeedMiles"]),
            wind_direction=int(current["winddirDegree"]),
            cloud_cover=int(current["cloudcover"]),
            visibility=float(current["visibilityMiles"]),
            conditions=current["weatherDesc"][0]["value"],
            precipitation_prob=int(current.get("precipMM", 0)),
            precipitation_amount=float(current.get("precipInches", 0)),
            uv_index=int(current["uvIndex"]),
        )

    async def _fetch_nws(self) -> Optional[WeatherConditions]:
        """Fetch current conditions from Weather.gov."""
        points_url = f"https://api.weather.gov/points/{self.latitude},{self.longitude}"
        resp = await self.client.get(
            points_url, headers={"User-Agent": "WeatherForecast/1.0"}
        )
        resp.raise_for_status()
        points_data = resp.json()

        stations_url = points_data["properties"]["observationStations"]
        resp = await self.client.get(
            stations_url, headers={"User-Agent": "WeatherForecast/1.0"}
        )
        resp.raise_for_status()
        stations = resp.json()
        station_id = stations["features"][0]["properties"]["stationIdentifier"]

        obs_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
        resp = await self.client.get(
            obs_url, headers={"User-Agent": "WeatherForecast/1.0"}
        )
        resp.raise_for_status()
        obs = resp.json()["properties"]

        temp_c = obs["temperature"]["value"]
        temp_f = (temp_c * 9 / 5) + 32 if temp_c else None

        cloud_layers = obs.get("cloudLayers", [])
        cloud_amount = cloud_layers[0].get("amount", "CLR") if cloud_layers else "CLR"
        cloud_cover = CLOUD_COVER_MAP.get(cloud_amount, 0)

        return WeatherConditions(
            temperature=temp_f or 0,
            feels_like=None,
            humidity=int(obs["relativeHumidity"]["value"] or 0),
            pressure=obs["barometricPressure"]["value"] or 0,
            wind_speed=obs["windSpeed"]["value"] or 0,
            wind_direction=obs["windDirection"]["value"],
            cloud_cover=cloud_cover,
            visibility=obs["visibility"]["value"] or 0,
            conditions=obs["textDescription"] or "Unknown",
            precipitation_prob=None,
            precipitation_amount=None,
            uv_index=None,
        )

    async def _fetch_open_meteo_hourly(self, hours: int) -> list[HourlyForecast]:
        """Fetch hourly forecast from Open-Meteo."""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,"
            "precipitation,pressure_msl,cloud_cover,wind_speed_10m,"
            "wind_direction_10m,weather_code",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "forecast_days": min(hours // 24 + 1, 16),
        }

        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        hourly = data["hourly"]
        forecasts = []

        for i in range(min(hours, len(hourly["time"]))):
            conditions = WeatherConditions(
                temperature=hourly["temperature_2m"][i],
                feels_like=None,
                humidity=hourly["relative_humidity_2m"][i],
                pressure=hourly["pressure_msl"][i],
                wind_speed=hourly["wind_speed_10m"][i],
                wind_direction=hourly["wind_direction_10m"][i],
                cloud_cover=hourly["cloud_cover"][i],
                visibility=None,
                conditions=self._wmo_code_to_text(hourly["weather_code"][i]),
                precipitation_prob=hourly["precipitation_probability"][i],
                precipitation_amount=hourly["precipitation"][i],
                uv_index=None,
            )

            forecasts.append(
                HourlyForecast(
                    timestamp=datetime.fromisoformat(hourly["time"][i]),
                    conditions=conditions,
                    source="open-meteo",
                )
            )

        return forecasts

    async def _fetch_nws_hourly(self, hours: int) -> list[HourlyForecast]:
        """Fetch hourly forecast from Weather.gov."""
        points_url = f"https://api.weather.gov/points/{self.latitude},{self.longitude}"
        resp = await self.client.get(
            points_url, headers={"User-Agent": "WeatherForecast/1.0"}
        )
        resp.raise_for_status()
        points_data = resp.json()

        hourly_url = points_data["properties"]["forecastHourly"]
        resp = await self.client.get(
            hourly_url, headers={"User-Agent": "WeatherForecast/1.0"}
        )
        resp.raise_for_status()
        forecast_data = resp.json()

        forecasts = []
        for period in forecast_data["properties"]["periods"][:hours]:
            conditions = WeatherConditions(
                temperature=float(period["temperature"]),
                feels_like=None,
                humidity=period.get("relativeHumidity", {}).get("value", 0),
                pressure=0,
                wind_speed=float(period["windSpeed"].split()[0]),
                wind_direction=self._direction_to_degrees(period["windDirection"]),
                cloud_cover=0,
                visibility=None,
                conditions=period["shortForecast"],
                precipitation_prob=period.get("probabilityOfPrecipitation", {}).get("value", 0),
                precipitation_amount=None,
                uv_index=None,
            )

            forecasts.append(
                HourlyForecast(
                    timestamp=datetime.fromisoformat(
                        period["startTime"].replace("Z", "+00:00")
                    ),
                    conditions=conditions,
                    source="weather.gov",
                )
            )

        return forecasts

    async def _fetch_open_meteo_daily(self, days: int) -> list[DailyForecast]:
        """Fetch daily forecast from Open-Meteo."""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
            "temperature_unit": "fahrenheit",
            "forecast_days": min(days, 16),
        }

        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        daily = data["daily"]
        forecasts = []

        for i in range(len(daily["time"])):
            forecasts.append(
                DailyForecast(
                    date=daily["time"][i],
                    temp_high=daily["temperature_2m_max"][i],
                    temp_low=daily["temperature_2m_min"][i],
                    conditions=self._wmo_code_to_text(daily["weather_code"][i]),
                    precipitation_prob=daily["precipitation_probability_max"][i] or 0,
                    summary=self._wmo_code_to_text(daily["weather_code"][i]),
                    source="open-meteo",
                )
            )

        return forecasts

    def _ensemble_conditions(self, conditions_list: list[WeatherConditions]) -> WeatherConditions:
        """Average multiple weather conditions."""
        n = len(conditions_list)
        return WeatherConditions(
            temperature=sum(c.temperature for c in conditions_list) / n,
            feels_like=sum((c.feels_like or c.temperature) for c in conditions_list) / n,
            humidity=int(sum(c.humidity for c in conditions_list) / n),
            pressure=sum(c.pressure for c in conditions_list) / n,
            wind_speed=sum(c.wind_speed for c in conditions_list) / n,
            wind_direction=int(sum((c.wind_direction or 0) for c in conditions_list) / n),
            cloud_cover=int(sum(c.cloud_cover for c in conditions_list) / n),
            visibility=sum((c.visibility or 0) for c in conditions_list) / n or None,
            conditions=conditions_list[0].conditions,
            precipitation_prob=int(sum((c.precipitation_prob or 0) for c in conditions_list) / n) or None,
            precipitation_amount=sum((c.precipitation_amount or 0) for c in conditions_list) / n or None,
            uv_index=int(sum((c.uv_index or 0) for c in conditions_list) / n) or None,
        )

    @staticmethod
    def _wmo_code_to_text(code: int) -> str:
        """Convert WMO weather code to text."""
        codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle",
            53: "Moderate drizzle", 55: "Dense drizzle", 61: "Slight rain",
            63: "Moderate rain", 65: "Heavy rain", 71: "Slight snow",
            73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
            80: "Slight rain showers", 81: "Moderate rain showers",
            82: "Violent rain showers", 85: "Slight snow showers",
            86: "Heavy snow showers", 95: "Thunderstorm",
            96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
        }
        return codes.get(code, "Unknown")

    @staticmethod
    def _direction_to_degrees(direction: str) -> int:
        """Convert wind direction text to degrees."""
        directions = {
            "N": 0, "NNE": 22, "NE": 45, "ENE": 67, "E": 90, "ESE": 112,
            "SE": 135, "SSE": 157, "S": 180, "SSW": 202, "SW": 225,
            "WSW": 247, "W": 270, "WNW": 292, "NW": 315, "NNW": 337,
        }
        return directions.get(direction, 0)
