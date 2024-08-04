import argparse
import csv
import json
from datetime import datetime
from typing import List

import httpx
from pydantic.json import pydantic_encoder

from backend.api_models import AddDataSeriesResult, DataSeriesCreate


def add_data_series_values(values: List[DataSeriesCreate]):
    payload = json.dumps([value.model_dump() for value in values], default=pydantic_encoder)
    response = httpx.post(
        "http://localhost:8000/api/dataseries/",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    return AddDataSeriesResult(**response.json())


def ingest_data_series(csv_file):
    data_series_list = []
    reader = csv.DictReader(csv_file)
    for row in reader:
        date_time = datetime.strptime(row["Date"], "%d/%m/%Y")
        for key, value in row.items():
            if key != "Date" and value:
                data_series_list.append(DataSeriesCreate(date_time=date_time, key=key, value=value))
    result = add_data_series_values(data_series_list)
    print(f"Values added: {result.values_added}")


def main():
    parser = argparse.ArgumentParser(description="CLI for Data Series Ingestion")
    parser.add_argument(
        "csv_file",
        type=argparse.FileType("r"),
        help="Path to the CSV file holding data series.",
    )
    args = parser.parse_args()
    ingest_data_series(args.csv_file)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)
