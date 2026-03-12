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





### 新闻源配置

>  📊 高优先级失败媒体分析
>
>   🔴 P0 - 顶级英文媒体（国际影响力大）
>
>   3. The Business Times (新加坡)
>
>      > [home - Laotian Times](https://laotiantimes.com/)：可以试试
>
>     - 状态：✗ 0/13 (0%)
>     - 重要性：新加坡顶级商业媒体
>     - 战略价值：⭐⭐⭐⭐⭐
>
>   4. The Phnom Penh Post (柬埔寨)
>
>      > [The Phnom Penh Post | The Phnom Penh Post is the oldest and most comprehensive independent newspaper covering Cambodia. Cambodia News, Phnom Penh News](https://www.phnompenhpost.com/)
>
>     - 状态：✗ 1/9 (11.1%) - 有更新但爬取失败
>     - 重要性：柬埔寨最大英文媒体
>     - 战略价值：⭐⭐⭐⭐
>
> ---
>
>   🟡 P1 - 样本量大的失败媒体（修复收益高）
>
>   5. The Online Citizen (新加坡)
>
>      > [- The Online Citizen](https://www.theonlinecitizen.com/)
>
>     - 状态：✗ 0/22 (0%) - 样本量最大
>     - 重要性：新加坡独立政治新闻网站
>     - 问题推测：可能需要登录或有严格反爬
>
>   6. Suara Pembaruan (印尼)
>
>      > [Berita Terkini Hari Ini, Bersatu Menginspirasi - BeritaSatu.com](https://www.beritasatu.com/)：特殊用例可以试试
>
>     - 状态：✗ 0/21 (0%)
>     - 重要性：印尼主流媒体
>     - 注意：URL 显示为 beritasatu.com（可能域名变更）
>
>     7. Investor Daily (印尼)
>
>     - 状态：✗ 0/20 (0%)
>     - 重要性：印尼投资金融领域权威
>     - 战略价值：商业情报重要来源
>
>     8. Business Mirror (菲律宾)
>
>     - 状态：✗ 0/20 (0%)
>     - 重要性：菲律宾商业媒体
>     - 战略价值：⭐⭐⭐⭐
>
> ---
>
>   🟢 P2 - 活跃但失败媒体（网站正常，配置有问题）
>
>     9. Republika (印尼)
>
>     - 状态：✓ 3/35 (8.6%) - 有更新但爬取率低
>     - 重要性：印尼主流伊斯兰媒体
>     - 修复收益：样本量大（35个）
>
>     10. Bisnis Indonesia (印尼)
>
>     - 状态：✓ 2/25 (8.0%) - 有更新但爬取率低
>     - 重要性：印尼商业财经权威
>     - 修复收益：样本量大（25个）
>
>     11. 南洋商报 (马来西亚)
>
>     - 状态：✓ 2/15 (13.3%) - 有更新但爬取率低
>     - 重要性：马来西亚华文主流媒体
>     - 战略价值：华文区域重要
>
> ---
>
>   🔵 P3 - 泰国主流媒体群组
>
>     12. Matichon (泰国)
>
>     - 状态：✗ 0/13 (0%)
>     - 重要性：泰国权威媒体集团
>
>     13. Thai Post (泰国)
>
>     - 状态：✗ 0/12 (0%)
>     - 重要性：泰国主流媒体
>
> ---
>
>   🎯 推荐修复顺序
>
>   第一批（顶级英文，调试容易）：
>
>     1. The Jakarta Post
>     2. Manila Bulletin
>     3. The Business Times
>
>   第二批（样本量大，修复收益高）：
>
>     4. The Online Citizen
>     5. Business Mirror
>     6. Investor Daily
>
>   第三批（活跃低效，优化提升）：
>
>     7. Republika (8.6% → 目标80%+)
>     8. Bisnis Indonesia (8.0% → 目标80%+)
>     9. 南洋商报 (13.3% → 目标80%+)
>
>   第四批（区域补充）：
>
>     10. The Phnom Penh Post (柬埔寨核心)
>     11. Matichon (泰国权威)
>
> ---
>
>   你想从哪个开始？ 我建议：
>
>   - 快速见效：The Jakarta Post（印尼顶级，英文调试）
>   - 高价值：Manila Bulletin（菲律宾最大，样本14个）
>   - 挑战性：The Online Citizen（22个样本全失败，可能技术难度高）

---

## P1 - 重要不紧急

### 功能完善
- 错误处理优化
- 日志系统完善
  - `crawl_log`表的json文件不太满意，太过省略了

- 配置管理优化

---

## P2 - 紧急不重要

### 监控告警

- 爬取失败告警
- 数据库异常告警
- 健康检查异常告警

### 运行统计
- 每日爬取量、新增链接数、成功率统计



### 反爬新闻源

>     1. Manila Bulletin (菲律宾)
>
> > claudflare绕不去，后面研究
>
>     - 状态：✗ 0/14 (0%)
>     - 重要性：菲律宾最大日报，历史最悠久
>     - 战略价值：⭐⭐⭐⭐⭐
>
> 

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
