from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(ROOT / ".env", ROOT / "backend" / ".env"), extra="ignore")

    # Infra
    database_url: str = "postgresql+psycopg://aarogya:aarogya@localhost:5433/aarogya"
    redis_url: str = "redis://localhost:6380/0"
    qdrant_url: str = "http://localhost:6333"
    storage_dir: str = str(ROOT / "backend" / "storage")
    public_base_url: str = "http://localhost:8000"  # ngrok https URL so Agora can reach the LLM endpoint
    timezone: str = "Asia/Kolkata"

    # LLM (any OpenAI-compatible endpoint: OpenAI, Gemini, Groq, OpenRouter...)
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0.2
    llm_fallback_models: str = "gemini-3.1-flash-lite,gemini-flash-lite-latest"
    llm_thinking: str = "minimal"  # Gemini 3+: minimal | low | medium | high

    # Agora
    agora_app_id: str = ""
    agora_app_certificate: str = ""
    agora_customer_id: str = ""
    agora_customer_secret: str = ""
    agora_api_base: str = "https://api.agora.io/api/conversational-ai-agent/v2/projects"
    agora_agent_uid: int = 1000
    agora_user_uid: int = 2000
    # JSON overrides for vendor blocks (paste exact blocks from Agora docs if defaults need changes)
    agora_asr_json: str = '{"language": "hi-IN"}'
    agora_tts_json: str = ""
    agora_llm_shared_secret: str = "aarogya-internal-llm-key"

    # Murf Falcon
    murf_api_key: str = ""
    murf_voice_id: str = "hi-IN-shweta"
    murf_model: str = "FALCON"
    murf_locale: str = "hi-IN"

    # Behaviour
    response_script: str = "devanagari"  # devanagari | latin  (how Hindi is written for TTS)


@lru_cache
def get_settings() -> Settings:
    return Settings()
