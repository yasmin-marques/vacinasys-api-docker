from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não foi definida no arquivo .env")

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

# tenta usar app/uploads primeiro
upload_inside_app = APP_DIR / "uploads"

# se não existir, usa uploads na raiz
if upload_inside_app.exists():
    UPLOAD_DIR = upload_inside_app
else:
    UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)