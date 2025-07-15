import asyncio
import subprocess

async def download_filings_with_puppeteer(filing_urls):
    if not filing_urls:
        print("No filings to download.")
        return

    # Convert list of URLs to args for node script
    args = ["node", "puppeteer_downloader.js"] + filing_urls

    print("▶️ Calling Puppeteer Node.js downloader...")

    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    if stdout:
        print(stdout.decode())

    if stderr:
        print("❗ Puppeteer stderr:", stderr.decode())

    if proc.returncode != 0:
        raise RuntimeError(f"Puppeteer downloader exited with code {proc.returncode}")
