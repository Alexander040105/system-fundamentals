# Starlink Daily Usage Scraper

## Project Overview
This project fetches Starlink daily usage data with Selenium, using a Brave browser session (remote debugging) for manual login. It saves the raw API JSON and exports a clean CSV of daily usage.

## Ethical Scraping Notice
Always respect the website terms of service and access policies. Keep requests minimal.

## Technologies Used
- Python
- Selenium WebDriver
- webdriver-manager

## Installation
1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.

## Virtual Environment Setup
```bash
python -m venv .venv
\.venv\Scripts\activate
```

## Install Requirements
```bash
pip install -r requirements.txt
```

## Configure Environment Variables
Optional variables used by the manual fetch script:
```env
CHROME_BINARY=C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe
CHROMEDRIVER_VERSION=148
CHROME_DEBUG_PORT=9222
CHROME_DEBUG_HOST=127.0.0.1
CHROME_USER_DATA_DIR=C:\BraveDebugProfile
CHROME_PROFILE_DIR=Default
```

## Run the Manual Fetch (Recommended)
1. Close all Brave windows.
2. Start Brave in remote debugging mode:
```cmd
start "" "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" --remote-debugging-port=9222 --user-data-dir="C:\BraveDebugProfile"
```
3. Log in to Starlink in the new Brave window.
4. Run the script from PowerShell:
```powershell
$env:CHROMEDRIVER_VERSION=148
$env:CHROME_DEBUG_PORT=9222
python .\manual_starlink_api_fetch.py
```

## Outputs
- JSON: output/data_usage.json
- CSV: output/starlink_daily_usage.csv

CSV format:
```
Date,Data Usage
2026-05-01,12.5 GB
2026-05-02,10.2 GB
```

## Repository Structure
```
webscraping-lab/
├── scraper/
│   ├── __init__.py
│   ├── auth.py
│   ├── config.py
│   ├── driver.py
│   ├── exporter.py
│   ├── usage_page.py
│   └── utils.py
├── output/
│   ├── data_usage.json
│   └── starlink_daily_usage.csv
├── manual_starlink_api_fetch.py
├── main.py
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

## Troubleshooting
- If you see `token_expired`, log in again in the same debug Brave window and rerun.
- If ChromeDriver version errors occur, update `CHROMEDRIVER_VERSION` to match your Brave major version.
- If the CSV is empty, verify the API response contains `content.billingCyclesAnnotated`.

## Security Reminder
Never commit your real `.env` file or credentials. Keep credentials private.
