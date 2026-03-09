"""MySQL 数据库配置"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class MySQLSettings(BaseSettings):
    """MySQL 数据库配置（从环境变量加载）"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # 连接配置
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = "123456"
    database: str = "news_crawl"

    # 连接池配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    # 开发配置
    echo: bool = False

    @property
    def url(self) -> str:
        """构造数据库连接 URL"""
        return f"mysql+asyncmy://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
