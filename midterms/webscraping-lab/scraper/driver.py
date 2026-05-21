from __future__ import annotations

import inspect

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .config import Config


def build_driver(config: Config) -> webdriver.Chrome:
    """Create a Chrome WebDriver with optional headless mode."""

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

    if config.headless:
        options.add_argument("--headless=new")

    if config.chrome_binary_path:
        options.binary_location = config.chrome_binary_path

    if config.user_data_dir:
        options.add_argument(f"--user-data-dir={config.user_data_dir}")
    if config.profile_dir:
        options.add_argument(f"--profile-directory={config.profile_dir}")

    if config.chromedriver_version:
        init_params = inspect.signature(ChromeDriverManager.__init__).parameters
        if "driver_version" in init_params:
            manager = ChromeDriverManager(driver_version=config.chromedriver_version)
        else:
            manager = ChromeDriverManager(version=config.chromedriver_version)
        service = Service(manager.install())
    else:
        service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)
