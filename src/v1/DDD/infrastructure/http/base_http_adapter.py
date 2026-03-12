"""
HTTP 适配器抽象基类

职责：
  定义 HTTP 适配器的统一接口，所有具体实现必须遵循此契约。

设计原则：
  - 依赖倒置：上层依赖抽象而非具体实现
  - 开闭原则：可扩展新的 HTTP 库实现，无需修改上层代码
"""

from abc import ABC, abstractmethod

from v1.DDD.infrastructure.http.request_parameter import RequestParameter
from v1.DDD.infrastructure.http.response import Response


class BaseHttpAdapter(ABC):
    """
    HTTP 适配器抽象基类

    所有 HTTP 适配器（httpx、curl_cffi、requests 等）都必须实现此接口。

    生命周期：
        适配器实例在整个生命周期内复用同一连接池。
        使用完毕后必须调用 close()，或使用 async with 管理。

        # 推荐写法
        async with SomeHttpAdapter() as adapter:
            response = await adapter.send(request_params)
    """

    @abstractmethod
    async def send(self, request_config: RequestParameter) -> Response:
        """
        发送 HTTP 请求

        Args:
            request_config: 请求参数配置

        Returns:
            Response: 统一的响应对象

        Raises:
            HttpRequestError: 网络层错误（超时、连接失败），可重试
            HttpStatusError: HTTP 状态码错误（4xx/5xx）
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        释放连接池资源

        程序退出或 Adapter 不再使用时调用。
        """
        pass

    # ------------------------------------------------------------------
    # 上下文管理器支持（默认实现）
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "BaseHttpAdapter":
        """进入 async with 上下文"""
        return self

    async def __aexit__(self, *_) -> None:
        """退出 async with 上下文，自动释放资源"""
        await self.close()
