from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    login_url: str
    usage_url: str
    api_usage_url: str
    email: str
    password: str
    output_csv: str
    crawl_delay_seconds: int
    headless: bool
    chrome_binary_path: str
    chromedriver_version: str
    manual_login: bool
    user_data_dir: str
    profile_dir: str
    email_selector: str
    password_selector: str
    submit_selector: str

    @staticmethod
    def _get_bool(value: str, default: bool = False) -> bool:
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "y"}

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()

        login_url = os.getenv("STARLINK_LOGIN_URL", "").strip()
        usage_url = os.getenv("STARLINK_USAGE_URL", "").strip()
        api_usage_url = os.getenv("STARLINK_API_USAGE_URL", "").strip()
        email = os.getenv("STARLINK_EMAIL", "").strip()
        password = os.getenv("STARLINK_PASSWORD", "").strip()
        output_csv = os.getenv("OUTPUT_CSV", "output/data_usage.csv").strip()
        crawl_delay = int(os.getenv("STARLINK_CRAWL_DELAY", "10"))
        headless = cls._get_bool(os.getenv("HEADLESS"), default=False)
        chrome_binary_path = os.getenv("CHROME_BINARY", "").strip()
        chromedriver_version = os.getenv("CHROMEDRIVER_VERSION", "").strip()
        manual_login = cls._get_bool(os.getenv("MANUAL_LOGIN"), default=False)
        user_data_dir = os.getenv("USER_DATA_DIR", "").strip()
        profile_dir = os.getenv("PROFILE_DIR", "").strip()

        # Optional selectors for flexible page structures.
        email_selector = os.getenv("STARLINK_EMAIL_SELECTOR", "[data-testid='email'] input").strip()
        password_selector = os.getenv("STARLINK_PASSWORD_SELECTOR", "[data-testid='password'] input").strip()
        submit_selector = os.getenv("STARLINK_SUBMIT_SELECTOR", "button[type='submit']").strip()

        missing = [
            name
            for name, value in [
                ("STARLINK_LOGIN_URL", login_url),
                ("STARLINK_USAGE_URL", usage_url),
                ("STARLINK_EMAIL", email),
                ("STARLINK_PASSWORD", password),
            ]
            if not value
        ]
        if missing:
            missing_csv = ", ".join(missing)
            raise ValueError(f"Missing required environment variables: {missing_csv}")

        return cls(
            login_url=login_url,
            usage_url=usage_url,
            api_usage_url=api_usage_url,
            email=email,
            password=password,
            output_csv=output_csv,
            crawl_delay_seconds=crawl_delay,
            headless=headless,
            chrome_binary_path=chrome_binary_path,
            chromedriver_version=chromedriver_version,
            manual_login=manual_login,
            user_data_dir=user_data_dir,
            profile_dir=profile_dir,
            email_selector=email_selector,
            password_selector=password_selector,
            submit_selector=submit_selector,
        )
