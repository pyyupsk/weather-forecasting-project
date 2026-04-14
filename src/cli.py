import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import click

from client import fetch
from config import get_token
from exporter import default_output_path, export

logging.basicConfig(format="%(levelname)-8s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TZ_BKK = timezone(timedelta(hours=7))


def _current_hour_bkk() -> int:
    return datetime.now(TZ_BKK).hour


def _load_locations_file(path: Path) -> list[dict[str, Any]]:
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise click.BadParameter(f"{path} must contain a JSON array")
    return data  # type: ignore[return-value]


@click.command()
@click.option(
    "--location", nargs=2, multiple=True, metavar="PROVINCE AMPHOE", help="Province + amphoe pair. Repeatable."
)
@click.option(
    "--locations",
    type=click.Path(exists=False, path_type=Path),
    default=None,
    help="JSON file with location list",
)
@click.option("--lat", type=float, default=None, help="Latitude (requires --lon)")
@click.option("--lon", type=float, default=None, help="Longitude (requires --lat)")
@click.option("--forecast", default="hourly", help="hourly or daily")
@click.option("--fields", default=None, help="Comma-separated fields")
@click.option("--date", default=None, help="Date YYYY-MM-DD")
@click.option("--hour", type=int, default=None, help="Hour 0-23 (hourly only)")
@click.option("--duration", type=int, default=24, help="Hours (max 48) or days (max 126)")
@click.option("--output", default=None, help="Output CSV path")
@click.option("--verbose", is_flag=True, default=False, help="Enable DEBUG logging")
def _main_cmd(
    location: tuple[tuple[str, str], ...],
    locations: Path | None,
    lat: float | None,
    lon: float | None,
    forecast: str,
    fields: str | None,
    date: str | None,
    hour: int | None,
    duration: int,
    output: str | None,
    verbose: bool,
) -> None:
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if forecast not in ("hourly", "daily"):
        click.echo("Error: --forecast must be 'hourly' or 'daily'. Use 'hourly' or 'daily'.", err=True)
        raise SystemExit(1)

    # Validate --lat/--lon must appear together
    if (lat is None) != (lon is None):
        click.echo("Error: --lat and --lon must be provided together.", err=True)
        raise SystemExit(1)

    # Build full location list
    all_locations: list[dict[str, Any]] = []
    for province, amphoe in location:
        all_locations.append({"province": province, "amphoe": amphoe})
    if locations:
        all_locations.extend(_load_locations_file(locations))
    if lat is not None and lon is not None:
        all_locations.append({"lat": lat, "lon": lon})

    if not all_locations:
        click.echo("Error: provide at least one location via --location, --locations, or --lat/--lon.", err=True)
        raise SystemExit(1)

    token = get_token()
    resolved_fields = fields or ("tc,rh" if forecast == "hourly" else "tc_min,tc_max,rh")
    resolved_date = date or datetime.now(TZ_BKK).strftime("%Y-%m-%d")
    resolved_hour = hour if hour is not None else (_current_hour_bkk() if forecast == "hourly" else None)
    resolved_output = output or default_output_path()

    succeeded = 0
    failed = 0
    all_rows: list[dict[str, Any]] = []

    for loc in all_locations:
        label = (
            f"{loc.get('province', '')} / {loc.get('amphoe', '')}"
            if "province" in loc
            else f"{loc['lat']},{loc['lon']}"
        )
        logger.info("Fetching %s forecast: %s", forecast, label)

        err, data = fetch(
            token=token,
            forecast=forecast,
            fields=resolved_fields,
            date=resolved_date,
            duration=duration,
            hour=resolved_hour,
            province=loc.get("province"),
            amphoe=loc.get("amphoe"),
            lat=loc.get("lat"),
            lon=loc.get("lon"),
        )

        if err:
            logger.error("Failed: %s — %s", label, err)
            failed += 1
        else:
            all_rows.extend(data.get("WeatherForecasts", []))  # type: ignore[union-attr]
            succeeded += 1

    if all_rows:
        export({"WeatherForecasts": all_rows}, resolved_fields.split(","), resolved_output)
        logger.info("Saved %d location(s) → %s", succeeded, resolved_output)

    click.echo(f"\nCompleted: {succeeded} succeeded, {failed} failed")


app = _main_cmd
