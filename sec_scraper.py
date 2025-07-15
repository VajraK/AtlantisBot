import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from datetime import datetime, timedelta
from urllib.parse import quote

async def wait_for_filings_table(page, selector="#hits > table > tbody > tr", retries=3, delay=10):
    for attempt in range(retries):
        try:
            print(f"Waiting for selector '{selector}', attempt {attempt+1}...")
            await page.wait_for_selector(selector, timeout=delay * 1000)
            return True
        except PlaywrightTimeoutError:
            print(f"Attempt {attempt + 1} waiting for selector timed out, retrying...")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                content = await page.content()
                print("Page content snippet on failure:", content[:1000])
                raise

async def scrape_filing_links(query: str, days_back: int = 1):
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
    results_set = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        # Initial wait for JS to populate results
        await asyncio.sleep(3)

        while True:
            await wait_for_filings_table(page, selector="#hits > table > tbody > tr", retries=3, delay=10)

            rows = await page.query_selector_all("#hits > table > tbody > tr")
            print(f"Found {len(rows)} rows on current page.")

            for row in rows:
                link_elem = await row.query_selector("td.filetype > a.preview-file")
                if not link_elem:
                    continue
                href = await link_elem.get_attribute("href")
                if href and href.startswith("http") and href not in results_set:
                    results.append(href)
                    results_set.add(href)

            # Find the next page button by data-value attribute
            next_page_link = None
            try:
                next_page_link = await page.query_selector('li.page-item > a.page-link[data-value="nextPage"]')
                if not next_page_link:
                    print("Next page link does not exist.")
                    break

                visible = await next_page_link.is_visible()
                if not visible:
                    print("Next page link is not visible.")
                    break

                # Check if parent li is disabled or hidden
                parent_li = await next_page_link.evaluate_handle("el => el.parentElement")
                style = await parent_li.get_attribute("style") or ""
                class_attr = await parent_li.get_attribute("class") or ""

                if "display: none" in style or "disabled" in class_attr.lower():
                    print("No more pages available (Next page link disabled or hidden).")
                    break

                print("Clicking 'Next page' link...")
                await next_page_link.scroll_into_view_if_needed()
                await next_page_link.click()

                # Wait for new rows to load
                await page.wait_for_selector("#hits > table > tbody > tr", timeout=15000)
                await asyncio.sleep(3)

            except PlaywrightError as e:
                print(f"Failed to click next page link or wait for new results: {e}")
                break

        await browser.close()

    return results
