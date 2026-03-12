"""
curl_cffi HTTP 适配器实现

职责：
  使用 curl_cffi 库发送 HTTP 请求，通过 impersonate 参数模拟真实浏览器 TLS 指纹。

优势：
  - 绕过 Cloudflare、DataDome 等反爬虫系统
  - 支持 HTTP/2、HTTP/3
  - 更真实的浏览器特征

设计原则：
  - 连接复用：AsyncSession 在整个生命周期内复用
  - 异常语义化：curl_cffi 异常翻译为统一的业务异常
  - 可观测性：记录请求日志
"""

import logging
import time

from curl_cffi.requests import AsyncSession, RequestsError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from v1.DDD.infrastructure.http.base_http_adapter import BaseHttpAdapter
from v1.DDD.infrastructure.http.request_parameter import RequestParameter
from v1.DDD.infrastructure.http.response import Response
# 复用 httpx_adapter 中定义的统一异常
from v1.DDD.infrastructure.http.httpx_adapter import (
    HttpRequestError,
    HttpStatusError,
)

logger = logging.getLogger(__name__)


class CurlCffiAdapter(BaseHttpAdapter):
    """
    curl_cffi HTTP 适配器实现

    特性：
      - 使用 impersonate 参数模拟真实浏览器（Chrome、Safari 等）
      - 支持 HTTP/2 和 HTTP/3
      - 绕过常见的反爬虫检测

    生命周期：
        AsyncSession 在 __init__ 创建，整个 Adapter 生命周期内复用同一连接池。
        使用完毕后必须调用 close()，或使用 async with 管理。

        # 推荐写法
        async with CurlCffiAdapter(impersonate="chrome120") as adapter:
            response = await adapter.send(request_params)
    """

    def __init__(
        self,
        impersonate: str = "chrome120",
        timeout: float = 30.0,
        connect_timeout: float = 5.0,
        read_timeout: float = 15.0,
        max_connections: int = 20,
    ) -> None:
        """
        初始化 curl_cffi 适配器

        Args:
            impersonate: 模拟的浏览器类型
                - "chrome120", "chrome110", "chrome99"
                - "safari15_5", "safari15_3"
                - "edge101", "edge99"
            timeout: 默认总超时时间（秒）
            connect_timeout: 连接超时时间（秒）
            read_timeout: 读取超时时间（秒）
            max_connections: 最大连接数
        """
        self._impersonate = impersonate
        self._timeout = timeout
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._max_connections = max_connections

        # 创建异步会话（连接复用）
        self._session = AsyncSession(impersonate=impersonate)

    async def close(self) -> None:
        """释放连接池，程序退出或 Adapter 不再使用时调用"""
        await self._session.close()

    # ------------------------------------------------------------------
    # 对外唯一入口
    # ------------------------------------------------------------------

    async def send(self, request_config: RequestParameter) -> Response:
        """
        上层统一调用此方法。
        内部重试对上层透明，失败时抛出 HttpRequestError 或 HttpStatusError。
        """
        return await self._send_with_retry(request_config)

    # ------------------------------------------------------------------
    # 重试包装
    # ------------------------------------------------------------------

    async def _send_with_retry(self, request_config: RequestParameter) -> Response:
        """
        动态构建重试装饰器后执行请求。

        为什么在方法内部定义装饰器而不是类级别？
        因为 max_retries / retry_delay 来自 RequestParameter，
        不同新闻源可以有不同的重试策略，必须运行时才能确定。
        """

        @retry(
            stop=stop_after_attempt(request_config.max_retries),
            wait=wait_exponential_jitter(
                initial=request_config.retry_delay, max=30, jitter=1
            ),
            # 只对网络层异常重试；HttpStatusError 由上层决定
            retry=retry_if_exception_type(HttpRequestError),
            reraise=True,
        )
        async def _do_send() -> Response:
            return await self._execute(request_config)

        return await _do_send()

    # ------------------------------------------------------------------
    # 单次请求执行
    # ------------------------------------------------------------------

    async def _execute(self, request_config: RequestParameter) -> Response:
        """
        真正执行单次 HTTP 请求，并将 curl_cffi 异常翻译为业务异常。
        """
        start = time.monotonic()

        try:
            # curl_cffi 的请求参数映射
            resp = await self._session.request(
                method=request_config.method,
                url=request_config.url,
                headers=request_config.headers,
                params=request_config.params,
                json=request_config.json_body,
                data=request_config.form_data,
                timeout=request_config.timeout or self._timeout,
                allow_redirects=request_config.allow_redirects,
            )

        except RequestsError as exc:
            # --- 异常语义化：curl_cffi 异常 → HttpRequestError ---
            # curl_cffi 的 RequestsError 包含超时、连接失败等所有网络错误
            logger.warning(
                "curl_cffi request error: %s — %s",
                request_config.url, exc,
            )
            raise HttpRequestError(url=request_config.url, cause=exc) from exc

        except Exception as exc:
            # 捕获其他未知异常
            logger.error(
                "Unexpected error in curl_cffi: %s — %s",
                request_config.url, exc,
            )
            raise HttpRequestError(url=request_config.url, cause=exc) from exc

        elapsed = time.monotonic() - start

        # 4xx / 5xx 统一翻译为 HttpStatusError
        if resp.status_code >= 400:
            logger.warning(
                "HTTP %d [%.2fs]: %s",
                resp.status_code, elapsed, request_config.url,
            )
            raise HttpStatusError(
                url=request_config.url, status_code=resp.status_code
            )

        # --- 可观测性：每次成功请求记录状态码 + 耗时 ---
        logger.info(
            "HTTP %d [%.2fs] [%s]: %s",
            resp.status_code, elapsed, self._impersonate, request_config.url,
        )

        return Response(
            status_code=resp.status_code,
            text=resp.text,
            headers=dict(resp.headers),
            url=str(resp.url),
        )
