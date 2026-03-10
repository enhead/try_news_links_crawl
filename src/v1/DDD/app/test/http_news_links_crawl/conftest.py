"""
pytest 配置文件

自动添加 src 目录到 Python 路径
"""

import sys
from pathlib import Path

# 计算到 src 目录的路径
# 当前文件: src/v1/DDD/app/test/http_news_links_crawl/conftest.py
# 需要到达: src/
# 向上 6 级: conftest.py -> http_news_links_crawl -> test -> app -> DDD -> v1 -> src
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

print(f"[conftest] 添加路径到 sys.path: {project_root}")
