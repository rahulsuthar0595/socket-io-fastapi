from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class ConfigSetting(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DEBUG: bool
    SOCKET_IO_AUTH_ENABLED: bool = False
    SOCKET_IO_ADMIN_USERNAME: str = ""
    SOCKET_IO_ADMIN_PASSWORD: str = ""
    SOCKET_IO_SERVER_ID: str

    REDIS_HOST: str
    REDIS_PORT : int

    MONGO_DB_HOST: str
    MONGO_DB_PORT: int
    MONGO_DB_NAME: str


@lru_cache
def get_settings():
    return ConfigSetting()


settings = get_settings()