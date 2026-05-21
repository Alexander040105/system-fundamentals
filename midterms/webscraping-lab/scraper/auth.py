from __future__ import annotations

from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse

from .utils import Config, sleep_for_crawl_delay


def login(session: requests.Session, config: Config) -> None:
    if not config.login_url:
        raise ValueError("STARLINK_LOGIN_URL is required.")

    login_page_url = infer_login_page_url(config.login_url)
    login_page = session.get(login_page_url, timeout=30)
    login_page.raise_for_status()

    csrf_name, csrf_token = extract_csrf_token(login_page.text)
    form_action, form_method = extract_form_target(login_page.text, config.login_url)

    payload = {
        config.email_field: config.email,
        config.password_field: config.password,
    }

    if csrf_token:
        payload[csrf_name or config.csrf_field] = csrf_token

    sleep_for_crawl_delay(config, "before login request")

    post_url = config.auth_url or form_action or config.login_url
    if form_method == "get":
        response = session.get(post_url, params=payload, timeout=30)
    else:
        response = session.post(post_url, data=payload, timeout=30)

    if response.status_code == 405 and form_method != "get":
        response = session.get(post_url, params=payload, timeout=30)

    response.raise_for_status()

    if not is_login_successful(response.text, session):
        raise RuntimeError(
            "Login failed. Inspect the login request in your browser and set "
            "STARLINK_AUTH_URL and field names if needed."
        )


def extract_csrf_token(html: str) -> tuple[str | None, str | None]:
    soup = BeautifulSoup(html, "html.parser")

    selectors = [
        "input[name=csrf]",
        "input[name=_csrf]",
        "input[name=csrf_token]",
        "input[name=authenticity_token]",
    ]

    for selector in selectors:
        field = soup.select_one(selector)
        if field and field.get("value"):
            return field.get("name"), field.get("value")

    meta = soup.select_one("meta[name=csrf-token], meta[name=csrf_token]")
    if meta and meta.get("content"):
        return meta.get("name"), meta.get("content")

    return None, None


def extract_form_target(html: str, base_url: str) -> tuple[str | None, str]:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if not form:
        return None, "post"

    action = form.get("action")
    method = (form.get("method") or "post").lower()
    if not action:
        return None, method

    return urljoin(base_url, action), method


def infer_login_page_url(login_url: str) -> str:
    parsed = urlparse(login_url)
    if "/auth/login" in parsed.path:
        base = f"{parsed.scheme}://{parsed.netloc}"
        return f"{base}/account/login"
    return login_url


def is_login_successful(html: str, session: requests.Session) -> bool:
    if session.cookies:
        return True

    html_lower = html.lower()
    return "account" in html_lower or "logout" in html_lower
