from typing import Any


class Response:
    """HTTP 响应封装"""
    def __init__(self, status_code: int, text: str = "", json_data: Any = None):
        self.status_code = status_code
        self.text = text
        self._json = json_data

    def json(self) -> Any:
        return self._json


class HttpAdapter:
    """
    唯一真正发出 HTTP 请求的地方。
    处理重试、超时、异常封装，不关心业务逻辑。
    """

    def send(self, request_params: dict[str, Any]) -> Response:
        # TODO: 实现实际的 HTTP 请求
        # request_params 包含 url / method / headers / timeout 等
        raise NotImplementedError
