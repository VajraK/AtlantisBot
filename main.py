import yaml
from datetime import date, timedelta, datetime
import os
import asyncio
import glob
import logging

from sec_scraper import scrape_filing_links
from sec_downloader import download_filings_with_puppeteer
from ai_api import analyze_filing
from telegram_sender import TelegramSender

telegram_sender = TelegramSender()
FILENAME = "filings.yaml"

# 🪵 Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("main.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

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

    if not queries:
        queries = [config.get("sec", {}).get("query", "PIPE Subscription Agreement")]

    days_back = config.get("sec", {}).get("days_back", 1)
    logger.info(f"🔍 Searching for queries over past {days_back} day(s): {queries}")

    all_filings = []

    for query in queries:
        logger.info(f"🔍 Searching for: '{query}'")
        filings = await scrape_filing_links(query=query, days_back=days_back)
        if filings:
            all_filings.extend(filings)
        else:
            logger.warning(f"❌ No filings found for '{query}'")

    seen = set()
    unique_filings = [f for f in all_filings if not (f in seen or seen.add(f))]

    if not unique_filings:
        logger.warning("❌ No filings found across all queries.")
        return

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
        logger.info("ℹ️ No new filings to save today.")
        return

    logger.info(f"🆕 Found {len(new_filings)} new filing(s) across all queries.")
    data[now_str] = new_filings
    save_filings(data)

    logger.info(f"⬇️ Starting download of {len(new_filings)} filings...")
    await download_filings_with_puppeteer(new_filings)
    logger.info("✅ All filings downloaded.")

    folders = sorted(glob.glob(f"filings/{today_str}*"), reverse=True)
    if not folders:
        logger.warning(f"❌ No download folder found for today: {today_str}")
        return

    download_dir = folders[0]
    logger.info(f"📂 Analyzing files in: {download_dir}")

    html_files = sorted([f for f in os.listdir(download_dir) if f.endswith(".html")])
    if not html_files:
        logger.warning("❌ No HTML filings found in download directory.")
        return

    logger.info(f"🧠 Analyzing {len(html_files)} filing(s) with GPT...")
    for i, filename in enumerate(html_files, 1):
        full_path = os.path.join(download_dir, filename)
        logger.info(f"📂 Filing {i}/{len(html_files)}: {filename}")
        
        result = await analyze_filing(full_path)
        
        if result:
            logger.info("📊 GPT Result:")
            logger.info(result)
        else:
            logger.warning("❌ No response or error.")
            continue

        out_path = full_path.replace(".html", ".gpt.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        logger.info(f"💾 Saved GPT result to: {out_path}")

        from duplicate_checker import is_duplicate
        logger.info("🔍 Checking for duplicates...")
        is_dup = await is_duplicate(result)

        if not is_dup and result.strip() != 'X':
            logger.info("📬 Sending unique filing to Telegram...")
            await telegram_sender.send_filing_result(result, filename)
        else:
            logger.warning("⚠️ Duplicate filing skipped.")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
