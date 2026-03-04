"""
使用示例：以某新闻源为例
场景：一级类别 [tech, finance]，二级类别依赖一级，每个二级类别下按页码翻页
"""
from news_crawler.layer import DependentLayer, EnumerableLayer, SequentialLayer
from news_crawler.source_config import ParseConfig, RequestConfig, SourceConfig

# 构造 Layer 链（从内向外，叶子层先创建）
page_layer = SequentialLayer(
    key="page",
    start=1,
    step=1,
    prune_exist_ratio=0.8,
)

cat2_layer = DependentLayer(
    key="cat2",
    parent_key="cat1",
    mapping={
        "tech":    ["ai", "mobile"],
        "finance": ["stock", "crypto"],
    },
    next_layer=page_layer,
)

cat1_layer = EnumerableLayer(
    key="cat1",
    values=["tech", "finance"],
    next_layer=cat2_layer,
)

# 组装 SourceConfig
config = SourceConfig(
    source_id="example_news",
    root_layer=cat1_layer,
    request_config=RequestConfig(
        url_template="https://example.com/{cat1}/{cat2}?page={page}",
        method="GET",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    ),
    parse_config=ParseConfig(
        type="css",
        rule="a.news-title",
        attr="href",
    ),
)

# 使用
# from news_crawler.http_adapter import HttpAdapter
# from news_crawler.db_checker import DbChecker
# from news_crawler.source_crawler import SourceCrawler
#
# crawler = SourceCrawler(config, HttpAdapter(), DbChecker())
#
# # 首次全量
# result = crawler.crawl()
#
# # 断点续跑（传入上次的 last_checkpoint）
# result = crawler.crawl(checkpoint=last_checkpoint)
#
# print(result.new_links)
# print(result.total_requests)
