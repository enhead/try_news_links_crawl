# BeritaSatu.com 新闻源集成指南

## 📋 已创建的文件

### 1. **配置文件**
- **路径**: `src/v1/DDD/app/src/resource/news_source/beritasatu_config.py`
- **功能**: BeritaSatu.com 的完整配置实现
- **特点**:
  - 支持 7 个主要栏目（国内、地方、经济、国际、体育、生活、汽车科技）
  - 适配特殊 URL 格式（包含数字 ID）
  - 完整的链接过滤和去重逻辑

### 2. **注册文件**（已更新）
- **路径**: `src/v1/DDD/app/src/resource/news_source/__init__.py`
- **更新**: 添加了 `BeritaSatuConfig` 的导入和导出

### 3. **测试脚本**
- **路径**: `test_beritasatu.py`
- **功能**: 测试配置是否正常工作

### 4. **SQL 脚本**（已更新）
- **路径**: `doc/sql/news_crawl.sql`
- **更新**: 添加了 BeritaSatu 的数据库记录

---

## 🚀 部署步骤

### 步骤 1: 更新数据库

执行 SQL 脚本以添加新闻源记录：

```bash
# 方式 1（推荐）
mysql -u root -p < doc/sql/news_crawl.sql

# 方式 2: 只执行 BeritaSatu 的 INSERT 语句
mysql -u root -p news_crawl -e "
INSERT INTO news_source (
    resource_id, name, domain, url, country, language, status, created_at, updated_at
) VALUES (
    'id_beritasatu',
    'BeritaSatu.com',
    'www.beritasatu.com',
    'https://www.beritasatu.com',
    'ID',
    'id',
    0,
    NOW(),
    NOW()
) ON DUPLICATE KEY UPDATE updated_at = NOW();
"
```

### 步骤 2: 运行测试脚本

验证配置是否正常工作：

```bash
cd /path/to/try_news_links_crawl
python test_beritasatu.py
```

**预期输出：**
```
===========================================================
BeritaSatu.com 配置测试
===========================================================
✓ 配置实例创建成功

1. 页面解析测试:
  正在抓取: https://www.beritasatu.com/nasional
  ✓ HTTP请求成功: status=200
  ✓ 解析成功
  ✓ 发现链接数: 15-30（大约）

  前10个链接示例:
    1. https://www.beritasatu.com/nasional/2975467/...
    2. https://www.beritasatu.com/nasional/2975441/...
    ...

  URL格式验证:
    有效URL数（包含数字ID）: 15/15
    验证通过: ✓

2. 分类提取测试:
  nasional -> 国内 (Nasional)
  nusantara -> 地方/群岛 (Nusantara)
  ...
===========================================================
测试完成
===========================================================
```

### 步骤 3: 运行主程序测试

使用主程序测试新闻源：

```bash
python src/v1/DDD/app/src/main/application.py id_beritasatu
```

---

## 📊 配置详情

### 支持的栏目

| 栏目代码 | 中文名称 | 英文名称 | URL |
|---------|---------|---------|-----|
| nasional | 国内 | Nasional | /nasional |
| nusantara | 地方/群岛 | Nusantara | /nusantara |
| ekonomi | 经济 | Ekonomi | /ekonomi |
| internasional | 国际 | Internasional | /internasional |
| sport | 体育 | Sport | /sport |
| lifestyle | 生活方式 | Lifestyle | /lifestyle |
| ototekno | 汽车科技 | Ototekno | /ototekno |

### URL 格式说明

**栏目页：**
```
https://www.beritasatu.com/nasional
```

**文章页（特殊格式）：**
```
https://www.beritasatu.com/nasional/2975467/muhammadiyah-tetapkan-idulfitri-1447-h-jatuh-pada-20-maret-2026
```

**格式解析：**
- `nasional`: 栏目名称
- `2975467`: **文章数字 ID**（关键特征）
- `muhammadiyah-tetapkan-...`: URL slug（文章标题）

### 过滤规则

自动排除以下类型的页面：
- 标签页 (`/tag/`)
- 作者页 (`/penulis/`)
- 编辑页 (`/editor/`)
- 索引页 (`/indeks`)
- 多媒体索引 (`/multimedia`)
- 特殊栏目（B-Plus、Network）
- 栏目首页和二级栏目首页

---

## 🔧 技术特点

### 1. **URL 正则表达式**

```python
article_pattern = r'beritasatu\.com/(nasional|nusantara|ekonomi|internasional|sport|lifestyle|ototekno|dki-jakarta|jabar|jateng|jatim|sumut|sumsel|bali|sulsel|kepri|banten)/\d+/[a-z0-9\-]+$'
```

**特点：**
- 匹配所有主要栏目
- **必须包含数字 ID** (`\d+`)
- 必须有 URL slug

### 2. **爬取策略**

```python
EnumerableLayer (栏目枚举)
  └─> SequentialLayer (只爬首页，max_pages=1)
        └─> DefaultCrawlNode (标准 HTTP 请求)
```

### 3. **性能优化**

- 只爬取每个栏目的首页
- 自动去重
- URL 清洗和规范化
- 高效的正则匹配

---

## ⚠️ 注意事项

1. **数字 ID 是必需的**
   - BeritaSatu 的 URL 包含唯一数字 ID
   - 正则表达式中的 `\d+` 不能省略

2. **地方栏目的扩展**
   - 除了主要栏目，还包含地方栏目（dki-jakarta, jabar, jateng 等）
   - 已在正则表达式中包含

3. **反爬虫机制**
   - 目前无强反爬虫机制
   - 建议保持合理的请求间隔

4. **语言处理**
   - 主要语言：印度尼西亚语
   - 需要确保系统支持 UTF-8 编码

---

## 🐛 故障排查

### 问题 1: 测试脚本无法运行

**解决方法：**
```bash
# 检查 Python 路径
export PYTHONPATH="${PYTHONPATH}:/path/to/try_news_links_crawl"

# 或在项目根目录运行
cd /path/to/try_news_links_crawl
python test_beritasatu.py
```

### 问题 2: 无法解析 URL

**检查：**
1. URL 是否包含数字 ID
2. 正则表达式是否正确
3. 网站结构是否发生变化

### 问题 3: 数据库连接失败

**检查：**
1. MySQL 服务是否运行
2. 数据库凭据是否正确
3. SQL 脚本是否执行成功

---

## 📈 预期结果

### 每个栏目的链接数量

根据测试，每个栏目首页大约包含：
- **国内（nasional）**: 15-25 篇文章
- **经济（ekonomi）**: 10-20 篇文章
- **国际（internasional）**: 10-15 篇文章
- **体育（sport）**: 10-20 篇文章
- **其他栏目**: 10-15 篇文章

**总计**: 每次爬取约 **80-120** 个新闻链接

---

## ✅ 验证清单

完成以下检查以确保集成成功：

- [ ] SQL 脚本已执行，数据库中存在 `id_beritasatu` 记录
- [ ] 测试脚本运行成功，能够解析链接
- [ ] URL 格式验证通过（包含数字 ID）
- [ ] 主程序能够成功调度 BeritaSatu 爬虫
- [ ] 配置类已在 `__init__.py` 中正确导入

---

## 📞 支持

如有问题，请检查：
1. 配置文件: `beritasatu_config.py`
2. 测试脚本: `test_beritasatu.py`
3. 日志文件: 查看主程序输出

**特殊提示**：BeritaSatu.com 的 URL 格式较为特殊（包含数字 ID），这是与其他新闻源的主要区别。
