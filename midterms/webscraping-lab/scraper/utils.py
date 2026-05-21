from __future__ import annotations

import time
from typing import Iterable, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def wait_for_element(
    driver: WebDriver,
    selectors: Iterable[str],
    timeout: int = 20,
    multiple: bool = False,
    visible: bool = True,
    clickable: bool = False,
):
    """Try a list of selectors and return the first matching element(s)."""

    last_error: Optional[Exception] = None
    for selector in selectors:
        try:
            wait = WebDriverWait(driver, timeout)
            if multiple:
                if visible:
                    return wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, selector)))
                return wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
            if clickable:
                return wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            if visible:
                return wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
            return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except Exception as exc:
            last_error = exc
            continue

    selector_list = ", ".join(selectors)
    raise RuntimeError(
        f"None of the selectors matched an element. Tried: {selector_list}"
    ) from last_error


def safe_sleep(seconds: int) -> None:
    """Respect crawl-delay or cool-down between major actions."""

    if seconds <= 0:
        return
    time.sleep(seconds)
