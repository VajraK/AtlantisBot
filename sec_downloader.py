import asyncio
import os
import random
from playwright.async_api import async_playwright

USER_AGENT = "VajraKantor vkantor@hopecapitaladvisors.com"

async def download_filings(filing_urls, save_folder):
    os.makedirs(save_folder, exist_ok=True)

    async with async_playwright() as p:
        # Launch browser with more natural settings
        browser = await p.chromium.launch(
            headless=False,  # Try with visible browser first
            slow_mo=100,    # Adds delay between actions
        )
        
        # Create context with proper headers
        context = await browser.new_context(
            user_agent=USER_AGENT,
            # Add common browser headers
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.sec.gov/',
                'DNT': '1',
            }
        )
        
        page = await context.new_page()
        
        for i, url in enumerate(filing_urls, 1):
            try:
                print(f"⬇️ Downloading filing {i}/{len(filing_urls)}: {url}")
                
                # Add random delay between 2-5 seconds
                await asyncio.sleep(random.uniform(2, 5))
                
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                
                # Add human-like delay after page load
                await asyncio.sleep(random.uniform(1, 3))
                
                content = await page.content()

                filename = os.path.join(save_folder, f"filing_{i}.html")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"✅ Saved {filename}")

            except Exception as e:
                print(f"⚠️ Failed to download {url}: {e}")
                # Longer delay on failure
                await asyncio.sleep(10)

        await browser.close()