
# 搜索下，文档里还有一些注释，不过直接让AI解释更快

import httpx
from tenacity import stop_after_attempt, wait_fixed, retry_if_exception_type, retry

from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.http.RequestConfig import RequestConfig
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.http.Response import Response


class HttpAdapter:
    """
    HTTP 请求适配器，封装 httpx。

    职责单一：只负责"发请求"这一件事。
    上层（CrawlNode）只需传入填充好的 RequestConfig，不需要感知 httpx 细节。
    重试逻辑由 tenacity 在内部处理，对上层透明。
    """

    def send(self, request_config: RequestConfig) -> Response:
        """对外唯一入口，上层统一调用此方法。"""
        return self._send_with_retry(request_config)

    def _send_with_retry(self, rc: RequestConfig) -> Response:
        """
        动态构建重试装饰器后执行请求。

        为什么在方法内部定义装饰器而不是类级别？
        因为 max_retries / retry_delay 来自 RequestConfig，
        不同新闻源可以有不同的重试策略，必须运行时才能确定。
        """

        @retry(
            # 最多尝试 max_retries 次（含第一次）
            stop=stop_after_attempt(rc.max_retries),
            # 每次重试前等待固定秒数
            wait=wait_fixed(rc.retry_delay),
            # 只对网络层异常重试；4xx/5xx 由 raise_for_status() 抛出
            # HTTPStatusError 不在此列，避免对服务端错误无意义重试
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
            # 重试次数耗尽后，将最后一次异常原样抛出，而非包装成 RetryError
            reraise=True,
        )
        def _do_send() -> Response:
            return self._execute(rc)

        return _do_send()

    @staticmethod
    def _execute(rc: RequestConfig) -> Response:
        """
        真正执行单次 HTTP 请求。

        使用 with 语句管理 httpx.Client 生命周期，
        每次请求结束后自动关闭连接，不复用连接池。
        若需要性能优化，可改为在外部维护一个长生命周期的 Client。
        """

        # RequestConfig.auth 是 tuple[str, str] | None（HTTP Basic Auth）
        # httpx 要求传入原生 tuple，dataclass 里存的已经是 tuple，直接用即可
        # 显式转换是为了防止子类传入 list 等其他序列类型
        auth = tuple(rc.auth) if rc.auth else None

        with httpx.Client(
            verify=rc.verify_ssl,           # False 可跳过 SSL 证书校验（内网/自签名场景）
            follow_redirects=rc.allow_redirects,
            proxy=rc.proxies,               # httpx >= 0.28 用 proxy（单个代理地址字符串）
            timeout=rc.timeout,
        ) as client:
            resp = client.request(
                method=rc.method,
                url=rc.url,                 # 经 build_request 填充后的最终 URL
                headers=rc.headers,         # bearer token 已在 build_request 时注入
                cookies=rc.cookies,
                params=rc.params or None,   # 空 dict 传 None，避免 URL 带多余 ?
                json=rc.json_body,          # Content-Type: application/json
                data=rc.form_data,          # Content-Type: application/x-www-form-urlencoded
                auth=auth,                  # HTTP Basic Auth，与 bearer token 二选一
            )
            # 4xx / 5xx 时抛出 httpx.HTTPStatusError，不会触发上层重试
            resp.raise_for_status()

        return Response(
            status_code=resp.status_code,
            text=resp.text,
            headers=dict(resp.headers),
            url=str(resp.url),              # 记录实际请求的 URL（重定向后可能与入参不同）
        )
