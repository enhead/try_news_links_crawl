"""
简单的数据库测试脚本

直接运行即可测试 Repository 功能：
python src/v1/DDD/app/test/http_news_links_crawl/simple_test.py
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy.dialects.mysql import insert

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from v1.DDD.infrastructure.config.mysql.settings import MySQLSettings
from v1.DDD.infrastructure.persistent.dao import NewsLinkDAO, NewsSourceDAO
from v1.DDD.infrastructure.persistent.models import NewsSourceModel
from v1.DDD.infrastructure.persistent.models.base import Base
from v1.DDD.infrastructure.persistent.repository.news_links_crawl_repository import NewsLinksCrawlRepository
from v1.DDD.domain.http_news_links_crawl.model.aggregate.news_link_batch_aggregate import NewsLinkBatchAggregate
from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import DiscoveredNewsLinkUrl
from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.domain.http_news_links_crawl.model.valobj import NewsSourceStatusVO


async def test_repository():
    """测试 Repository 功能"""

    print("=" * 60)
    print("开始测试 NewsLinksCrawlRepository")
    print("=" * 60)

    # 1. 创建数据库引擎
    settings = MySQLSettings()
    engine = create_async_engine(settings.url, echo=False)

    # 2. 创建会话
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        # 3. 创建 DAO 和 Repository
        news_source_dao = NewsSourceDAO(session)
        news_link_dao = NewsLinkDAO(session)
        repository = NewsLinksCrawlRepository(news_link_dao, news_source_dao)

        print("\n✅ 数据库连接成功")

        # ========== 测试 1：插入测试数据 ==========
        print("\n" + "=" * 60)
        print("测试 1：插入测试新闻源")
        print("=" * 60)

        # 如果存在会报错，这里稍微改一下
        # test_source = NewsSourceModel(
        #     resource_id="test_source_001",
        #     name="测试新闻源",
        #     domain="test.com",
        #     url="https://test.com",
        #     country="SG",
        #     language="en",
        #     status=0,
        # )
        # session.add(test_source)
        # await session.commit()
        # print("✅ 测试新闻源插入成功")

        # 存在重复：忽略；不存在：插入；不会有异常
        stmt = insert(NewsSourceModel).values(
            resource_id="test_source_001",
            name="测试新闻源",
            domain="test.com",
            url="https://test.com",
            country="SG",
            language="en",
            status=0,
        )

        stmt = stmt.on_duplicate_key_update(
            resource_id=stmt.inserted.resource_id
        )

        await session.execute(stmt)
        await session.commit()



        # ========== 测试 2：查询新闻源 ==========
        print("\n" + "=" * 60)
        print("测试 2：根据 resource_id 查询新闻源")
        print("=" * 60)

        result = await repository.get_source_by_resource_id("test_source_001")
        if result:
            print(f"✅ 查询成功：{result.name} ({result.resource_id})")
            print(f"   - 域名：{result.domain}")
            print(f"   - 国家：{result.country}")
            print(f"   - 状态：{result.status}")
        else:
            print("❌ 查询失败")

        # ========== 测试 3：批量保存链接 ==========
        print("\n" + "=" * 60)
        print("测试 3：批量保存新闻链接")
        print("=" * 60)

        metadata = NewsSourceMetadata(
            resource_id="test_source_001",
            name="测试新闻源",
            domain="test.com",
            url="https://test.com",
            country="SG",
            language="en",
            status=NewsSourceStatusVO.NORMAL,
        )

        links = [
            DiscoveredNewsLinkUrl(
                url="https://test.com/news/1",
                crawl_params={"page": 1},
                category="Politics",
            ),
            DiscoveredNewsLinkUrl(
                url="https://test.com/news/2",
                crawl_params={"page": 1},
                category="Technology",
            ),
        ]

        aggregate = NewsLinkBatchAggregate(metadata=metadata, links=links)
        save_result = await repository.save_batch(aggregate)

        print(f"✅ 保存成功：{save_result.saved_count} 条")
        if save_result.skipped_urls:
            print(f"   跳过重复：{len(save_result.skipped_urls)} 条")

        # ========== 测试 4：批量去重 ==========
        print("\n" + "=" * 60)
        print("测试 4：批量去重检查")
        print("=" * 60)

        # 添加一个新链接和一个已存在的链接
        new_links = [
            DiscoveredNewsLinkUrl(
                url="https://test.com/news/2",  # 已存在
                crawl_params={"page": 1},
                category="Technology",
            ),
            DiscoveredNewsLinkUrl(
                url="https://test.com/news/3",  # 新链接
                crawl_params={"page": 2},
                category="Sports",
            ),
        ]

        check_aggregate = NewsLinkBatchAggregate(metadata=metadata, links=new_links)
        filtered = await repository.check_exists_batch(check_aggregate)

        print(f"✅ 去重完成：")
        print(f"   - 检查数量：{len(new_links)}")
        print(f"   - 新链接数：{len(filtered.links)}")
        print(f"   - 新链接：{[link.url for link in filtered.links]}")

        # ========== 测试 5：查询所有活跃新闻源 ==========
        print("\n" + "=" * 60)
        print("测试 5：查询所有活跃新闻源")
        print("=" * 60)

        active_sources = await repository.get_all_active_sources()
        print(f"✅ 查询成功：找到 {len(active_sources)} 个活跃新闻源")
        for source in active_sources:
            print(f"   - {source.name} ({source.resource_id})")

        # ========== 清理测试数据 ==========
        print("\n" + "=" * 60)
        print("清理测试数据")
        print("=" * 60)

        await session.rollback()  # 回滚所有更改
        print("✅ 测试数据已回滚")

    await engine.dispose()

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_repository())
