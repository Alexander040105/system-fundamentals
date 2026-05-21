from __future__ import annotations

from bs4 import BeautifulSoup
import json
import re


def parse_usage_from_html(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")

    table_records = parse_usage_from_table(soup)
    if table_records:
        return table_records

    bar_records = parse_usage_from_bars(soup)
    if bar_records:
        return bar_records

    records: list[dict[str, str]] = []
    for script in soup.find_all("script"):
        script_text = (script.string or "").strip()
        if not script_text:
            continue

        for candidate in extract_json_candidates(script_text):
            data = safe_json_loads(candidate)
            if data is None:
                continue

            records.extend(find_usage_records(data))

    return dedupe_records(records)


def parse_usage_from_json(data: object) -> list[dict[str, str]]:
    records = find_usage_records(data)
    return dedupe_records(records)


def parse_usage_from_table(soup: BeautifulSoup) -> list[dict[str, str]]:
    for table in soup.find_all("table"):
        headers = [
            th.get_text(strip=True).lower()
            for th in table.find_all("th")
        ]

        if not headers:
            continue

        if "date" in headers and ("usage" in headers or "data usage" in headers):
            date_index = headers.index("date")
            usage_index = headers.index("usage") if "usage" in headers else headers.index("data usage")

            records = []
            for row in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cells) <= max(date_index, usage_index):
                    continue

                records.append(
                    {
                        "Date": cells[date_index],
                        "Data_Usage": cells[usage_index],
                    }
                )

            if records:
                return records

    return []


def parse_usage_from_bars(soup: BeautifulSoup) -> list[dict[str, str]]:
    bars = soup.find_all("rect", class_="MuiBarElement-root")
    if not bars:
        return []

    records = []
    day = 1
    for bar in bars:
        height = bar.get("height")
        if not height:
            continue

        try:
            height_value = float(height)
        except ValueError:
            continue

        records.append(
            {
                "Date": str(day),
                "Data_Usage": str(height_value),
            }
        )
        day += 1

    return records


def extract_json_candidates(text: str) -> list[str]:
    candidates: list[str] = []

    json_parse_match = re.search(r"JSON\.parse\((.+)\)", text)
    if json_parse_match:
        raw = json_parse_match.group(1).strip().strip(";")
        raw = raw.strip("\"'")
        raw = raw.encode("utf-8").decode("unicode_escape")
        candidates.append(raw)

    if text.startswith("{") or text.startswith("["):
        candidates.append(text)
        return candidates

    for match in re.finditer(r"({.*})", text, re.DOTALL):
        candidates.append(match.group(1))

    for match in re.finditer(r"(\[.*\])", text, re.DOTALL):
        candidates.append(match.group(1))

    return candidates


def safe_json_loads(text: str) -> object | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def find_usage_records(data: object) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []

    if isinstance(data, dict):
        record = normalize_record(data)
        if record:
            records.append(record)

        for value in data.values():
            records.extend(find_usage_records(value))

    elif isinstance(data, list):
        for item in data:
            records.extend(find_usage_records(item))

    return records


def normalize_record(item: dict) -> dict[str, str] | None:
    lower_keys = {k.lower(): k for k in item.keys()}

    date_key = None
    for key in ["date", "day", "usage_date", "usageDate", "usage_day"]:
        if key.lower() in lower_keys:
            date_key = lower_keys[key.lower()]
            break

    usage_key = None
    for key in [
        "usage",
        "data_usage",
        "datausage",
        "used",
        "gb",
        "usage_gb",
        "datausagegb",
        "downloaded",
        "bytes",
    ]:
        if key.lower() in lower_keys:
            usage_key = lower_keys[key.lower()]
            break

    if not date_key or not usage_key:
        return None

    date_value = str(item.get(date_key, "")).strip()
    usage_value = item.get(usage_key)

    if date_value == "":
        return None

    usage_text = format_usage_value(usage_key, usage_value)
    if usage_text == "":
        return None

    return {"Date": date_value, "Data_Usage": usage_text}


def format_usage_value(key: str, value: object) -> str:
    if value is None:
        return ""

    if isinstance(value, (int, float)):
        if "byte" in key.lower():
            gb_value = float(value) / (1024**3)
            return f"{gb_value:.2f} GB"
        return f"{value} GB"

    value_text = str(value).strip()
    if value_text == "":
        return ""

    return value_text


def dedupe_records(records: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    deduped = []

    for record in records:
        key = (record.get("Date"), record.get("Data_Usage"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)

    return deduped
