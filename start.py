import asyncio
import subprocess
import sys
import os
from datetime import datetime

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "main.py")

async def run_every_30_minutes():
    while True:
        print(f"⏳ Starting run at {datetime.now().isoformat()}")
        process = await asyncio.create_subprocess_exec(
            sys.executable,  # Automatically uses the Python interpreter running this script (e.g. from venv)
            SCRIPT_PATH,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        print(f"✅ Finished run at {datetime.now().isoformat()} with exit code {process.returncode}")
        if stdout:
            print("📤 Output:\n", stdout.decode())
        if stderr:
            print("⚠️ Errors:\n", stderr.decode())

        print("🕒 Sleeping for 30 minutes...\n")
        await asyncio.sleep(1800)

if __name__ == "__main__":
    asyncio.run(run_every_30_minutes())
