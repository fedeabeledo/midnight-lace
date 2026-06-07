from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://midnightlace:midnightlace@localhost:5432/midnightlace"
    jwt_secret: str = "SECRETO_ULTRA_SEGURO"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    api_key: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@midnightlace.com"
    smtp_from_name: str = "Midnight Lace"
    smtp_use_tls: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
