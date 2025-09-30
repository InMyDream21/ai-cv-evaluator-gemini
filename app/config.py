from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class Config(BaseModel):
    google_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gen_temperature: float = float(os.getenv("GEN_TEMPERATURE", 0.7))
    db_path: str = os.getenv("DB_PATH", "local.db")
    gen_top_p: float = float(os.getenv("GEN_TOP_P", 0.9))
    gen_top_k: int = int(os.getenv("GEN_TOP_K", 50))

config = Config()