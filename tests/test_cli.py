import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from cli import app

runner = CliRunner()

SAMPLE_DATA: dict = {"WeatherForecasts": [{"location": {"lat": 13.8, "lon": 100.1}, "forecasts": [{"time": "2026-04-13T08:00:00+07:00", "data": {"tc": 28.5, "rh": 75}}]}]}


def _patch_fetch_success(mocker: Any) -> Any:
    return mocker.patch("cli.fetch", return_value=(None, SAMPLE_DATA))


def _patch_export(mocker: Any) -> Any:
    return mocker.patch("cli.export")


def _patch_token(mocker: Any) -> Any:
    return mocker.patch("cli.get_token", return_value="test-token")


def test_single_location_calls_fetch(mocker: Any) -> None:
    _patch_token(mocker)
    fetch_mock = _patch_fetch_success(mocker)
    _patch_export(mocker)

    result = runner.invoke(app, ["--location", "นครปฐม", "สามพราน"])

    assert result.exit_code == 0
    fetch_mock.assert_called_once()
    call_kwargs = fetch_mock.call_args[1]
    assert call_kwargs["province"] == "นครปฐม"
    assert call_kwargs["amphoe"] == "สามพราน"


def test_multiple_locations_calls_fetch_for_each(mocker: Any) -> None:
    _patch_token(mocker)
    fetch_mock = _patch_fetch_success(mocker)
    _patch_export(mocker)

    result = runner.invoke(app, ["--location", "นครปฐม", "สามพราน", "--location", "กรุงเทพมหานคร", "พระนคร"])

    assert result.exit_code == 0
    assert fetch_mock.call_count == 2


def test_locations_file_is_merged_with_location_flag(mocker: Any, tmp_path: Path) -> None:
    _patch_token(mocker)
    fetch_mock = _patch_fetch_success(mocker)
    _patch_export(mocker)

    locations_file = tmp_path / "locs.json"
    locations_file.write_text(json.dumps([{"province": "เชียงใหม่", "amphoe": "เมือง"}]))

    result = runner.invoke(app, ["--location", "นครปฐม", "สามพราน", "--locations", str(locations_file)])

    assert result.exit_code == 0
    assert fetch_mock.call_count == 2


def test_coordinates_flag_calls_fetch_with_lat_lon(mocker: Any) -> None:
    _patch_token(mocker)
    fetch_mock = _patch_fetch_success(mocker)
    _patch_export(mocker)

    result = runner.invoke(app, ["--lat", "13.8", "--lon", "100.1"])

    assert result.exit_code == 0
    call_kwargs = fetch_mock.call_args[1]
    assert call_kwargs["lat"] == 13.8
    assert call_kwargs["lon"] == 100.1


def test_no_location_exits_with_error(mocker: Any) -> None:
    _patch_token(mocker)

    result = runner.invoke(app, [])

    assert result.exit_code != 0
    assert "location" in result.output.lower() or result.exit_code == 1


def test_only_lat_without_lon_exits_with_error(mocker: Any) -> None:
    _patch_token(mocker)

    result = runner.invoke(app, ["--lat", "13.8"])

    assert result.exit_code != 0


def test_failed_location_does_not_abort_run(mocker: Any) -> None:
    _patch_token(mocker)
    mocker.patch("cli.fetch", side_effect=[(Exception("API error"), None), (None, SAMPLE_DATA)])
    _patch_export(mocker)

    result = runner.invoke(app, ["--location", "bad", "place", "--location", "นครปฐม", "สามพราน"])

    assert result.exit_code == 0
    assert "1 succeeded" in result.output
    assert "1 failed" in result.output


def test_summary_reflects_counts(mocker: Any) -> None:
    _patch_token(mocker)
    _patch_fetch_success(mocker)
    _patch_export(mocker)

    result = runner.invoke(app, ["--location", "นครปฐม", "สามพราน", "--location", "กรุงเทพมหานคร", "พระนคร"])

    assert "2 succeeded" in result.output
    assert "0 failed" in result.output


def test_custom_output_path_passed_to_export(mocker: Any, tmp_path: Path) -> None:
    _patch_token(mocker)
    _patch_fetch_success(mocker)
    export_mock = _patch_export(mocker)

    output_path = str(tmp_path / "custom.csv")
    runner.invoke(app, ["--location", "นครปฐม", "สามพราน", "--output", output_path])

    export_mock.assert_called_once()
    assert export_mock.call_args[0][2] == output_path


def test_default_output_uses_timestamp(mocker: Any) -> None:
    _patch_token(mocker)
    _patch_fetch_success(mocker)
    export_mock = _patch_export(mocker)
    mocker.patch("cli.default_output_path", return_value="weather_2026-04-13T08-00-00.csv")

    runner.invoke(app, ["--location", "นครปฐม", "สามพราน"])

    assert export_mock.call_args[0][2] == "weather_2026-04-13T08-00-00.csv"


def test_invalid_forecast_type_exits_with_error(mocker: Any) -> None:
    _patch_token(mocker)

    result = runner.invoke(app, ["--location", "นครปฐม", "สามพราน", "--forecast", "weekly"])

    assert result.exit_code != 0
    assert "hourly" in result.output or "daily" in result.output


def test_default_hour_uses_current_bkk_hour(mocker: Any) -> None:
    _patch_token(mocker)
    fetch_mock = _patch_fetch_success(mocker)
    _patch_export(mocker)
    mocker.patch("cli._current_hour_bkk", return_value=9)

    runner.invoke(app, ["--location", "นครปฐม", "สามพราน"])

    call_kwargs = fetch_mock.call_args[1]
    assert call_kwargs["hour"] == 9


def test_default_date_uses_today_bkk(mocker: Any) -> None:
    _patch_token(mocker)
    fetch_mock = _patch_fetch_success(mocker)
    _patch_export(mocker)

    result = runner.invoke(app, ["--location", "นครปฐม", "สามพราน"])

    assert result.exit_code == 0
    call_kwargs = fetch_mock.call_args[1]
    # date should be a YYYY-MM-DD string, not None
    import re
    assert re.match(r"\d{4}-\d{2}-\d{2}", call_kwargs["date"])
