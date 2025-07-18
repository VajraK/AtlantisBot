import yaml
from datetime import date, timedelta, datetime
import os
import asyncio
import glob
from sec_scraper import scrape_filing_links
from sec_downloader import download_filings_with_puppeteer
from ai_api import analyze_filing
from telegram_sender import TelegramSender

telegram_sender = TelegramSender()
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
    queries = config.get("sec", {}).get("queries")

    # Fallback to single 'query' key if 'queries' is not provided
    if not queries:
        queries = [config.get("sec", {}).get("query", "PIPE Subscription Agreement")]

    days_back = config.get("sec", {}).get("days_back", 1)
    print(f"🔍 Searching for queries over past {days_back} day(s): {queries}")

    all_filings = []

    for query in queries:
        print(f"\n🔍 Searching for: '{query}'")
        filings = await scrape_filing_links(query=query, days_back=days_back)
        if filings:
            all_filings.extend(filings)
        else:
            print(f"❌ No filings found for '{query}'")

    # Remove duplicates while preserving order
    seen = set()
    unique_filings = [f for f in all_filings if not (f in seen or seen.add(f))]

    if not unique_filings:
        print("❌ No filings found across all queries.")
        return

    # Load past filings and check for new ones
    data = load_filings()
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_str = today.isoformat()
    yesterday_str = yesterday.isoformat()
    now_str = datetime.now().isoformat(timespec='seconds')

    seen_filings = set()
    for key, links in data.items():
        if key.startswith(today_str) or key.startswith(yesterday_str):
            seen_filings.update(links)

    new_filings = [f for f in unique_filings if f not in seen_filings]

    if not new_filings:
        print("ℹ️ No new filings to save today.")
        return

    print(f"🆕 Found {len(new_filings)} new filing(s) across all queries.")
    data[now_str] = new_filings
    save_filings(data)

    print(f"⬇️ Starting download of {len(new_filings)} filings...")
    await download_filings_with_puppeteer(new_filings)
    print("✅ All filings downloaded.")

    # Proceed with the rest of the pipeline
    folders = sorted(glob.glob(f"filings/{today_str}*"), reverse=True)
    if not folders:
        print(f"❌ No download folder found for today: {today_str}")
        return

    download_dir = folders[0]
    print(f"📂 Analyzing files in: {download_dir}")

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
        if result and result.strip() != 'X':
            await telegram_sender.send_filing_result(result, filename)

        # 💾 Optionally save output to .gpt.txt
        if result:
            out_path = full_path.replace(".html", ".gpt.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(result)

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
