from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Any,Mapping
from enum import Enum

from v1.DDD.domain.http_news_links_crawl.service.crawl_layer.abstract_layer import AbstractCrawlLayer




class LayerType(str, Enum): # 此处改为枚举类
    """
    目前拥有的几个实现类对应的Key，此处主要用于注册类
    """
    ENUMERABLE = "enumerable"
    MAPPING  = "mapping"
    SEQUENTIAL = "sequential"


# 大部分重要参数我都放这里了
# 在包一层传参，感觉这里仅仅是做到
@dataclass(slots=True,frozen=True)
#   slots：加上这个注解后会更省内存，改为固定结构存储，不再借助__dict__，适合比较固定的场景
#   frozen: 不允许修改,可以做更多的优化
class LayerSchema:
    """
    描述 Layer 链结构，纯数据，可序列化
        用于注册Layer对象
    """
    type: LayerType               # "enumerable" | "dependent" | "sequential"
    key: str
    values: Mapping[str, Any] | list[Any] | Any             # 各 Layer 类型自己解释这个字段    # 为了拓展性，这里不改了
    next: "LayerSchema | None" = None




# 工厂装饰器 — 无参数，自动读类上的 type_key
class CrawlLayerFactory:
    _registry: dict[str, type[AbstractCrawlLayer]] = {}

    @classmethod
    def register(cls, type_key: str):   # cls是类本身的意思
        """
        装饰器：类自己声明注册到哪个 key
            性能：
                - 几乎为零。 装饰器在 import 时执行一次，本质就是一次 dict[key] = class 的写入。
                - 运行时 build() 只是一次 dict.get(key)，O(1)。
        """

        def decorator(layer_cls: type[AbstractCrawlLayer]):
            if type_key in cls._registry:   # 做一次重复性检查
                raise RuntimeError(f"Layer type 已注册: {type_key}")   # 这里就不用额外封装了，如果没有设计对，感觉不能让她运行了

            cls._registry[type_key] = layer_cls
            return layer_cls

        return decorator

    @classmethod
    def build(cls, schema: LayerSchema) -> AbstractCrawlLayer:

        layer_cls = cls._registry.get(schema.type)

        if layer_cls is None:
            raise ValueError(f"未知 Layer 类型: {schema.type}")

        next_layer = cls.build(schema.next) if schema.next else None

        return layer_cls(
            key=schema.key,
            values=schema.values,
            next_layer=next_layer
        )