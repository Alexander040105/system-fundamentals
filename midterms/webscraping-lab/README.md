# Starlink Daily Usage Scraper

## Project Overview
This project logs into a Starlink account, visits the usage page, extracts daily data usage records, and exports the results to a CSV file for academic submission and GitHub publication.

## Ethical Scraping Notice
Always respect the website terms of service and access policies. This project enforces a crawl delay and keeps requests minimal.

## Robots.txt Compliance
The Starlink robots.txt specifies `Crawl-delay: 10`. This scraper waits 10 seconds between major requests to comply.

## Technologies Used
- Python
- requests
- BeautifulSoup (bs4)
- pandas
- python-dotenv

## Installation
1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.

## Virtual Environment Setup
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

## Install Requirements
```bash
pip install -r requirements.txt
```

## Configure Environment Variables
1. Copy `.env.example` to `.env`.
2. Fill in your Starlink credentials and URLs.

Example:
```env
STARLINK_EMAIL=your_email@example.com
STARLINK_PASSWORD=your_password
```

## How to Run
```bash
python main.py
```

## Output Explanation
The scraper writes the output to `output/data_usage.csv` with the format:
```
Date,Data_Usage
2026-05-01,12.5 GB
2026-05-02,10.2 GB
```

## Repository Structure
```
webscraping-lab/
├── scraper/
│   ├── auth.py
│   ├── parser.py
│   ├── exporter.py
│   └── utils.py
├── output/
│   └── data_usage.csv
├── main.py
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

## Troubleshooting
- If login fails, inspect the login request in your browser developer tools and set:
  - `STARLINK_AUTH_URL`
  - `STARLINK_LOGIN_FIELD_EMAIL`
  - `STARLINK_LOGIN_FIELD_PASSWORD`
  - `STARLINK_CSRF_FIELD`
- If no data is found, inspect the usage page or API calls and set `STARLINK_API_USAGE_URL`.

## Security Reminder
Never commit your real `.env` file. Keep credentials private.

## Sample Screenshot Placeholder
Add a screenshot here for the final submission.
