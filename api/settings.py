# backend/settings.py
import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):   
    MODEL_DIR: str = Field(
        ..., description="Ruta al directorio donde está exportado el modelo"
    )

    
    TWILIO_ACCOUNT_SID: str = Field(..., env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str  = Field(..., env="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_FROM: str = Field(..., env="TWILIO_WHATSAPP_FROM")
    TWILIO_WHATSAPP_TO: str   = Field(..., env="TWILIO_WHATSAPP_TO")

   
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., env="SUPABASE_KEY")

    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


tools_settings = Settings()