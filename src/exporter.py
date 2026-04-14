from datetime import datetime
from typing import Any

import pandas as pd

FIELD_LABELS: dict[str, str] = {
    "tc": "Temperature (°C)",
    "rh": "Humidity (%)",
    "rain": "Rainfall (mm)",
    "ws10m": "Wind Speed (m/s)",
    "wd10m": "Wind Direction (°)",
    "cond": "Condition",
    "tc_max": "Max Temperature (°C)",
    "tc_min": "Min Temperature (°C)",
    "swdown": "Solar Radiation (W/m²)",
}


def default_output_path() -> str:
    return f"weather_{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.csv"


def export(data: dict[str, Any], fields: list[str], output: str) -> None:
    columns = ["Latitude", "Longitude", "Time"] + [FIELD_LABELS.get(f, f) for f in fields]

    rows = [
        [
            item["location"]["lat"],
            item["location"]["lon"],
            forecast["time"],
            *[forecast["data"].get(f) for f in fields],
        ]
        for item in data["WeatherForecasts"]
        for forecast in item["forecasts"]
    ]

    df = pd.DataFrame(rows, columns=columns)  # type: ignore[arg-type]
    df.to_csv(output, index=False)
