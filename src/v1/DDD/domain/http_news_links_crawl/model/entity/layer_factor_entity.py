from __future__ import annotations
from dataclasses import dataclass
from typing import Any

# 最后还是决定用Context对象，传入哪些Bean对象，用IOC之类的方法学习成本还是太高

@dataclass
class LayerFactorEntity:
    """
    layer层的传参
    """
    ...