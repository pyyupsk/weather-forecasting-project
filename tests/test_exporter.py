import csv
from datetime import datetime
from pathlib import Path

from exporter import default_output_path, export

SAMPLE_DATA: dict = {
    "WeatherForecasts": [
        {
            "location": {"lat": 13.8, "lon": 100.1},
            "forecasts": [
                {"time": "2026-04-13T08:00:00+07:00", "data": {"tc": 28.5, "rh": 75}},
                {"time": "2026-04-13T09:00:00+07:00", "data": {"tc": 29.0, "rh": 72}},
            ],
        }
    ]
}


def test_export_creates_csv_with_correct_columns(tmp_path: Path) -> None:
    output = str(tmp_path / "out.csv")
    export(SAMPLE_DATA, ["tc", "rh"], output)

    with open(output) as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
    assert columns == ["Latitude", "Longitude", "Time", "Temperature (°C)", "Humidity (%)"]


def test_export_creates_csv_with_correct_rows(tmp_path: Path) -> None:
    output = str(tmp_path / "out.csv")
    export(SAMPLE_DATA, ["tc", "rh"], output)

    with open(output) as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["Temperature (°C)"] == "28.5"
    assert rows[0]["Humidity (%)"] == "75"
    assert rows[1]["Temperature (°C)"] == "29.0"


def test_export_unknown_field_uses_field_name_as_column(tmp_path: Path) -> None:
    data = {
        "WeatherForecasts": [
            {
                "location": {"lat": 13.8, "lon": 100.1},
                "forecasts": [
                    {"time": "2026-04-13T08:00:00+07:00", "data": {"pressure": 1013}},
                ],
            }
        ]
    }
    output = str(tmp_path / "out.csv")
    export(data, ["pressure"], output)

    with open(output) as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
    assert "pressure" in (columns or [])


def test_default_output_path_format() -> None:
    before = datetime.now()
    path = default_output_path()
    after = datetime.now()

    assert path.startswith("weather_")
    assert path.endswith(".csv")
    # parse the timestamp from the filename
    ts_str = path[len("weather_"):-len(".csv")]
    ts = datetime.strptime(ts_str, "%Y-%m-%dT%H-%M-%S")
    assert before.replace(microsecond=0) <= ts <= after.replace(microsecond=0)
