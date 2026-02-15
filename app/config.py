"""Configuration and environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Configuration
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# OpenAI Configuration
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")

# Timezone Configuration
DEFAULT_TZ = os.environ.get("DEFAULT_TZ", "Asia/Kolkata")
