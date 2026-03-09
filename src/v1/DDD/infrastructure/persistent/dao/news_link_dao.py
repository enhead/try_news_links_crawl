"""NewsLink 数据访问对象"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert

from ..models.news_link import NewsLinkModel


# TODO：后面再看看这里都是简单实现
class NewsLinkDAO:
    """NewsLink 数据访问对象（纯数据库操作）"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_insert_ignore(self, records: list[dict]) -> int:
        """
        批量插入（忽略重复）

        Args:
            records: 待插入的记录列表

        Returns:
            成功插入的数量
        """
        if not records:
            return 0

        stmt = insert(NewsLinkModel).values(records)
        stmt = stmt.on_duplicate_key_update(updated_at=stmt.inserted.updated_at)

        result = await self.session.execute(stmt)
        return result.rowcount

    async def check_urls_exist(self, urls: list[str]) -> set[str]:
        """
        批量查询 URL 是否存在

        Args:
            urls: URL 列表

        Returns:
            已存在的 URL 集合
        """
        if not urls:
            return set()

        stmt = select(NewsLinkModel.url).where(NewsLinkModel.url.in_(urls))
        result = await self.session.execute(stmt)
        return {row[0] for row in result.fetchall()}
