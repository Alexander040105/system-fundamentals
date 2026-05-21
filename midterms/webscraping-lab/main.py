from scraper.auth import login
from scraper.exporter import export_to_csv
from scraper.parser import parse_usage_from_html, parse_usage_from_json
from scraper.utils import (
    ensure_output_dir,
    get_default_headers,
    load_config,
    sleep_for_crawl_delay,
)

from pathlib import Path
import requests


def main() -> None:
    config = load_config()

    session = requests.Session()
    session.headers.update(get_default_headers())

    login(session, config)

    sleep_for_crawl_delay(config, "before usage page request")

    usage_html = None
    if config.usage_url:
        response = session.get(config.usage_url, timeout=30)
        response.raise_for_status()
        usage_html = response.text

    records = []
    if usage_html:
        records = parse_usage_from_html(usage_html)

    api_payload = None
    if not records and config.api_usage_url:
        sleep_for_crawl_delay(config, "before usage API request")
        api_response = session.get(config.api_usage_url, timeout=30)
        api_response.raise_for_status()
        api_payload = api_response.text
        records = parse_usage_from_json(api_response.json())

    if not records:
        output_dir = Path(ensure_output_dir(config.output_csv)).parent
        if usage_html:
            (output_dir / "usage_page.html").write_text(
                usage_html, encoding="utf-8"
            )
        if api_payload:
            (output_dir / "usage_api.json").write_text(
                api_payload, encoding="utf-8"
            )
        raise RuntimeError(
            "No usage records found. Verify endpoints and parsing rules. "
            "Saved debug files to output/usage_page.html or output/usage_api.json."
        )

    output_path = ensure_output_dir(config.output_csv)
    export_to_csv(records, output_path)
    print(f"Saved {len(records)} records to {output_path}")


if __name__ == "__main__":
    main()
