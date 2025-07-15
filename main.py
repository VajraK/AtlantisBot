import yaml
from datetime import datetime
from sec_scraper import scrape_filing_links

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    query = config.get("sec", {}).get("query", "PIPE Subscription Agreement")
    days_back = config.get("sec", {}).get("days_back", 1)

    print(f"🔍 Searching for: '{query}' over past {days_back} day(s)")

    filings = scrape_filing_links(query=query, days_back=days_back)

    if not filings:
        print("❌ No filings found.")
        return

    print(f"✅ Found {len(filings)} filings:")
    for f in filings:
        print(f" - {f}")

if __name__ == "__main__":
    main()
