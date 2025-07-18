import asyncio
import subprocess
import sys
import os
import yaml
from datetime import datetime

# Path to the script to run
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "main.py")

# Path to the config file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

async def run_every_x_minutes(interval_minutes: int):
    while True:
        print(f"⏳ Starting run at {datetime.now().isoformat()}")
        process = await asyncio.create_subprocess_exec(
            sys.executable,
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

        print(f"🕒 Sleeping for {interval_minutes} minutes...\n")
        await asyncio.sleep(interval_minutes * 60)

if __name__ == "__main__":
    config = load_config()
    interval = config.get("interval_minutes", 30)  # Default to 30 if not set
    asyncio.run(run_every_x_minutes(interval))
