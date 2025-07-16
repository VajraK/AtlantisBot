import sys
import os
import tiktoken
from bs4 import BeautifulSoup

# Pricing per 1,000 tokens
PRICING = {
    "gpt-4.1": {"input": 0.002, "output": 0.008},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}

def extract_text_from_html(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            text = soup.get_text(separator="\n")
            return text.strip()
    except Exception as e:
        print(f"❌ Error reading or parsing HTML: {e}")
        sys.exit(1)

def count_tokens(text, model="gpt-4-turbo"):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print(f"⚠️ Model '{model}' not recognized by tiktoken. Using cl100k_base.")
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def estimate_gpt_cost(input_tokens, model="gpt-4-turbo", output_tokens_estimate=None):
    if output_tokens_estimate is None:
        output_tokens_estimate = int(input_tokens * 0.3)

    if model not in PRICING:
        print(f"⚠️ Unknown model '{model}'. Falling back to gpt-4-turbo.")
        model = "gpt-4-turbo"

    cost_input = (input_tokens / 1000) * PRICING[model]["input"]
    cost_output = (output_tokens_estimate / 1000) * PRICING[model]["output"]
    total_cost = cost_input + cost_output

    return {
        "model": model,
        "input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens_estimate,
        "estimated_cost_usd": round(total_cost, 4)
    }

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Estimate GPT model token usage and cost for an HTML file.")
    parser.add_argument("filepath", help="Path to HTML file (e.g., filing_1.html)")
    parser.add_argument(
        "--model",
        choices=["gpt-3.5-turbo", "gpt-4.1", "gpt-4-turbo"],
        default="gpt-4-turbo",
        help="Model to estimate cost for (default: gpt-4-turbo)"
    )
    args = parser.parse_args()

    if not os.path.exists(args.filepath):
        print(f"❌ File not found: {args.filepath}")
        sys.exit(1)

    text = extract_text_from_html(args.filepath)
    input_tokens = count_tokens(text, model=args.model)
    estimate = estimate_gpt_cost(input_tokens, model=args.model)

    print("\n📊 OpenAI Cost Estimate")
    print("------------------------------------")
    print(f"📄 File: {os.path.basename(args.filepath)}")
    print(f"🧠 Model: {estimate['model']}")
    print(f"🔢 Input Tokens: {estimate['input_tokens']}")
    print(f"🔢 Estimated Output Tokens: {estimate['estimated_output_tokens']}")
    print(f"💵 Estimated Cost: ${estimate['estimated_cost_usd']}")
    print("------------------------------------\n")

if __name__ == "__main__":
    main()
