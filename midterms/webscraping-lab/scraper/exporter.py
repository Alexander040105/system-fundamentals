from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .usage_page import UsageRecord


def export_to_csv(records: Iterable[UsageRecord], output_csv: str) -> str:
    """Write usage records to CSV and return the file path."""

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow(["Date", "Data_Usage"])
        for record in records:
            writer.writerow([record.date, record.usage])

    return str(output_path)
