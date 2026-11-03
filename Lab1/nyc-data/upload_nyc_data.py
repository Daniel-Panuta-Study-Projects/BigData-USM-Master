import os
import time

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Core config
API_URL = "https://data.cityofnewyork.us/api/odata/v4/ye3c-m4ga?$format=json"
SAVE_FORMAT = "parquet"
CSV_FILE = "nyc_civil_list.csv"
PARQUET_FILE = "nyc_civil_list.parquet"


def create_robust_session():
    """Configures a request session with spoofed browser headers and smart retries."""
    session = requests.Session()

    # 1. Pretend to be a real web browser to avoid Socrata's automated connection blocks
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
    )

    # 2. Automatically retry network hiccups with exponential backoff delays (e.g., wait 2s, 4s, 8s...)
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def download_large_odata(initial_url, file_format):
    current_url = initial_url
    batch_count = 0
    total_records = 0
    is_first_chunk = True

    output_path = PARQUET_FILE if file_format == "parquet" else CSV_FILE
    print(f"Starting robust data export to: '{output_path}'")

    if os.path.exists(output_path):
        os.remove(output_path)

    pq_writer = None
    session = create_robust_session()

    # Outermost error loop to handle pagination recovery
    while current_url:
        try:
            print(f"Fetching chunk {batch_count + 1}...")

            # 3. Explicit timeouts: 15s to establish connection, 90s to read data chunk stream
            response = session.get(current_url, timeout=(15, 90))
            response.raise_for_status()
            data = response.json()

            records = data.get("value", [])
            if not records:
                print("Extraction complete. No more records found.")
                break

            df = pd.DataFrame(records).astype(str)

            if file_format == "parquet":
                table = pa.Table.from_pandas(df, preserve_index=False)
                if is_first_chunk:
                    pq_writer = pq.ParquetWriter(output_path, table.schema)
                pq_writer.write_table(table)
            else:
                if is_first_chunk:
                    df.to_csv(output_path, index=False, mode="w")
                else:
                    df.to_csv(output_path, index=False, mode="a", header=False)

            is_first_chunk = False
            batch_count += 1
            total_records += len(records)

            print(
                f"-> Saved Batch {batch_count:04d} | Total Rows: {total_records:,}"
            )

            # Move to next Socrata page pointer token
            current_url = data.get("@odata.nextLink")

            # Politeness delay to prevent rate-limiting triggers
            time.sleep(0.5)

        except (requests.exceptions.RequestException, Exception) as e:
            print(f"\n[Warning] Network/API hitch encountered: {e}")
            print("Cooling down for 15 seconds before trying again...")
            time.sleep(15)
            # The loop continues using the last-saved 'current_url' state
            continue

    if pq_writer:
        pq_writer.close()

    print(
        f"\n[Success] Pipeline finished. Local database created with {total_records:,} entries."
    )


if __name__ == "__main__":
    download_large_odata(API_URL, SAVE_FORMAT)
