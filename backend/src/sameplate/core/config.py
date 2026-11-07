from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    debug: bool = False

    postgres_host: str = Field(min_length=1)
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_user: str = Field(min_length=1)
    postgres_password: SecretStr
    postgres_db: str = Field(min_length=1)
