from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

from datetime import datetime, timedelta

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


WAIT_SECONDS = 20
LOGIN_URL = "https://www.starlink.com/auth/login"
API_URL = (
    "https://starlink.com/api/telemetryagg/v1/data-usage/account/"
    "ACC-2735603-74738-20/service-line/AST-2293597-46342-54/annotated"
)


def _default_user_data_dir() -> str:
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        return ""
    brave_user_data = Path(local_app_data) / "BraveSoftware" / "Brave-Browser" / "User Data"
    if brave_user_data.exists():
        return str(brave_user_data)
    return str(Path(local_app_data) / "Google" / "Chrome" / "User Data")


def _default_binary_path() -> str:
    program_files = os.getenv("PROGRAMFILES")
    if program_files:
        brave_path = Path(program_files) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe"
        if brave_path.exists():
            return str(brave_path)
    return ""


def build_driver() -> tuple[webdriver.Chrome, bool]:
    debug_port = os.getenv("CHROME_DEBUG_PORT", "").strip()
    debug_host = os.getenv("CHROME_DEBUG_HOST", "127.0.0.1").strip() or "127.0.0.1"
    chromedriver_version = os.getenv("CHROMEDRIVER_VERSION", "").strip()

    if debug_port:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", f"{debug_host}:{debug_port}")
        if chromedriver_version:
            service = Service(ChromeDriverManager(driver_version=chromedriver_version).install())
        else:
            service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options), True

    options = webdriver.ChromeOptions()

    # Reduce automation fingerprints.
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    chrome_binary = os.getenv("CHROME_BINARY", "").strip() or _default_binary_path()
    if chrome_binary:
        options.binary_location = chrome_binary

    user_data_dir = os.getenv("CHROME_USER_DATA_DIR", "").strip() or _default_user_data_dir()
    profile_dir = os.getenv("CHROME_PROFILE_DIR", "").strip() or "Default"
    if user_data_dir:
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument(f"--profile-directory={profile_dir}")

    if chromedriver_version:
        service = Service(ChromeDriverManager(driver_version=chromedriver_version).install())
    else:
        service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Hide webdriver flag in the DOM on every new document.
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        },
    )
    return driver, False


def wait_for_page_ready(driver: webdriver.Chrome, timeout: int) -> None:
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def read_page_payload(driver: webdriver.Chrome) -> tuple[str, bool]:
    try:
        body = driver.find_element(By.TAG_NAME, "body")
    except NoSuchElementException:
        return "", False

    text = body.text.strip()
    if text.startswith("{") or text.startswith("["):
        return text, True
    return driver.page_source, False


def save_output(payload: str, output_path: Path, is_json: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if is_json:
        parsed = json.loads(payload)
        output_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    else:
        output_path.write_text(payload, encoding="utf-8")


def export_usage_csv(payload: str, output_path: Path) -> bool:
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return False

    cycles = parsed.get("content", {}).get("billingCyclesAnnotated", [])
    if not cycles:
        return False

    extracted_rows: list[list[str]] = []
    for cycle in cycles:
        start_date_raw = cycle.get("startDate")
        if not start_date_raw:
            continue
        start_date = datetime.strptime(start_date_raw.split("T")[0], "%Y-%m-%d")
        daily_data = cycle.get("dailyData", [])

        for index, usage_wrapper in enumerate(daily_data):
            current_day = start_date + timedelta(days=index)
            current_day_str = current_day.strftime("%Y-%m-%d")
            if usage_wrapper and len(usage_wrapper) > 0:
                gb_value = round(float(usage_wrapper[0]), 2)
            else:
                gb_value = 0.0
            extracted_rows.append([current_day_str, f"{gb_value} GB"])

    if not extracted_rows:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Data Usage"])
        writer.writerows(extracted_rows)
    return True


def run() -> int:
    driver = None
    try:
        driver, attached = build_driver()
        if not attached:
            driver.get(LOGIN_URL)

            print("Log in manually, then press Enter to continue...")
            input()
        else:
            print("Using existing Chrome session via remote debugging.")

        driver.get(API_URL)
        wait_for_page_ready(driver, WAIT_SECONDS)

        # Ensure body is present before reading content.
        WebDriverWait(driver, WAIT_SECONDS).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        payload, is_json = read_page_payload(driver)
        if not payload:
            print("No content found on the API page.")
            return 2

        print(payload)

        output_path = Path("output") / "data_usage.json"
        save_output(payload, output_path, is_json)
        print(f"Saved output to: {output_path}")

        if is_json:
            csv_path = Path("output") / "starlink_daily_usage.csv"
            if export_usage_csv(payload, csv_path):
                print(f"Saved CSV output to: {csv_path}")
            else:
                print("No usage rows detected for CSV export.")

    except TimeoutException:
        print("Timed out waiting for the page to load.")
        return 1
    except (NoSuchElementException, WebDriverException, ValueError) as exc:
        print(f"Browser error: {exc}")
        return 1
    finally:
        if driver and not attached:
            try:
                driver.quit()
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(run())
