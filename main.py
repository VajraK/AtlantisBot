import yaml
from datetime import date, timedelta
import os
import asyncio
from sec_scraper import scrape_filing_links
from sec_downloader import download_filings_with_puppeteer
from ai_api import analyze_filing

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
    await download_filings_with_puppeteer(to_download)
    print("✅ All filings downloaded.")

    # 🔍 Analyze each downloaded filing
    download_dir = f"filings/{todays_str}"
    if not os.path.isdir(download_dir):
        print(f"❌ Download directory not found: {download_dir}")
        return

    html_files = sorted([f for f in os.listdir(download_dir) if f.endswith(".html")])
    if not html_files:
        print("❌ No HTML filings found in download directory.")
        return

    print(f"🧠 Analyzing {len(html_files)} filing(s) with GPT...")
    for i, filename in enumerate(html_files, 1):
        full_path = os.path.join(download_dir, filename)
        print(f"\n📂 Filing {i}/{len(html_files)}: {filename}")
        result = await analyze_filing(full_path)
        print("📊 GPT Result:")
        print(result or "❌ No response or error.")
        print("-" * 40)

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
