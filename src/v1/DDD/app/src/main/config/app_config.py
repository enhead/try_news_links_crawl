"""
应用配置类

职责：
- 从 .env 文件加载配置
- 提供类型安全的配置访问
- 验证配置完整性
"""

from dataclasses import dataclass
from typing import Literal
import os
from pathlib import Path


@dataclass(frozen=True)
class DatabaseConfig:
    """数据库配置"""
    host: str
    port: int
    user: str
    password: str
    database: str
    pool_size: int
    pool_recycle: int
    echo: bool

    @property
    def url(self) -> str:
        """构建数据库连接 URL"""
        return (
            f"mysql+aiomysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass(frozen=True)
class HttpConfig:
    """HTTP 配置"""
    # 适配器选择
    default_adapter: str  # "httpx" 或 "curl_cffi"

    # curl_cffi 特有配置
    curl_cffi_impersonate: str  # "chrome120", "safari15_5", etc.

    # 通用配置（适用于所有适配器）
    timeout: float
    connect_timeout: float
    read_timeout: float
    write_timeout: float
    pool_timeout: float
    max_connections: int
    max_keepalive_connections: int


@dataclass(frozen=True)
class NewsSourceConfig:
    """新闻源配置"""
    module_paths: list[str]  # 要导入的新闻源模块路径列表


@dataclass(frozen=True)
class AppConfig:
    """应用配置"""
    env: Literal["development", "production", "test"]
    log_level: str

    database: DatabaseConfig
    http: HttpConfig
    news_source: NewsSourceConfig

    @staticmethod
    def _find_project_root(env_file: str = ".env") -> Path:
        """
        智能查找项目根目录

        查找策略（优先级从高到低）：
        1. 环境变量 PROJECT_ROOT
        2. 当前工作目录
        3. 向上搜索（从当前文件位置向上查找）
        4. 固定相对路径（兜底）

        Args:
            env_file: .env 文件名

        Returns:
            项目根目录路径
        """
        # 策略 1: 环境变量 PROJECT_ROOT
        project_root_env = os.getenv("PROJECT_ROOT")
        if project_root_env:
            project_root = Path(project_root_env)
            if (project_root / env_file).exists():
                return project_root

        # 策略 2: 当前工作目录
        cwd = Path.cwd()
        if (cwd / env_file).exists():
            return cwd

        # 策略 3: 向上搜索（从当前文件位置向上查找）
        current = Path(__file__).resolve().parent
        for _ in range(10):  # 最多向上搜索 10 层
            if (current / env_file).exists():
                return current
            if current.parent == current:  # 到达根目录
                break
            current = current.parent

        # 策略 4: 固定相对路径（兜底）
        # 文件位置：src/v1/DDD/app/src/main/config/app_config.py
        # 向上 8 级到达项目根目录
        fallback_root = Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent
        return fallback_root

    @classmethod
    def from_env(cls, env_file: str = ".env") -> "AppConfig":
        """
        从 .env 文件加载配置（智能查找项目根目录）

        查找策略（优先级从高到低）：
        1. 环境变量 PROJECT_ROOT 指定的路径
        2. 当前工作目录
        3. 向上搜索直到找到 .env 文件
        4. 相对于代码文件的固定层级（兜底）

        Args:
            env_file: .env 文件名（默认 ".env"）

        Returns:
            AppConfig 实例

        Raises:
            FileNotFoundError: .env 文件不存在
            ValueError: 配置项缺失或格式错误
        """
        from dotenv import load_dotenv

        # 查找项目根目录
        project_root = cls._find_project_root(env_file)
        env_path = project_root / env_file

        if not env_path.exists():
            raise FileNotFoundError(
                f".env 文件不存在: {env_path}\n"
                f"请复制 .env.example 为 .env 并修改配置\n"
                f"当前查找路径: {project_root}\n"
                f"提示: 可以设置环境变量 PROJECT_ROOT 来指定项目根目录"
            )

        load_dotenv(env_path)

        # 构建配置对象
        try:
            database = DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "3306")),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_DATABASE", "news_crawl"),
                pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
                pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            )

            http = HttpConfig(
                default_adapter=os.getenv("HTTP_DEFAULT_ADAPTER", "curl_cffi"),
                curl_cffi_impersonate=os.getenv("HTTP_CURL_CFFI_IMPERSONATE", "chrome120"),
                timeout=float(os.getenv("HTTP_TIMEOUT", "30")),
                connect_timeout=float(os.getenv("HTTP_CONNECT_TIMEOUT", "5")),
                read_timeout=float(os.getenv("HTTP_READ_TIMEOUT", "15")),
                write_timeout=float(os.getenv("HTTP_WRITE_TIMEOUT", "5")),
                pool_timeout=float(os.getenv("HTTP_POOL_TIMEOUT", "5")),
                max_connections=int(os.getenv("HTTP_MAX_CONNECTIONS", "20")),
                max_keepalive_connections=int(os.getenv("HTTP_MAX_KEEPALIVE_CONNECTIONS", "10")),
            )

            # 解析新闻源模块配置
            modules_str = os.getenv(
                "NEWS_SOURCE_MODULES",
                "v1.DDD.app.src.resource.news_source"  # 默认值
            )
            # 逗号分隔的字符串转为数组
            module_paths = [m.strip() for m in modules_str.split(",") if m.strip()]

            news_source = NewsSourceConfig(module_paths=module_paths)

            return cls(
                env=os.getenv("APP_ENV", "development"),
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                database=database,
                http=http,
                news_source=news_source,
            )
        except (ValueError, TypeError) as e:
            raise ValueError(f"配置格式错误: {e}")
