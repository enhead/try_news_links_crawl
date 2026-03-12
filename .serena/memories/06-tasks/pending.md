# 待实现功能清单

## 🔴 当前在做
<!-- 同时最多1-2件，写清楚进展和卡点 -->
_（空）_

---

## P0 - 紧急且重要

### sequential_layer 职责重构
- **问题**：`sequential_layer.py` 里有大量与调用爬虫节点相关的代码，与顺序层本身职责混在一起
- **方向 A**：抽离节点调用逻辑到独立类
- **方向 B**：新增 `SingleLayer`，让无需翻页的新闻源绕过顺序层直接爬取
- **文件**：`src/v1/DDD/domain/http_news_links_crawl/service/single_news_link_crawl/crawl_layer/impl/sequential_layer.py`
- **下一步**：读代码后先确认选哪个方向，再动手

### jakartaglobe.id 分页问题
- **问题**：该网站 `https://jakartaglobe.id/{category}/newsindex/` 自身分页机制损坏
- **初步结论**：不需要分页处理
- **待研究**：是直接在该网站的 layer_schema 配置中去掉分页层，还是需要在 Layer 机制层面支持"无需分页"的标记
- **关联**：与 sequential_layer 重构可能有关

---

## P1 - 重要不紧急

### 功能完善
- 错误处理优化
- 日志系统完善
- 配置管理优化

---

## P2 - 紧急不重要

### 监控告警
- 爬取失败告警
- 数据库异常告警
- 健康检查异常告警

### 运行统计
- 每日爬取量、新增链接数、成功率统计

---

## P3 - 不紧急不重要

### 性能优化
- 并发控制、连接池优化、批量操作调优

### 高级功能
- 增量调度、动态反爬、分布式爬取

---

## 相关链接

- [项目概览](../overview) - 已完成功能
- [检查清单](checklist) - 完成检查项
