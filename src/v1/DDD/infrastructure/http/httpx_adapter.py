"""
这个只管发HTTP，其他一律不管


让AI帮我改造的
    1. 连接复用：with httpx.Client() 在每次请求里新建，完全没有复用
    2. 异常语义化：httpx 异常直接透传到上层
    3. 可观测性：没有任何日志


"""


import logging
import time

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
    wait_fixed,
)

from v1.DDD.infrastructure.http.base_http_adapter import BaseHttpAdapter
from v1.DDD.infrastructure.http.request_parameter import RequestParameter
from v1.DDD.infrastructure.http.response import Response

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 业务异常：上层只需感知这两个，不需要 import httpx
# ---------------------------------------------------------------------------

class HttpRequestError(Exception):
    """网络层错误（超时、连接失败），可重试。"""

    def __init__(self, url: str, cause: Exception) -> None:
        super().__init__(f"Network error on {url}: {cause}")
        self.url = url
        self.cause = cause


class HttpStatusError(Exception):
    """
    HTTP 状态码错误（4xx / 5xx）。
    4xx 不可重试（请求本身有问题），5xx 由 tenacity 按策略处理。
    """

    def __init__(self, url: str, status_code: int) -> None:
        super().__init__(f"HTTP {status_code}: {url}")
        self.url = url
        self.status_code = status_code


# ---------------------------------------------------------------------------
# HttpxAdapter
# ---------------------------------------------------------------------------

class HttpxAdapter(BaseHttpAdapter):
    """
    httpx HTTP 请求适配器，封装 httpx。

    职责单一：只负责"发请求"这一件事。
    上层（CrawlNode）只需传入填充好的 RequestParameter，不需要感知 httpx 细节。

    生命周期：
        AsyncClient 在 __init__ 创建，整个 Adapter 生命周期内复用同一连接池。
        使用完毕后必须调用 close()，或使用 async with 管理。

        # 推荐写法
        async with HttpxAdapter() as adapter:
            response = await adapter.send(request_params)
    """

    def __init__(
        self,
        timeout: float = 30.0,
        connect_timeout: float = 5.0,
        read_timeout: float = 15.0,
        write_timeout: float = 5.0,
        pool_timeout: float = 5.0,
        max_connections: int = 20,
        max_keepalive_connections: int = 10,
    ) -> None:
        """
        初始化 HTTP 适配器

        Args:
            timeout: 默认总超时时间（秒）
            connect_timeout: 连接超时时间（秒）
            read_timeout: 读取超时时间（秒）
            write_timeout: 写入超时时间（秒）
            pool_timeout: 连接池获取超时时间（秒）
            max_connections: 最大连接数
            max_keepalive_connections: 最大保持连接数
        """
        # AsyncClient 在此处创建一次，后续所有 send() 共用同一连接池。
        # 连接复用避免了每次请求都重新 TCP/TLS 握手的开销。
        self._client = httpx.AsyncClient(
            # 连接池上限：防止对同一站点开太多并发连接，被对方封 IP
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
            ),
            # 全局默认超时，可被 RequestParameter.timeout 覆盖
            timeout=httpx.Timeout(
                timeout,
                connect=connect_timeout,
                read=read_timeout,
                write=write_timeout,
                pool=pool_timeout,
            ),
        )

    async def close(self) -> None:
        """释放连接池，程序退出或 Adapter 不再使用时调用。"""
        await self._client.aclose()

    async def __aenter__(self) -> "HttpxAdapter":
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

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
            # 原代码用 wait_fixed，这里改为指数退避 + jitter：
            # 防止多个并发请求在同一时刻集体重试，形成"重试风暴"打垮对方服务。
            # 如果 RequestParameter 明确指定了固定延迟，可换回 wait_fixed(rc.retry_delay)。
            wait=wait_exponential_jitter(initial=request_config.retry_delay, max=30, jitter=1),
            # 只对网络层异常重试；HttpStatusError 由上层决定，不在重试范围内
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
        真正执行单次 HTTP 请求，并将 httpx 异常翻译为业务异常。
        """
        auth = tuple(request_config.auth) if request_config.auth else None
        start = time.monotonic()

        try:
            resp = await self._client.request(
                method=request_config.method,
                url=request_config.url,
                headers=request_config.headers,
                params=request_config.params or None,
                json=request_config.json_body,
                data=request_config.form_data,
                auth=auth,
                timeout=request_config.timeout,                    # 单次请求可覆盖全局超时
                follow_redirects=request_config.allow_redirects,
            )
        except httpx.TimeoutException as exc:
            # --- 异常语义化：超时 → HttpRequestError，上层不感知 httpx ---
            logger.warning("Timeout: %s", request_config.url)
            raise HttpRequestError(url=request_config.url, cause=exc) from exc

        except httpx.NetworkError as exc:
            # --- 异常语义化：网络错误 → HttpRequestError ---
            logger.warning("Network error: %s — %s", request_config.url, exc)
            raise HttpRequestError(url=request_config.url, cause=exc) from exc

        elapsed = time.monotonic() - start

        # 4xx / 5xx 统一翻译为 HttpStatusError
        if resp.is_error:
            logger.warning(
                "HTTP %d [%.2fs]: %s",
                resp.status_code, elapsed, request_config.url,
            )
            raise HttpStatusError(url=request_config.url, status_code=resp.status_code)

        # --- 可观测性：每次成功请求记录状态码 + 耗时 ---
        logger.info(
            "HTTP %d [%.2fs]: %s",
            resp.status_code, elapsed, request_config.url,
        )

        return Response(
            status_code=resp.status_code,
            text=resp.text,
            headers=dict(resp.headers),
            url=str(resp.url),
        )