"""
新闻源配置包

此目录存放具体的新闻源配置类实现。

使用方式：
1. 创建新闻源配置类，继承 AbstractNewsSourceConfig
2. 使用 @NewsSourceConfigRegistry.register("resource_id") 装饰器注册
3. 在此文件中导入配置类以触发装饰器注册

示例：
    # jawapos_config.py
    @NewsSourceConfigRegistry.register("id_jawapos")
    class JawaPosConfig(AbstractNewsSourceConfig):
        ...

    # __init__.py
    from v1.DDD.app.src.resource.news_source.jawapos_config import JawaPosConfig

注意：
- 配置类必须在应用启动时被导入，否则装饰器不会执行
- 建议在此 __init__.py 中统一导入所有配置类
- 不要忘记sql文件需要更新插入
"""
# 导入所有新闻源配置类以触发装饰器注册
from v1.DDD.app.src.resource.news_source.jawapos_config import JawaPosConfig
from v1.DDD.app.src.resource.news_source.berita_harian_config import BeritaHarianConfig
from v1.DDD.app.src.resource.news_source.jinbian_wanbao_config import JinbianWanbaoConfig
from v1.DDD.app.src.resource.news_source.kompas_config import KompasConfig

__all__ = ["JawaPosConfig", "BeritaHarianConfig", "JinbianWanbaoConfig", "KompasConfig"]
