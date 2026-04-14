from typing import Any
from unittest.mock import MagicMock

from client import fetch

BASE_KWARGS: dict[str, Any] = {
    "token": "test-token",
    "forecast": "hourly",
    "fields": "tc,rh",
    "date": "2026-04-13",
    "duration": 24,
    "province": "นครปฐม",
    "amphoe": "สามพราน",
}

SAMPLE_RESPONSE: dict = {"WeatherForecasts": [{"location": {"lat": 13.8, "lon": 100.1}, "forecasts": []}]}


def _mock_response(status: int, json_data: dict | None = None, text: str = "") -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = json_data or {}
    mock.text = text
    mock.reason = "OK" if status == 200 else "Error"
    return mock


def test_fetch_returns_data_on_200(mocker: Any) -> None:
    mocker.patch("client.requests.get", return_value=_mock_response(200, SAMPLE_RESPONSE))
    err, data = fetch(**BASE_KWARGS)
    assert err is None
    assert data == SAMPLE_RESPONSE


def test_fetch_returns_error_on_400(mocker: Any) -> None:
    mocker.patch("client.requests.get", return_value=_mock_response(400, text="Bad Request"))
    err, data = fetch(**BASE_KWARGS)
    assert err is not None
    assert data is None
    assert "400" in str(err)


def test_fetch_retries_on_5xx_and_succeeds(mocker: Any) -> None:
    mock_500 = _mock_response(503)
    mock_200 = _mock_response(200, SAMPLE_RESPONSE)
    mocker.patch("client.requests.get", side_effect=[mock_500, mock_500, mock_200])
    mocker.patch("client.time.sleep")

    err, data = fetch(**BASE_KWARGS)
    assert err is None
    assert data == SAMPLE_RESPONSE


def test_fetch_returns_error_after_3_failed_retries(mocker: Any) -> None:
    mocker.patch("client.requests.get", return_value=_mock_response(503))
    mocker.patch("client.time.sleep")

    err, data = fetch(**BASE_KWARGS)
    assert err is not None
    assert data is None


def test_fetch_retries_on_network_error_and_succeeds(mocker: Any) -> None:
    import requests as req

    mocker.patch("client.requests.get", side_effect=[req.ConnectionError("down"), _mock_response(200, SAMPLE_RESPONSE)])
    mocker.patch("client.time.sleep")

    err, data = fetch(**BASE_KWARGS)
    assert err is None
    assert data == SAMPLE_RESPONSE


def test_fetch_returns_error_on_repeated_network_failures(mocker: Any) -> None:
    import requests as req

    mocker.patch("client.requests.get", side_effect=req.ConnectionError("down"))
    mocker.patch("client.time.sleep")

    err, data = fetch(**BASE_KWARGS)
    assert err is not None
    assert data is None


def test_fetch_422_corrects_starttime_and_retries(mocker: Any) -> None:
    error_text = "The starttime must be a date after or equal to 2026-04-14T00:00:00."
    mock_422 = _mock_response(422, text=error_text)
    mock_200 = _mock_response(200, SAMPLE_RESPONSE)
    get_mock = mocker.patch("client.requests.get", side_effect=[mock_422, mock_200])

    err, data = fetch(**BASE_KWARGS)
    assert err is None
    assert data == SAMPLE_RESPONSE
    # second call should have corrected date
    second_call_params = get_mock.call_args_list[1][1]["params"]
    assert second_call_params["date"] == "2026-04-14"


def test_fetch_uses_at_endpoint_for_coordinates(mocker: Any) -> None:
    get_mock = mocker.patch("client.requests.get", return_value=_mock_response(200, SAMPLE_RESPONSE))
    fetch(token="tok", forecast="hourly", fields="tc,rh", date="2026-04-13", duration=24, lat=13.8, lon=100.1)
    called_url = get_mock.call_args[0][0]
    assert called_url.endswith("/hourly/at")


def test_fetch_uses_place_endpoint_for_province(mocker: Any) -> None:
    get_mock = mocker.patch("client.requests.get", return_value=_mock_response(200, SAMPLE_RESPONSE))
    fetch(**BASE_KWARGS)
    called_url = get_mock.call_args[0][0]
    assert called_url.endswith("/hourly/place")
