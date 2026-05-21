from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, List, Optional

import requests
from selenium.webdriver.remote.webdriver import WebDriver

from .usage_page import UsageRecord


def _first_value(item: dict, keys: Iterable[str]) -> Optional[Any]:
    for key in keys:
        if key in item and item[key] is not None:
            return item[key]
    return None


def _normalize_usage(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return f"{value}"
    return str(value).strip()


def _extract_usage_records(payload: Any) -> List[UsageRecord]:
    candidates: List[dict] = []

    if isinstance(payload, list):
        candidates = [item for item in payload if isinstance(item, dict)]
    elif isinstance(payload, dict):
        for key in ("data", "records", "days", "daily", "usage", "items"):
            if isinstance(payload.get(key), list):
                candidates = [item for item in payload[key] if isinstance(item, dict)]
                break

    records: List[UsageRecord] = []
    for item in candidates:
        date_value = _first_value(
            item,
            ["date", "day", "startDate", "periodStart", "timestamp", "usageDate"],
        )
        usage_value = _first_value(
            item,
            ["usage", "dataUsage", "total", "totalUsage", "gb", "gigaBytes"],
        )

        if date_value is None and usage_value is None:
            continue

        records.append(UsageRecord(str(date_value), _normalize_usage(usage_value)))

    return records


def fetch_usage_api(driver: WebDriver, api_url: str, output_dir: str = "output") -> tuple[List[UsageRecord], str]:
    """Fetch usage data from the authenticated API using Selenium cookies."""

    session = requests.Session()
    user_agent = driver.execute_script("return navigator.userAgent")

    for cookie in driver.get_cookies():
        session.cookies.set(
            cookie.get("name"),
            cookie.get("value"),
            domain=cookie.get("domain"),
            path=cookie.get("path", "/"),
        )

    response = session.get(api_url, headers={"User-Agent": user_agent}, timeout=30)
    response.raise_for_status()
    payload = response.json()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "usage_api.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return _extract_usage_records(payload), str(json_path)
