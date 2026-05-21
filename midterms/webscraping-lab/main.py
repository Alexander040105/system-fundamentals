from __future__ import annotations

import sys
from pathlib import Path

from scraper.auth import login
from scraper.api_client import fetch_usage_api
from scraper.config import Config
from scraper.driver import build_driver
from scraper.exporter import export_to_csv
from scraper.usage_page import navigate_to_usage_page, save_page_html, scrape_usage
from scraper.utils import safe_sleep


def run() -> int:
    """Entry point for the scraper."""

    try:
        config = Config.from_env()
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        return 1

    driver = None
    try:
        driver = build_driver(config)

        # Login and wait for authentication.
        login(driver, config)

        # Respect crawl-delay between login and usage page access.
        safe_sleep(config.crawl_delay_seconds)

        records = []

        if config.api_usage_url:
            try:
                records, json_path = fetch_usage_api(driver, config.api_usage_url)
                if records:
                    print(f"Saved API payload to: {json_path}")
                else:
                    print(f"API response saved to: {json_path}")
            except Exception as exc:
                print(f"API fetch failed, falling back to page scrape: {exc}")

        if not records:
            # Navigate to the authenticated usage page and scrape data.
            navigate_to_usage_page(driver, config)
            scrape_result = scrape_usage(driver)

            if not scrape_result.records:
                html_path = save_page_html("output", scrape_result.page_html)
                print("No records extracted from the page.")
                print(f"Saved HTML snapshot to: {html_path}")
                return 2

            records = scrape_result.records

        output_path = export_to_csv(records, config.output_csv)
        print(f"Saved {len(records)} records to: {output_path}")

    except Exception as exc:
        print(f"Unexpected error: {exc}")
        return 3
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(run())
