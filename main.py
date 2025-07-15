import yaml
from datetime import date, timedelta
import os
import asyncio
from sec_scraper import scrape_filing_links
from sec_downloader import download_filings

FILENAME = "filings.yaml"

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_filings():
    if os.path.exists(FILENAME):
        with open(FILENAME, "r") as f:
            return yaml.safe_load(f) or {}
    else:
        return {}

def save_filings(data):
    with open(FILENAME, "w") as f:
        yaml.safe_dump(data, f)

async def async_main():
    config = load_config()
    query = config.get("sec", {}).get("query", "PIPE Subscription Agreement")
    days_back = config.get("sec", {}).get("days_back", 1)

    print(f"🔍 Searching for: '{query}' over past {days_back} day(s)")

    filings = await scrape_filing_links(query=query, days_back=days_back)
    if not filings:
        print("❌ No filings found.")
        return

    data = load_filings()

    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    todays_str = date.today().isoformat()

    yesterdays_filings = set(data.get(yesterday_str, []))

    if not yesterdays_filings:
        print(f"ℹ️ No filings found for yesterday ({yesterday_str}). Saving all found filings for today.")
        data[todays_str] = filings
    else:
        print(f"ℹ️ Found {len(yesterdays_filings)} filings from yesterday in YAML.")
        new_filings = [f for f in filings if f not in yesterdays_filings]

        if not new_filings:
            print("ℹ️ No new filings to save today.")
            return

        data[todays_str] = new_filings

    save_filings(data)

    to_download = data[todays_str]
    print(f"⬇️ Starting download of {len(to_download)} filings...")
    await download_filings(to_download, save_folder="./filings")
    print("✅ All filings downloaded.")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
