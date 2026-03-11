"""CrawlLog 映射器：CrawlNodeResultEntity -> 数据库记录"""

from datetime import datetime

from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import CrawlNodeResultEntity
from v1.DDD.domain.http_news_links_crawl.model.valobj.node_status_vo import NodeStatusVO


class CrawlLogMapper:
    """CrawlNodeResultEntity 与数据库记录之间的映射器"""

    @staticmethod
    def result_to_insert_record(
        resource_id: str,
        result: CrawlNodeResultEntity,
        started_at: datetime,
        finished_at: datetime,
    ) -> dict:
        """
        将爬取结果转换为数据库插入记录

        Args:
            resource_id: 新闻源唯一标识
            result: 顶层爬取结果（通常是 COMPOSITE 节点）
            started_at: 爬取开始时间
            finished_at: 爬取结束时间

        Returns:
            可直接用于数据库插入的字典
        """
        # 1. 映射爬取状态
        crawl_status = CrawlLogMapper._map_crawl_status(result.status)

        # 2. 提取统计信息
        total_categories = result.total_requests
        success_categories = result.success_requests
        failed_categories = result.failed_requests
        total_links_found = result.total_links_found
        total_links_new = result.total_links_new

        # 3. 构建详细信息 JSON
        details = CrawlLogMapper._build_details_json(result)

        # 4. 组装记录
        return {
            "resource_id": resource_id,
            "crawl_status": crawl_status,
            "total_categories": total_categories,
            "success_categories": success_categories,
            "failed_categories": failed_categories,
            "total_links_found": total_links_found,
            "total_links_new": total_links_new,
            "details": details,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_ms": result.duration_ms,
        }

    @staticmethod
    def _map_crawl_status(status: NodeStatusVO) -> str:
        """
        将 NodeStatus 映射为数据库的 crawl_status 字符串

        Args:
            status: 节点状态

        Returns:
            "success" / "partial" / "failed"
        """
        if status == NodeStatusVO.SUCCESS:
            return "success"
        elif status == NodeStatusVO.PARTIAL_SUCCESS:
            return "partial"
        else:
            return "failed"

    @staticmethod
    def _build_details_json(result: CrawlNodeResultEntity) -> dict:
        """
        构建 details JSON 字段

        Args:
            result: 爬取结果（组合节点）

        Returns:
            包含 categories 数组的字典

        格式示例：
        {
            "categories": [
                {
                    "category": "politics",
                    "params": {"category": "politics", "page": 1},
                    "status": "success",
                    "links_found": 10,
                    "links_new": 5,
                    "duration_ms": 1234
                },
                {
                    "category": "tech",
                    "params": {"category": "tech", "page": 1},
                    "status": "http_error",
                    "http_code": 500,
                    "error": "Internal Server Error",
                    "duration_ms": 567
                }
            ]
        }
        """
        # 收集所有叶子节点
        leaf_nodes = result.collect_leaf_nodes()

        categories = []
        for leaf in leaf_nodes:
            category_detail = {}

            # 基本信息（从 execution 获取）
            if leaf.execution:
                exec_phase = leaf.execution

                # 请求参数
                category_detail["params"] = exec_phase.request_params

                # 提取 category 字段（如果存在）
                if "category" in exec_phase.request_params:
                    category_detail["category"] = exec_phase.request_params["category"]
                else:
                    # 如果没有 category，使用完整参数作为标识
                    category_detail["category"] = str(exec_phase.request_params)

                # 状态
                category_detail["status"] = leaf.status.value

                # 链接统计
                category_detail["links_found"] = exec_phase.links_found_count
                category_detail["links_new"] = exec_phase.links_new_count

                # HTTP 状态码（如果存在）
                if exec_phase.response_status_code is not None:
                    category_detail["http_code"] = exec_phase.response_status_code

                # 解析错误（如果存在）
                if exec_phase.parse_error:
                    category_detail["error"] = exec_phase.parse_error

                # 耗时
                category_detail["duration_ms"] = leaf.duration_ms

                categories.append(category_detail)

        return {"categories": categories}
