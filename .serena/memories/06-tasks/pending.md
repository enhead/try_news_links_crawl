# 待实现功能清单

> 按优先级组织的待办任务

## 当前在做



## P0 - 紧急且重要

- 完善Layer的机制规则：
  - https://jakartaglobe.id/{category}/newsindex/
    - 对于这个网站他本身分页自己就坏了，不需要分页，这里我需要研究下
  - C:\Users\Administrator\Desktop\work\try_news_links_crawl\src\v1\DDD\domain\http_news_links_crawl\service\single_news_link_crawl\crawl_layer\impl\sequential_layer.py
    - 关于顺序层的代码其实有很多都是跟调用爬虫节点相关的，这个其实最好抽离出来更好点
    - 或者看看是否需要新增 SingleLayer，直接绕过顺序层

## P1 - 重要不紧急



### 功能完善
- 错误处理优化
- 日志系统完善
- 配置管理优化

## P2 - 紧急不重要

### 监控告警
- 爬取失败告警
- 数据库异常告警
- 健康检查异常告警

### 运行统计
- 每日爬取量
- 新增链接数
- 成功率统计

## P3 - 不紧急不重要

### 性能优化
- 并发控制
- 连接池优化
- 批量操作调优

### 高级功能
- 增量调度
- 动态反爬
- 分布式爬取

## 相关链接

- [项目概览](../overview) - 已完成功能
- [检查清单](checklist) - 完成检查项
