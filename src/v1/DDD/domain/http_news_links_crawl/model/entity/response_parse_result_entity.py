from dataclasses import dataclass, field

from v1.DDD.domain.http_news_links_crawl.model.valobj.response_parse_result_status_vo import ResponseParseResultStatusVO


@dataclass
class ResponseParseResultEntity:
    """
    新闻链接爬虫一次请求的响应进行解析后的直接结果

    职责边界：
        仅仅是对HTTP响应最直接的一次处理，取出新闻网页中所有想要的结果：这里主要就是具体新闻的url
        其他东西都不负责
    """

    status: ResponseParseResultStatusVO
    # 新闻链接列表
    urls: list[str] = field(default_factory=list)


    # 后续会根据需要添加字段
    #   ？ 分页控制：是否有下一页，感觉不一定需要
    #   ？ 错误诊断信息
    # 非致命的单条解析错误，供日志用，不阻断流程
    errors: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        """本页解析出的有效 URL 数为 0。"""
        return len(self.urls) == 0

