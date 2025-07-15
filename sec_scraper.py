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

        # Initial wait for JS to populate results
        time.sleep(2)

        while True:
            wait_for_filings_table(page, selector="#hits > table > tbody > tr", retries=3, delay=10)

            rows = page.query_selector_all("#hits > table > tbody > tr")
            print(f"Found {len(rows)} rows on current page.")

            for row in rows:
                link_elem = row.query_selector("td.filetype > a.preview-file")
                if not link_elem:
                    continue
                href = link_elem.get_attribute("href")
                if href and href.startswith("http") and href not in results:
                    results.append(href)

            # Check for 'Next page' link presence and enabled state
            next_page_link = page.query_selector('li.page-item > a.page-link[data-value="nextPage"]')
            if next_page_link:
                parent_li = next_page_link.evaluate_handle("el => el.parentElement")
                style = parent_li.get_attribute("style") or ""
                class_attr = parent_li.get_attribute("class") or ""

                if "display: none" in style or "disabled" in class_attr.lower():
                    print("No more pages available (Next page link disabled or hidden).")
                    break

                print("Clicking 'Next page' link...")
                next_page_link.click()
                # Wait for new content to load
                time.sleep(5)
            else:
                print("No 'Next page' link found.")
                break

        browser.close()

    return results
