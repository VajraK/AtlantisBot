# AtlantisBot: SEC Filing Scraper + GPT Analyzer + Telegram Notifier

This bot:

1. Searches EDGAR (SEC) filings for a specific keyword (e.g. "PIPE Subscription Agreement").
2. Downloads any new HTML filings from the past 1–2 days.
3. Uses OpenAI's GPT-4 to analyze them.
4. Sends summarized results to a Telegram group.

---

## 🔧 Setup Instructions

### 1. Clone and install dependencies

```bash
git clone https://github.com/yourusername/AtlantisBot.git
cd AtlantisBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 2. Install Puppeteer

Make sure you have **Node.js** installed.

```bash
npm install -g puppeteer
```

Puppeteer is used to reliably download and render HTML content from SEC.gov.

---

### 3. Create `config.yaml`

This file controls your bot's behavior.

```yaml
sec:
  query: "PIPE Subscription Agreement"
  days_back: 1

telegram_bot_token: "YOUR_TELEGRAM_BOT_API_TOKEN"
telegram_chat_id: "YOUR_TELEGRAM_GROUP_CHAT_ID"

openai_api_key: "sk-..."
prompt:
```

- You can get your Telegram bot token from [@BotFather](https://t.me/BotFather).
- To get your group chat ID:

  1. Add your bot to the group.
  2. Send a message.
  3. Run a helper script like `tgi.py` or use Bot APIs to get the group ID.

- You need an OpenAI API key from [https://platform.openai.com](https://platform.openai.com).

---

### 4. Run the Bot

```bash
python main.py
```

This will:

- Search for new filings
- Download and analyze them
- Send summaries to your Telegram group

---

## 📁 File Structure

```
AtlantisBot/
├── main.py                  # Entry point
├── ai_api.py                # GPT analysis
├── telegram_sender.py       # Telegram integration
├── sec_scraper.py           # SEC search logic
├── sec_downloader.py        # Puppeteer download
├── config.yaml              # Your secrets + config
├── filings.yaml             # History of seen filings
├── filings/                 # Where HTML and GPT output goes
├── requirements.txt
└── README.md
```

---

## ⚠️ Notes

- Large SEC filings are chunked, summarized using a cheaper model, then summarized again by GPT-4.
- The bot avoids re-analyzing filings from today or yesterday.
- Telegram messages are skipped if the result is just `"X"` or empty.

---

## 🧠 License

MIT. Use responsibly.

❤️
