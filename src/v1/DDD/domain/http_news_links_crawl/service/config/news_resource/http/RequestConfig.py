# 自定义HTTP请求的必要参数



# news_crawler/request_config.py

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequestConfig:
    # ── 基础 ──────────────────────────────────────────────────────
    url: str                               # 填充后即为最终 URL
    method: str = "GET"

    # ── 请求头 / Cookie ───────────────────────────────────────────
    headers: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)

    # ── 参数 / 请求体 ─────────────────────────────────────────────
    params: dict[str, Any] = field(default_factory=dict)   # 值支持 {占位符}
    json_body: dict[str, Any] | None = None
    form_data: dict[str, str] | None = None

    # ── 认证 ──────────────────────────────────────────────────────
    auth: tuple[str, str] | None = None
    bearer_token: str | None = None

    # ── 连接控制 ──────────────────────────────────────────────────
    timeout: float = 10.0
    allow_redirects: bool = True
    verify_ssl: bool = True
    proxies: dict[str, str] | None = None

    # ── 重试 ──────────────────────────────────────────────────────
    max_retries: int = 3
    retry_delay: float = 1.0




