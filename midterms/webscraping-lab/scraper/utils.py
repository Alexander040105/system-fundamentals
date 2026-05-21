from dataclasses import dataclass
from pathlib import Path
import os
import time

from dotenv import load_dotenv


@dataclass
class Config:
    email: str
    password: str
    login_url: str
    auth_url: str | None
    usage_url: str
    api_usage_url: str | None
    crawl_delay: int
    output_csv: str
    email_field: str
    password_field: str
    csrf_field: str


def load_config() -> Config:
    load_dotenv()

    email = os.getenv("STARLINK_EMAIL", "").strip()
    password = os.getenv("STARLINK_PASSWORD", "").strip()

    if not email or not password:
        raise ValueError(
            "Missing credentials. Set STARLINK_EMAIL and STARLINK_PASSWORD in .env."
        )

    login_url = os.getenv("STARLINK_LOGIN_URL", "https://starlink.com/account/login").strip()
    usage_url = os.getenv(
        "STARLINK_USAGE_URL",
        "https://starlink.com/account/service-line/AST-2293597-46342-54",
    ).strip()

    auth_url = os.getenv("STARLINK_AUTH_URL", "").strip() or None
    api_usage_url = os.getenv("STARLINK_API_USAGE_URL", "").strip() or None

    crawl_delay = int(os.getenv("STARLINK_CRAWL_DELAY", "10"))
    output_csv = os.getenv("OUTPUT_CSV", "output/data_usage.csv").strip()

    email_field = os.getenv("STARLINK_LOGIN_FIELD_EMAIL", "email").strip()
    password_field = os.getenv("STARLINK_LOGIN_FIELD_PASSWORD", "password").strip()
    csrf_field = os.getenv("STARLINK_CSRF_FIELD", "csrf_token").strip()

    return Config(
        email=email,
        password=password,
        login_url=login_url,
        auth_url=auth_url,
        usage_url=usage_url,
        api_usage_url=api_usage_url,
        crawl_delay=crawl_delay,
        output_csv=output_csv,
        email_field=email_field,
        password_field=password_field,
        csrf_field=csrf_field,
    )


def get_default_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0 Safari/537.36"
        ),
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }


def sleep_for_crawl_delay(config: Config, reason: str) -> None:
    if config.crawl_delay <= 0:
        return

    print(f"Sleeping {config.crawl_delay}s ({reason})")
    time.sleep(config.crawl_delay)


def ensure_output_dir(output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)
