from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    import pyodbc
except ImportError:  # pragma: no cover
    pyodbc = None


PREFERRED_SQL_SERVER_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Club Python API", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    db_driver: str = Field(default="ODBC Driver 17 for SQL Server", alias="DB_DRIVER")
    db_server: str = Field(default=r"localhost\MAY1", alias="DB_SERVER")
    db_name: str = Field(default="UmaClubKPI", alias="DB_NAME")
    db_trusted_connection: str = Field(default="yes", alias="DB_TRUSTED_CONNECTION")
    db_encrypt: str = Field(default="no", alias="DB_ENCRYPT")
    db_trust_server_certificate: str = Field(default="yes", alias="DB_TRUST_SERVER_CERTIFICATE")

    club_id: str = Field(default="508865447", alias="CLUB_ID")
    uma_moe_base_url: str = Field(default="https://uma.moe", alias="UMA_MOE_BASE_URL")
    uma_moe_text_proxy_url: str = Field(
        default="https://r.jina.ai/http://uma.moe",
        alias="UMA_MOE_TEXT_PROXY_URL",
    )

    sync_enabled: bool = Field(default=True, alias="SYNC_ENABLED")
    sync_hour: int = Field(default=0, alias="SYNC_HOUR")
    sync_minute: int = Field(default=5, alias="SYNC_MINUTE")
    sync_timezone: str = Field(default="Asia/Saigon", alias="SYNC_TIMEZONE")
    default_requested_by: str = Field(default="system", alias="DEFAULT_REQUESTED_BY")

    @property
    def effective_db_driver(self) -> str:
        configured = self.db_driver.strip()
        if pyodbc is None:
            return configured

        installed = set(pyodbc.drivers())
        if configured in installed:
            return configured

        for candidate in PREFERRED_SQL_SERVER_DRIVERS:
            if candidate in installed:
                return candidate

        return configured

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            if self.database_url.startswith("postgresql://"):
                return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
            return self.database_url

        connection_string = (
            f"DRIVER={{{self.effective_db_driver}}};"
            f"SERVER={self.db_server};"
            f"DATABASE={self.db_name};"
            f"Trusted_Connection={self.db_trusted_connection};"
            f"Encrypt={self.db_encrypt};"
            f"TrustServerCertificate={self.db_trust_server_certificate};"
        )
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
