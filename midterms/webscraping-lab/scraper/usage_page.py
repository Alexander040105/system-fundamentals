from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import Config
from .utils import wait_for_element


@dataclass
class UsageRecord:
    date: str
    usage: str


@dataclass
class ScrapeResult:
    records: List[UsageRecord]
    page_html: str


def navigate_to_usage_page(driver: WebDriver, config: Config, timeout: int = 30) -> None:
    """Navigate to the authenticated usage page."""

    driver.get(config.usage_url)
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    # Wait for a likely data container or table to appear.
    wait_for_element(
        driver,
        [
            "table",
            "[data-testid*='usage']",
            "[class*='usage']",
        ],
        timeout=timeout,
    )


def _normalize_header(text: str) -> str:
    return "".join(ch for ch in text.lower().strip() if ch.isalnum())


def _extract_from_table(driver: WebDriver) -> List[UsageRecord]:
    table = driver.find_element(By.CSS_SELECTOR, "table")
    headers = [
        _normalize_header(th.text)
        for th in table.find_elements(By.CSS_SELECTOR, "thead th")
    ]

    date_idx = None
    usage_idx = None
    for idx, header in enumerate(headers):
        if "date" in header:
            date_idx = idx
        if "usage" in header or "data" in header:
            usage_idx = idx

    if date_idx is None or usage_idx is None:
        raise ValueError("Could not map table headers to date and usage columns.")

    records: List[UsageRecord] = []
    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    for row in rows:
        cells = row.find_elements(By.CSS_SELECTOR, "td")
        if len(cells) <= max(date_idx, usage_idx):
            continue
        records.append(UsageRecord(cells[date_idx].text.strip(), cells[usage_idx].text.strip()))

    return records


def scrape_usage(driver: WebDriver) -> ScrapeResult:
    """Scrape usage data from the authenticated page."""

    page_html = driver.page_source
    records: List[UsageRecord] = []

    try:
        records = _extract_from_table(driver)
    except Exception:
        # Table parsing may fail if the page uses cards or custom layout.
        # Return empty records but keep HTML for debugging.
        pass

    return ScrapeResult(records=records, page_html=page_html)


def save_page_html(output_dir: str, html: str) -> str:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    html_path = output_path / "usage_page.html"
    html_path.write_text(html, encoding="utf-8")
    return str(html_path)
