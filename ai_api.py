import os
import re
import yaml
import openai
import logging
import tiktoken
from datetime import datetime
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_INPUT_TOKENS = 25000  # Max tokens for final GPT-4.1 prompt
CHUNK_TOKENS = 10000      # Tokens per chunk for summarization
MAX_CHUNKS = 5            # Max number of chunks to process

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def clean_response_text(text: str) -> str:
    text = re.sub(r'^\s*```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```\s*$', '', text, flags=re.IGNORECASE)
    return text.strip()

def chunk_text(text, max_chunk_tokens=CHUNK_TOKENS, model="gpt-4o-mini"):
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_chunk_tokens):
        chunk_tokens = tokens[i:i+max_chunk_tokens]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks[:MAX_CHUNKS]

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

    encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    tokens = encoding.encode(text)

    current_date = datetime.now().strftime("%Y-%m-%d")
    prompt_filled = prompt_template.replace("{{current_date}}", current_date)

    # If input is small enough, send directly to GPT-4.1
    if len(tokens) <= MAX_INPUT_TOKENS:
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

    # Otherwise chunk and summarize with cheaper model first
    chunks = chunk_text(text)
    summaries = []
    for i, chunk in enumerate(chunks, 1):
        summary_prompt = (
            "Please provide a concise summary of the following document chunk "
            f"(part {i} of {len(chunks)}), focusing on private investment rounds and relevant financial details:\n\n"
            + chunk
        )
        try:
            logger.info(f"Summarizing chunk {i}/{len(chunks)} with cheaper model...")
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # cheaper model for summarization; can switch to "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": "You are a helpful assistant specialized in summarizing financial documents."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=500,
                temperature=0.3,
            )
            raw_summary = response.choices[0].message.content
            cleaned_summary = clean_response_text(raw_summary)
            summaries.append(cleaned_summary)
        except Exception as e:
            logger.error(f"OpenAI API error during chunk {i} summary: {e}")
            summaries.append(f"❌ Error summarizing chunk {i}")

    combined_summary = "\n\n".join(summaries)
    final_prompt = prompt_filled + "\n\nHere is the combined summary of the document:\n\n" + combined_summary

    try:
        logger.info("Sending combined summary to OpenAI GPT-4.1 for final analysis...")
        final_response = openai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a financial analyst specializing in private investment rounds before IPO."},
                {"role": "user", "content": final_prompt}
            ],
            max_tokens=1000,
            temperature=0.2,
        )
        raw_final_output = final_response.choices[0].message.content
        cleaned_final_output = clean_response_text(raw_final_output)
        return cleaned_final_output

    except Exception as e:
        logger.error(f"OpenAI API error during final analysis: {e}")
        return None

async def ask_gpt(prompt: str, model="gpt-4.1", temperature=0.3, max_tokens=500) -> str:
    config = load_config()
    api_key = config.get("openai_api_key") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found.")
        return None

    openai.api_key = api_key

    try:
        logger.info("Sending custom prompt to GPT...")
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that checks for semantic duplication in text summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        raw_output = response.choices[0].message.content
        return clean_response_text(raw_output)
    except Exception as e:
        logger.error(f"Error calling GPT in ask_gpt(): {e}")
        return None
