import os
from dotenv import load_dotenv

load_dotenv()

HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

MODEL_DIR = os.getenv("MODELS_DIR", "models/ru/diarization")

if not HUGGINGFACE_TOKEN:
    raise ValueError("Ошибка: HUGGINGFACE_TOKEN не найден в .env файле!")
