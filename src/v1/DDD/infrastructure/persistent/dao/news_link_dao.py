"""NewsLink 数据访问对象"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert

from v1.DDD.infrastructure.persistent.models import NewsLinkModel


# TODO：后面再看看这里都是简单实现
class NewsLinkDAO:
    """
    NewsLink 数据访问对象（无状态）

    设计说明：
    - 不持有 session，每个方法接受 session 参数
    - 可以在 Repository 中复用同一个实例
    - 纯粹的数据库操作封装
    """

    async def bulk_insert_ignore(self, session: AsyncSession, records: list[dict]) -> int:
        """
        批量插入（忽略重复）

        Args:
            session: 数据库会话
            records: 待插入的记录列表

        Returns:
            成功插入的数量
        """
        if not records:
            return 0

        stmt = insert(NewsLinkModel).values(records)
        # ON DUPLICATE KEY UPDATE：遇到重复的 url 时，不做任何更新（相当于 IGNORE）
        stmt = stmt.on_duplicate_key_update(url=stmt.inserted.url)

        result = await session.execute(stmt)
        return result.rowcount

    async def check_urls_exist(self, session: AsyncSession, urls: list[str]) -> set[str]:
        """
        批量查询 URL 是否存在

        Args:
            session: 数据库会话
            urls: URL 列表

        Returns:
            已存在的 URL 集合
        """
        if not urls:
            return set()

        stmt = select(NewsLinkModel.url).where(NewsLinkModel.url.in_(urls))
        result = await session.execute(stmt)
        return {row[0] for row in result.fetchall()}
