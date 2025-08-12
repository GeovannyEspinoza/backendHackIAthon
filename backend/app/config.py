from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
TMP_DIR = DATA_DIR / "tmp"
SAMPLES_DIR = DATA_DIR / "samples"

# Carga .env
load_dotenv(BASE_DIR / ".env")

# Flags
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "1") == "1"
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "25"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")