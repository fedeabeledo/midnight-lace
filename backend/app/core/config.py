from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://midnightlace:midnightlace@localhost:5432/midnightlace"
    # TODO: Cambiar esto por variables de entorno para mayor seguridad
    jwt_secret: str = "SECRETO_ULTRA_SEGURO"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
