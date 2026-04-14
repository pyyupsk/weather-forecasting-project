import logging
import time
from typing import Any

import requests

BASE_URL = "https://data.tmd.go.th/nwpapi/v1/forecast/location"

logger = logging.getLogger(__name__)


def _build_params(
    fields: str,
    date: str,
    duration: int,
    forecast: str,
    hour: int | None,
    province: str | None,
    amphoe: str | None,
    lat: float | None,
    lon: float | None,
) -> tuple[str, dict[str, Any]]:
    if lat is not None and lon is not None:
        endpoint = "at"
        params: dict[str, Any] = {"lat": lat, "lon": lon}
    else:
        endpoint = "place"
        params = {}
        if province:
            params["province"] = province
        if amphoe:
            params["amphoe"] = amphoe

    params["fields"] = fields
    params["date"] = date
    params["duration"] = duration
    if forecast == "hourly" and hour is not None:
        params["hour"] = hour

    return endpoint, params


def _handle_422(
    url: str,
    headers: dict[str, str],
    params: dict[str, Any],
    forecast: str,
    text: str,
) -> tuple[Exception, None] | tuple[None, dict[str, Any]]:
    try:
        corrected = text.split("The starttime must be a date after or equal to ")[1].split(".")[0]
        params["date"] = corrected.split("T")[0]
        if forecast == "hourly" and "T" in corrected:
            params["hour"] = int(corrected.split("T")[1].split(":")[0])
        logger.warning("422: corrected starttime to %s, retrying once", corrected)
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return None, response.json()
        return Exception(f"HTTP {response.status_code}: {response.text}"), None
    except (IndexError, ValueError) as e:
        return Exception(f"422 parse error: {e}"), None


def fetch(
    token: str,
    forecast: str,
    fields: str,
    date: str,
    duration: int,
    hour: int | None = None,
    province: str | None = None,
    amphoe: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> tuple[Exception, None] | tuple[None, dict[str, Any]]:
    endpoint, params = _build_params(fields, date, duration, forecast, hour, province, amphoe, lat, lon)
    url = f"{BASE_URL}/{forecast}/{endpoint}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}",
    }

    delays = [1, 2, 4]
    last_error: Exception = Exception("Unknown error")

    for attempt, delay in enumerate(delays, start=1):
        try:
            logger.debug("GET %s params=%s", url, params)
            response = requests.get(url, headers=headers, params=params)
            logger.debug("Response: %d", response.status_code)

            if response.status_code == 200:
                return None, response.json()

            if response.status_code == 422:
                return _handle_422(url, headers, params, forecast, response.text)

            if response.status_code >= 500:
                last_error = Exception(f"HTTP {response.status_code}: {response.reason}")
                if attempt < len(delays):
                    logger.warning("Retry %d/3: %d %s", attempt, response.status_code, response.reason)
                    time.sleep(delay)
                    continue
                return last_error, None

            return Exception(f"HTTP {response.status_code}: {response.text}"), None

        except requests.RequestException as e:
            last_error = Exception(str(e))
            if attempt < len(delays):
                logger.warning("Retry %d/3: %s", attempt, e)
                time.sleep(delay)
                continue
            return last_error, None

    return last_error, None
