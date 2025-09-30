from google import genai
from google.genai import types
import time, random
from typing import List, Optional
from .config import config

client = genai.Client(api_key=config.google_api_key)
TEXT_MODEL = "gemini-2.5-flash"
EMBED_MODEL = "gemini-embedding-001"

def embed_text(texts: List[str]) -> List[List[float]]:
    backoffs = [0.5, 1, 2]
    for i in range(len(backoffs) + 1):
        try:
            response = client.models.embed_content(
                model=EMBED_MODEL,
                contents=texts
            )
            if response.embeddings is None:
                return []
            return [embedding.values for embedding in response.embeddings if embedding.values is not None]
        except Exception as e:
            if i == len(backoffs):
                raise e
            time.sleep(backoffs[i] + random.uniform(0, 0.25))
    return []

def generate_text(prompt: str, system: str = "", temperature: Optional[float] = None) -> str:
    t = config.gen_temperature if temperature is None else temperature
    backoffs = [0.5, 1, 2]
    for i in range(len(backoffs) + 1):
        try:
            # model = client.models.GenerativeModel(
            #     TEXT_MODEL,
            #     system_instruction=system or None,
            # )

            response = client.models.generate_content(
                model=TEXT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=t,
                    top_p=config.gen_top_p,
                    top_k=config.gen_top_k,
                )
            )
            return response.text.strip() if response.text else ""
        except Exception as e:
            if i == len(backoffs):
                raise e
            time.sleep(backoffs[i] + random.uniform(0, 0.25))

    return ""