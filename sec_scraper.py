import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime, timedelta
from urllib.parse import quote

def wait_for_filings_table(page, selector="#hits > table > tbody > tr", retries=3, delay=10):
    for attempt in range(retries):
        try:
            print(f"Waiting for selector '{selector}', attempt {attempt+1}...")
            page.wait_for_selector(selector, timeout=delay * 1000)
            return True
        except PlaywrightTimeoutError:
            print(f"Attempt {attempt + 1} waiting for selector timed out, retrying...")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                # Optionally dump page content for debugging
                content = page.content()
                print("Page content snippet on failure:", content[:1000])
                raise

def scrape_filing_links(query: str, days_back: int = 1):
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days_back)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    encoded_query = quote(quote(query))

    url = (
        f"https://www.sec.gov/edgar/search/#/q={encoded_query}"
        f"&dateRange=custom&startdt={start_str}&enddt={end_str}"
    )

    print(f"Opening SEC search URL:\n{url}")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")

        # Wait a bit for JS to render results container
        time.sleep(2)

        wait_for_filings_table(page, selector="#hits > table > tbody > tr", retries=3, delay=10)

        rows = page.query_selector_all("#hits > table > tbody > tr")
        print(f"Found {len(rows)} rows.")

        for row in rows:
            link_elem = row.query_selector("td.filetype > a.preview-file")
            if not link_elem:
                continue
            href = link_elem.get_attribute("href")
            if href and href.startswith("http"):
                results.append(href)

        browser.close()

    return results
