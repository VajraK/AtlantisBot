import os
from datetime import date, timedelta
from ai_api import ask_gpt  # This now works!

def get_recent_gpt_texts(base_folder="filings"):
    today = date.today()
    yesterday = today - timedelta(days=1)
    relevant_days = [today.isoformat(), yesterday.isoformat()]
    texts = []

    for folder in os.listdir(base_folder):
        if any(folder.startswith(day) for day in relevant_days):
            folder_path = os.path.join(base_folder, folder)
            if not os.path.isdir(folder_path):
                continue
            for file in os.listdir(folder_path):
                if file.endswith(".gpt.txt"):
                    try:
                        with open(os.path.join(folder_path, file), "r", encoding="utf-8") as f:
                            texts.append(f.read().strip())
                    except Exception:
                        continue

    return texts

async def is_duplicate(new_text: str) -> bool:
    old_texts = get_recent_gpt_texts()
    if not old_texts:
        return False  # No comparison = not a duplicate

    prompt = f"""
You are a financial analyst reviewing summaries of SEC PIPE filings for potential duplication.

You are given a **NEW filing summary** and a list of **OLD filing summaries** from the past 48 hours.

Determine if the new summary is **semantically duplicative** of any previous ones — meaning it describes essentially the same transaction, investment structure, terms, or parties (e.g., same PIPE amount, company, instruments, timing, or contact info).

Filings may differ in wording or formatting, but if they describe the same PIPE deal or closely related tranches, they are considered duplicates.

Reply ONLY with one word:
- "YES" if it's a duplicate
- "NO" if it's materially different or substantively unique

NEW FILING:
{new_text}

OLD FILINGS:
{chr(10).join(old_texts)}
"""

    response = await ask_gpt(prompt)
    return response.strip().lower().startswith("yes")
