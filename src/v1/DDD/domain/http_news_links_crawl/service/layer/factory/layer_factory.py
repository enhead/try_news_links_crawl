from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Any

from v1.DDD.domain.http_news_links_crawl.service.layer.abstract_layer import AbstractLayer


# 大部分重要参数我都放这里了

# 在包一层传参，感觉这里仅仅是做到
@dataclass
class LayerSchema:
    """
    描述 Layer 链结构，纯数据，可序列化
        用于注册Layer对象
    """
    type: str               # "enumerable" | "dependent" | "sequential"
    key: str
    values: Any             # 各 Layer 类型自己解释这个字段
    next: LayerSchema | None = None

# 常量定义（对应 StrategyRuleConstants）
class LayerTypeConstants:
    """
    目前拥有的几个实现类对应的Key，此处主要用于注册类
    """
    ENUMERABLE = "enumerable"
    DEPENDENT  = "dependent"
    SEQUENTIAL = "sequential"



# 工厂装饰器 — 无参数，自动读类上的 type_key
class LayerFactory:
    _registry: dict[str, type[AbstractLayer]] = {}

    @classmethod
    def register(cls, type_key: str):
        """
        装饰器：类自己声明注册到哪个 key
            性能：
                - 几乎为零。 装饰器在 import 时执行一次，本质就是一次 dict[key] = class 的写入。
                - 运行时 build() 只是一次 dict.get(key)，O(1)。
        """

        def decorator(layer_cls: type[AbstractLayer]):
            cls._registry[type_key] = layer_cls
            return layer_cls

        return decorator

    @classmethod
    def build(cls, schema: LayerSchema) -> AbstractLayer:
        layer_cls = cls._registry.get(schema.type)
        if layer_cls is None:
            raise ValueError(f"未知 Layer 类型: {schema.type}")

        next_layer = cls.build(schema.next) if schema.next else None

        if next_layer is None:
            return layer_cls(key=schema.key, values=schema.values)
        return layer_cls(key=schema.key, values=schema.values, next_layer=next_layer)