from news_crawler.models import CheckResult


class DbChecker:
    """
    数据库存在性检查。
    批量查询哪些链接已存在，减少 DB 往返。
    """

    def check_batch(self, links: list[str]) -> CheckResult:
        # TODO: 实现实际的数据库批量查询
        raise NotImplementedError
