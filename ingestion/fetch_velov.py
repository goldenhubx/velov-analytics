"""Récupère un snapshot du flux GBFS Vélo'v Lyon et l'écrit en parquet."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.cyclocity.fr/contracts/lyon/gbfs"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def fetch_json(endpoint: str) -> dict:
    url = f"{BASE_URL}/{endpoint}.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def snapshot_station_status(ingested_at: datetime) -> None:
    payload = fetch_json("station_status")
    stations = payload["data"]["stations"]
    df = pd.json_normalize(stations)
    df["ingested_at"] = ingested_at

    out_dir = RAW_DIR / "station_status"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = ingested_at.strftime("%Y%m%dT%H%M%SZ") + ".parquet"
    df.to_parquet(out_dir / filename, index=False)


def snapshot_station_information(ingested_at: datetime) -> None:
    payload = fetch_json("station_information")
    stations = payload["data"]["stations"]
    df = pd.json_normalize(stations)
    df["ingested_at"] = ingested_at

    out_dir = RAW_DIR / "station_information"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = ingested_at.strftime("%Y%m%dT%H%M%SZ") + ".parquet"
    df.to_parquet(out_dir / filename, index=False)


def main() -> None:
    ingested_at = datetime.now(timezone.utc)
    snapshot_station_status(ingested_at)
    snapshot_station_information(ingested_at)
    print(f"Snapshot écrit pour {ingested_at.isoformat()}")


if __name__ == "__main__":
    main()