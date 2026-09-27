"""Récupère un snapshot du flux GBFS Vélo'v Lyon et l'insère dans MotherDuck."""

import os
from datetime import datetime, timezone

import duckdb
import pandas as pd
import requests

BASE_URL = "https://api.cyclocity.fr/contracts/lyon/gbfs"
DATABASE = "velov_analytics"


def fetch_json(endpoint: str) -> dict:
    response = requests.get(f"{BASE_URL}/{endpoint}.json", timeout=10)
    response.raise_for_status()
    return response.json()


def get_connection() -> duckdb.DuckDBPyConnection:
    token = os.environ["MOTHERDUCK_TOKEN"]
    con = duckdb.connect(f"md:?motherduck_token={token}")
    con.sql(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
    con.sql(f"USE {DATABASE}")
    return con


def append_snapshot(
    con: duckdb.DuckDBPyConnection, table_name: str, df: pd.DataFrame
) -> None:
    con.sql(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df LIMIT 0")
    con.sql(f"INSERT INTO {table_name} SELECT * FROM df")


def main() -> None:
    ingested_at = datetime.now(timezone.utc)
    con = get_connection()

    status_payload = fetch_json("station_status")
    status_df = pd.json_normalize(status_payload["data"]["stations"])
    status_df["ingested_at"] = ingested_at
    append_snapshot(con, "raw_station_status", status_df)

    info_payload = fetch_json("station_information")
    info_df = pd.json_normalize(info_payload["data"]["stations"])
    info_df["ingested_at"] = ingested_at
    append_snapshot(con, "raw_station_information", info_df)

    con.close()
    print(f"Snapshot inséré pour {ingested_at.isoformat()}")


if __name__ == "__main__":
    main()
