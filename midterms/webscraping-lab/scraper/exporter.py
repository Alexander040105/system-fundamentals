from __future__ import annotations

from typing import Iterable

import pandas as pd


def export_to_csv(records: Iterable[dict[str, str]], output_path: str) -> None:
    data = list(records)
    if not data:
        raise ValueError("No records to export.")

    for record in data:
        if "Date" not in record or "Data_Usage" not in record:
            raise ValueError("Records must include Date and Data_Usage keys.")

    df = pd.DataFrame(data)
    df = df[["Date", "Data_Usage"]]
    df.to_csv(output_path, index=False)
