import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
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
    results_set = set()  # For fast duplicate checking

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")

        # Initial wait for JS to populate results
        time.sleep(3)

        while True:
            wait_for_filings_table(page, selector="#hits > table > tbody > tr", retries=3, delay=10)

            rows = page.query_selector_all("#hits > table > tbody > tr")
            print(f"Found {len(rows)} rows on current page.")

            for row in rows:
                link_elem = row.query_selector("td.filetype > a.preview-file")
                if not link_elem:
                    continue
                href = link_elem.get_attribute("href")
                if href and href.startswith("http") and href not in results_set:
                    results.append(href)
                    results_set.add(href)

            # Find the next page button by text or aria-label, fallback on data-value attribute
            next_page_link = None
            try:
                next_page_link = page.query_selector('li.page-item > a.page-link[data-value="nextPage"]')
                if not next_page_link or not next_page_link.is_visible():
                    print("Next page link is not visible or does not exist.")
                    break

                # Check if parent li is disabled or hidden
                parent_li = next_page_link.evaluate_handle("el => el.parentElement")
                style = parent_li.get_attribute("style") or ""
                class_attr = parent_li.get_attribute("class") or ""

                if "display: none" in style or "disabled" in class_attr.lower():
                    print("No more pages available (Next page link disabled or hidden).")
                    break

                print("Clicking 'Next page' link...")
                # Scroll into view and click safely
                next_page_link.scroll_into_view_if_needed()
                next_page_link.click()

                # Wait for the rows to refresh by waiting for network idle or specific element changes
                # We'll wait for either new rows or a slight delay for lazy load
                page.wait_for_selector("#hits > table > tbody > tr", timeout=15000)

                # Additional sleep to allow JS to finish loading
                time.sleep(3)

            except PlaywrightError as e:
                print(f"Failed to click next page link or wait for new results: {e}")
                break

        browser.close()

    return results