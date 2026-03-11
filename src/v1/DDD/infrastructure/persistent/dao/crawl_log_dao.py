"""CrawlLog 数据访问对象"""

from sqlalchemy.ext.asyncio import AsyncSession

from v1.DDD.infrastructure.persistent.models.crawl_log import CrawlLogModel


class CrawlLogDAO:
    """
    CrawlLog 数据访问对象（无状态）

    设计说明：
    - 不持有 session，每个方法接受 session 参数
    - 可以在 Repository 中复用同一个实例
    - 纯粹的数据库操作封装
    """

    async def insert(self, session: AsyncSession, record: dict) -> int:
        """
        插入单条爬取日志记录

        Args:
            session: 数据库会话
            record: 待插入的记录字典

        Returns:
            插入记录的主键 ID
        """
        model = CrawlLogModel(**record)
        session.add(model)
        await session.flush()  # 获取自增 ID
        return model.id
