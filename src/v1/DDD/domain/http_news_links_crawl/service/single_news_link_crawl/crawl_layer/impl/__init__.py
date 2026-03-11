"""
爬取层实现包初始化文件

导入所有 Layer 实现类以触发 @CrawlLayerFactory.register() 装饰器
这确保所有 Layer 类型在工厂注册表中可用
"""

# 导入所有 Layer 实现类以触发装饰器注册
from .enumerable_layer import EnumerableLayer
from .mapping_layer import MappingLayer
from .sequential_layer import SequentialLayer

__all__ = [
    "EnumerableLayer",
    "MappingLayer",
    "SequentialLayer",
]
