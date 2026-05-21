from __future__ import annotations

from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import Config
from .utils import wait_for_element


def login(driver: WebDriver, config: Config, timeout: int = 30) -> None:
    """Log in to Starlink using the configured credentials."""

    driver.get(config.login_url)

    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    if config.manual_login:
        print(
            "Manual login enabled. Complete login in the browser. "
            "Waiting until the URL contains /account..."
        )
        WebDriverWait(driver, timeout * 6).until(
            lambda d: "/account" in d.current_url
        )
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return

    # Wait for the login form fields to appear.
    email_selectors = [
        config.email_selector,
        "[data-testid='email'] input",
        "input[name='email']",
        "input[name='username']",
        "input[type='email']",
        "input[autocomplete='username']",
    ]
    password_selectors = [
        config.password_selector,
        "[data-testid='password'] input",
        "input[name='password']",
        "input[type='password']",
        "input[autocomplete='current-password']",
    ]

    def save_snapshot(name: str) -> Path:
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = output_dir / name
        snapshot_path.write_text(driver.page_source, encoding="utf-8")
        return snapshot_path

    try:
        # Ensure the login form is present before selecting inputs.
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
        )
        email_input = wait_for_element(
            driver,
            email_selectors,
            timeout=timeout,
            visible=False,
            clickable=False,
        )
    except Exception as exc:
        snapshot_path = save_snapshot("login_page.html")
        raise RuntimeError(
            f"Login selectors not found. Saved HTML snapshot to: {snapshot_path}"
        ) from exc

    if email_input.is_enabled():
        email_input.clear()
        email_input.send_keys(config.email)
    # Click submit (Next) after email.
    if email_input.is_enabled():
        try:
            submit_button = wait_for_element(
                driver,
                [config.submit_selector, "button[type='submit']", "button[name='login']"],
                timeout=timeout,
                visible=True,
            )
            submit_button.click()
        except Exception:
            email_input.send_keys(Keys.ENTER)

    # Wait for password step or validation error.
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "[data-testid='password'] input")
            or d.find_elements(By.CSS_SELECTOR, "[data-testid='form-validation-summary']")
        )
    except Exception:
        snapshot_path = save_snapshot("login_after_next.html")
        raise RuntimeError(
            "Login did not advance to the password step. "
            f"Saved HTML snapshot to: {snapshot_path}"
        )

    if driver.find_elements(By.CSS_SELECTOR, "[data-testid='form-validation-summary']"):
        snapshot_path = save_snapshot("login_validation_error.html")
        if config.manual_login:
            print(
                "Login validation error detected. "
                "Solve any captcha or wait for the error to clear in the browser, "
                "then press Enter to continue."
            )
            input()
        else:
            raise RuntimeError(
                "Login showed a validation error after submitting email. "
                f"Saved HTML snapshot to: {snapshot_path}"
            )

    # Wait for password field to appear (two-step flow) or already present.
    try:
        password_input = wait_for_element(
            driver,
            password_selectors,
            timeout=timeout,
            visible=True,
            clickable=True,
        )
    except Exception:
        try:
            password_input = wait_for_element(
                driver,
                password_selectors,
                timeout=timeout,
                visible=False,
                clickable=False,
            )
        except Exception as exc:
            snapshot_path = save_snapshot("login_password_step.html")
            raise RuntimeError(
                f"Password selectors not found. Saved HTML snapshot to: {snapshot_path}"
            ) from exc
    password_input.clear()
    password_input.send_keys(config.password)

    # Click submit or press Enter as a fallback.
    try:
        submit_button = wait_for_element(
            driver,
            [config.submit_selector, "button[type='submit']", "button[name='login']"],
            timeout=timeout,
            visible=True,
        )
        submit_button.click()
    except Exception:
        password_input.send_keys(Keys.ENTER)

    # Wait for authentication to complete by URL change or usage page elements.
    WebDriverWait(driver, timeout).until(
        lambda d: d.current_url != config.login_url
    )

    # Some flows redirect through intermediate pages; wait for a stable document ready state.
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    # Optional: ensure we are authenticated by checking for a logged-in cookie or element.
    WebDriverWait(driver, timeout).until_not(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
    )
