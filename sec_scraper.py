import asyncio
import json

async def scrape_filing_links(query: str, days_back: int = 1):
    # Prepare input data for Node.js process
    input_data = {
        "query": query,
        "days_back": days_back
    }
    input_json = json.dumps(input_data)

    # Start Node.js process
    proc = await asyncio.create_subprocess_exec(
        "node", "puppeteer_scraper.js",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Send input data to Node.js
    stdout, stderr = await proc.communicate(input_json.encode())

    # Handle errors
    if proc.returncode != 0:
        error_message = stderr.decode().strip()
        raise RuntimeError(f"SEC scraper failed: {error_message}")

    # Parse results from stdout
    try:
        results = json.loads(stdout.decode())
        return results
    except json.JSONDecodeError:
        raise RuntimeError("Failed to parse scraper output")