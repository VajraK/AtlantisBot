import os
import yaml
import openai
import asyncio
import sys
from bs4 import BeautifulSoup
import logging
import tiktoken
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_INPUT_TOKENS = 27000  # Leave room for output

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def clean_response_text(text: str) -> str:
    import re
    text = re.sub(r'^\s*```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```\s*$', '', text, flags=re.IGNORECASE)
    return text.strip()

def truncate_text_to_max_tokens(text: str, max_tokens=MAX_INPUT_TOKENS, model="gpt-4o-mini"):
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        logger.info(f"Text too long ({len(tokens)} tokens), truncating to {max_tokens} tokens.")
        tokens = tokens[:max_tokens]
        truncated_text = encoding.decode(tokens)
        return truncated_text
    return text

async def analyze_filing(filepath: str) -> str:
    config = load_config()
    api_key = config.get("openai_api_key") or os.environ.get("OPENAI_API_KEY")
    prompt_template = config.get("prompt")

    if not api_key:
        logger.error("OpenAI API key not found.")
        return None
    if not prompt_template:
        logger.error("Prompt not found in config.yaml.")
        return None

    openai.api_key = api_key

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            text = soup.get_text(separator="\n").strip()
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return None

    text = truncate_text_to_max_tokens(text, max_tokens=MAX_INPUT_TOKENS)

    current_date = datetime.now().strftime("%Y-%m-%d")
    prompt_filled = prompt_template.replace("{{current_date}}", current_date)
    full_prompt = prompt_filled + "\n\nHere is the document:\n\n" + text

    try:
        logger.info("Sending request to OpenAI GPT-4.1...")
        response = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a financial analyst specializing in private investment rounds before IPO."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1000,
            temperature=0.2,
        )
        raw_output = response.choices[0].message.content
        cleaned_output = clean_response_text(raw_output)
        return cleaned_output

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ai_api.py <path_to_html_filing>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    async def main():
        logger.info(f"Analyzing {file_path}...")
        result = await analyze_filing(file_path)
        print("\n📊 GPT Result:")
        print(result or "❌ No response or error.")

    asyncio.run(main())
