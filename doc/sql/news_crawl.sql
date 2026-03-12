-- ============================================================
-- 数据库初始化脚本
-- ============================================================
-- ⚠️ 重要：运行本项目前必须先执行此 SQL 文件初始化数据库
--
-- 执行方式：
--   方式1（推荐）: mysql -u root -p < doc/sql/news_crawl.sql
--   方式2: 使用 MySQL Workbench 打开并执行
--   方式3: 命令行: mysql -u root -p -e "source /path/to/news_crawl.sql"
--
-- 功能说明：
--   1. 创建数据库 news_crawl
--   2. 创建 3 张核心表：news_source, news_link, news_content
--   3. 运行主程序时，插入配置新闻源数据
--
-- 版本要求：MySQL 5.7+ / MariaDB 10.2+
-- ============================================================
CREATE DATABASE IF NOT EXISTS `news_crawl`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `news_crawl`;

-- ------------------------------------------------------------
-- 1. news_source — 新闻源元数据表
--    职责：描述一个新闻源"是什么"，静态配置，低频变更
--    写入方：人工初始化；status 字段由程序在解析持续异常时自动更新
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `news_source`;
CREATE TABLE `news_source`
(
    `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `resource_id` VARCHAR(255) NOT NULL COMMENT '与代码 AbstractNewsSourceConfig.source_id 严格对应 规则待定不太确定，命名规范：{country}_{media_name}，如 sg_straits_times',
    `name`        VARCHAR(255) NOT NULL COMMENT '媒体机构名称，如 Vietnam News',
    `domain`      VARCHAR(255) NOT NULL COMMENT '域名，如 vietnamnews.vn',
    `url`         VARCHAR(255) NOT NULL COMMENT '新闻页面 URL，备用一下',
    `country`     CHAR(2)      NOT NULL COMMENT '所属国家，ISO 3166-1 alpha-2，如 SG / MY / TH',
    `language`    VARCHAR(20)  NOT NULL COMMENT '主要语言，BCP 47 格式，如 en / zh / id / th',
    `status`      TINYINT      NOT NULL DEFAULT 0
        COMMENT '0-正常调度  1-手动停用  2-解析异常（parse_response 连续失败后由程序自动标记）；CrawlOrchestrator 仅调度 status=0 的源',
    `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_resource_id` (`resource_id`),
    INDEX `idx_domain` (`domain`),
    INDEX `idx_status` (`status`),
    INDEX `idx_country` (`country`)

) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
    COMMENT = '新闻源元数据表，仅存静态描述信息；请求配置（RequestConfig）与 Layer 结构在代码中维护，不在此处存储；这里图省事';



DROP TABLE IF EXISTS `news_link`;
CREATE TABLE `news_link`
(
    `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT,

    -- 新闻源关联（冗余存储，查询不需要 JOIN）
    `resource_id`   VARCHAR(255) NOT NULL COMMENT '关联 news_source.resource_id',
    `country`       VARCHAR(20)  NOT NULL COMMENT '冗余，来自 news_source',
    `name`          VARCHAR(255) NOT NULL COMMENT '冗余，媒体机构名称',
    `domain`        VARCHAR(255) NOT NULL COMMENT '冗余，域名',
    `language`      VARCHAR(20)  NOT NULL COMMENT '冗余，语言代码',

    -- 链接
    `url`           VARCHAR(255) NOT NULL COMMENT '新闻页面 URL',
    `crawl_params`  JSON         NULL COMMENT '发现此链接时的完整遍历参数快照，如 {"cat1":"tech","cat2":"ai","page":1}；用于问题排查与链接复现，不参与业务查询',
    `category`      VARCHAR(100) NOT NULL COMMENT '栏目分类，如 Politics（原 class_1）',

    -- 流水线状态
    `is_parse`      TINYINT      NOT NULL DEFAULT 0
        COMMENT '0-未解析  1-解析成功  2-日期不符  3-标题或正文无内容  4-解析失败',
    `is_translated` TINYINT      NOT NULL DEFAULT 0
        COMMENT '0-未翻译  1-已翻译  2-翻译失败',
    `success`       TINYINT      NOT NULL DEFAULT 0
        COMMENT '0-未同步到报告库  1-已同步',

    `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_url` (`url`),
    INDEX `idx_resource_id` (`resource_id`),
    INDEX `idx_is_parse` (`is_parse`),
    INDEX `idx_success` (`success`),
    INDEX `idx_country` (`country`),
    INDEX `idx_domain` (`domain`)

    -- 复合索引（覆盖流水线最高频的三种查询模式）
    -- ① 爬虫调度：按源拉取待处理链接，按时间排序
    # INDEX       `idx_resource_fetch`      (`resource_id`, `fetch_status`, `created_at`),
    -- ② 解析器调度：拉取已抓取但未解析的链接
    # INDEX       `idx_fetch_parse`         (`fetch_status`, `is_parse`),
    -- ③ 同步调度：拉取解析成功但未同步的链接
    # INDEX       `idx_parse_sync`          (`is_parse`, `sync_status`)

) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
    COMMENT = '新闻链接主表，记录爬虫发现的所有链接及其流水线状态';
# 健康检查的记录肯定是不能放在整个表里


-- ============================================================
-- 3. news_content — 新闻内容表
--    职责：存储解析后的结构化内容与翻译结果
--    写入时机：is_parse=1（解析成功）后由解析器写入
--    主键与 news_link.id 完全对应（1:1），无独立自增
--    无显式外键约束，应用层保证 id 存在于 news_link
-- ============================================================
DROP TABLE IF EXISTS `news_content`;
CREATE TABLE `news_content`
(
    `id`            INT UNSIGNED NOT NULL COMMENT '与 news_link.id 完全对应，非自增',

    -- 原始抓取内容
    `html_content`  MEDIUMTEXT   NULL COMMENT '原始 HTML，fetch_status=1 后写入；正文解析的原始来源',
    `publish_date`  DATE         NULL COMMENT '发布日期，无法解析时存 NULL，严禁写入 0000-00-00',

    -- 解析产物（原语言）
    `title`         TEXT         NULL COMMENT '原语言标题',
    `abstract`      TEXT         NULL COMMENT '摘要（从页面提取，非 AI 生成；如来源不同子类注释说明）',
    `content`       MEDIUMTEXT   NULL COMMENT '原语言正文',

    -- 中文翻译
    `title_cn`      TEXT         NULL,
    `abstract_cn`   TEXT         NULL,
    `content_cn`    MEDIUMTEXT   NULL,

    -- 英文翻译
    `title_en`      TEXT         NULL,
    `abstract_en`   TEXT         NULL,
    `content_en`    MEDIUMTEXT   NULL,

    -- 翻译状态（从 news_link 移入，属于内容层）
    `is_translated` TINYINT      NOT NULL DEFAULT 0
        COMMENT '0-未翻译  1-已翻译  2-翻译失败',

    -- 调试与追溯
    `parsed_at`     DATETIME     NULL     DEFAULT NULL
        COMMENT '最近一次成功解析的时间；与 created_at 区分，支持重解析场景',
    `parse_error`   TEXT         NULL
        COMMENT '最近一次解析失败的异常信息（对应 news_link.is_parse=4），方便排查；成功时清空',

    `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    INDEX `idx_publish_date` (`publish_date`),
    INDEX `idx_is_translated` (`is_translated`),
    FULLTEXT INDEX `ft_title` (`title`),
    FULLTEXT INDEX `ft_title_en` (`title_en`),
    FULLTEXT INDEX `ft_content` (`content`)

) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
    COMMENT = '新闻内容表，1:1 对应 news_link，仅在解析成功后写入。parse_error 在 is_parse=4 时由应用层同步写入本表，便于故障排查。';


-- ============================================================
-- 4. crawl_log — 爬虫执行日志表
--    职责：记录每次爬取任务的详细执行结果
--    写入方：爬虫服务在每次爬取结束后写入
-- ============================================================
DROP TABLE IF EXISTS `crawl_log`;
CREATE TABLE `crawl_log`
(
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `resource_id`         VARCHAR(255) NOT NULL COMMENT '关联 news_source.resource_id',

    -- 爬取结果汇总
    `crawl_status`        VARCHAR(20)  NOT NULL
        COMMENT 'success-全部成功 partial-部分失败 failed-全部失败',
    `total_categories`    INT          NOT NULL DEFAULT 0 COMMENT '本次爬取的栏目/参数组合数',
    `success_categories`  INT          NOT NULL DEFAULT 0 COMMENT '成功的栏目数',
    `failed_categories`   INT          NOT NULL DEFAULT 0 COMMENT '失败的栏目数',
    `total_links_found`   INT          NOT NULL DEFAULT 0 COMMENT '总共发现的链接数',
    `total_links_new`     INT          NOT NULL DEFAULT 0 COMMENT '新增链接数',

    -- 详细信息（JSON格式）
    `details`             JSON         NULL COMMENT '每个栏目的详细结果，格式见注释',

    -- 时间
    `started_at`          DATETIME     NOT NULL COMMENT '爬取开始时间',
    `finished_at`         DATETIME     NOT NULL COMMENT '爬取结束时间',
    `duration_ms`         INT          NOT NULL COMMENT '耗时（毫秒）',

    `created_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    INDEX `idx_resource_id` (`resource_id`),
    INDEX `idx_crawl_status` (`crawl_status`),
    INDEX `idx_started_at` (`started_at`)

) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
    COMMENT = '爬虫执行日志表：记录每次爬取任务的详细结果，用于监控和问题排查

-- details 字段 JSON 格式示例：
-- {
--   "categories": [
--     {
--       "category": "politics",
--       "params": {"category": "politics", "page": 1},
--       "status": "success",
--       "links_found": 10,
--       "links_new": 5,
--       "duration_ms": 1234
--     },
--     {
--       "category": "tech",
--       "params": {"category": "tech", "page": 1},
--       "status": "http_error",
--       "http_code": 500,
--       "error": "Internal Server Error",
--       "duration_ms": 567
--     }
--   ]
-- }
';


-- ============================================================
-- 初始化数据：插入默认新闻源
-- ============================================================
-- 说明：项目运行需要一定需要插入配置好的新闻源
-- ============================================================

INSERT INTO `news_source` (
    `resource_id`,
    `name`,
    `domain`,
    `url`,
    `country`,
    `language`,
    `status`,
    `created_at`,
    `updated_at`
) VALUES (
    'id_jawapos',                    -- 新闻源唯一标识（对应代码中的 JawaPosConfig）
    'Jawa Pos',                      -- 媒体名称
    'www.jawapos.com',               -- 域名
    'https://www.jawapos.com',       -- 首页 URL
    'ID',                            -- 国家代码（印度尼西亚）
    'id',                            -- 语言代码（印尼语）
    0,                               -- 状态：0-正常调度
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE             -- 如果已存在则更新时间
    `updated_at` = NOW();

-- ------------------------------------------------------------
-- Berita Harian (马来西亚)
-- ------------------------------------------------------------
INSERT INTO `news_source` (
    `resource_id`,
    `name`,
    `domain`,
    `url`,
    `country`,
    `language`,
    `status`,
    `created_at`,
    `updated_at`
) VALUES (
    'my_berita_harian',              -- 新闻源唯一标识（对应代码中的 BeritaHarianConfig）
    'Berita Harian',                 -- 媒体名称
    'www.bharian.com.my',            -- 域名
    'https://www.bharian.com.my',    -- 首页 URL
    'MY',                            -- 国家代码（马来西亚）
    'ms',                            -- 语言代码（马来语）
    0,                               -- 状态：0-正常调度
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE             -- 如果已存在则更新时间
    `updated_at` = NOW();

-- ------------------------------------------------------------
-- 金边晚报 (柬埔寨)
-- ------------------------------------------------------------
INSERT INTO `news_source` (
    `resource_id`,
    `name`,
    `domain`,
    `url`,
    `country`,
    `language`,
    `status`,
    `created_at`,
    `updated_at`
) VALUES (
    'kh_jinbian_wanbao',             -- 新闻源唯一标识（对应代码中的 JinbianWanbaoConfig）
    '金边晚报',                       -- 媒体名称
    'www.jinbianwanbao.cn',          -- 域名
    'http://www.jinbianwanbao.cn',   -- 首页 URL
    'KH',                            -- 国家代码（柬埔寨）
    'zh-CN',                         -- 语言代码（中文简体）
    0,                               -- 状态：0-正常调度
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE             -- 如果已存在则更新时间
    `updated_at` = NOW();

-- ------------------------------------------------------------
-- Kompas (印度尼西亚)
-- ------------------------------------------------------------
INSERT INTO `news_source` (
    `resource_id`,
    `name`,
    `domain`,
    `url`,
    `country`,
    `language`,
    `status`,
    `created_at`,
    `updated_at`
) VALUES (
    'id_kompas',                     -- 新闻源唯一标识（对应代码中的 KompasConfig）
    'Kompas',                        -- 媒体名称
    'www.kompas.com',                -- 域名
    'https://www.kompas.com',        -- 首页 URL
    'ID',                            -- 国家代码（印度尼西亚）
    'id',                            -- 语言代码（印尼语）
    0,                               -- 状态：0-正常调度
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE             -- 如果已存在则更新时间
    `updated_at` = NOW();

-- ------------------------------------------------------------
-- BruDirect (文莱)
-- ------------------------------------------------------------
INSERT INTO `news_source` (
    `resource_id`,
    `name`,
    `domain`,
    `url`,
    `country`,
    `language`,
    `status`,
    `created_at`,
    `updated_at`
) VALUES (
    'bn_brudirect',                  -- 新闻源唯一标识（对应代码中的 BruDirectConfig）
    'BruDirect',                     -- 媒体名称
    'brudirect.com',                 -- 域名
    'https://brudirect.com',         -- 首页 URL
    'BN',                            -- 国家代码（文莱）
    'en',                            -- 语言代码（英语）
    0,                               -- 状态：0-正常调度
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE             -- 如果已存在则更新时间
    `updated_at` = NOW();

-- ------------------------------------------------------------
-- Bangkok Post (泰国)
-- ------------------------------------------------------------
INSERT INTO `news_source` (
    `resource_id`,
    `name`,
    `domain`,
    `url`,
    `country`,
    `language`,
    `status`,
    `created_at`,
    `updated_at`
) VALUES (
    'th_bangkok_post',               -- 新闻源唯一标识（对应代码中的 BangkokPostConfig）
    'Bangkok Post',                  -- 媒体名称
    'www.bangkokpost.com',           -- 域名
    'https://www.bangkokpost.com',   -- 首页 URL
    'TH',                            -- 国家代码（泰国）
    'en',                            -- 语言代码（英语）
    0,                               -- 状态：0-正常调度
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE             -- 如果已存在则更新时间
    `updated_at` = NOW();

-- ------------------------------------------------------------
-- Inquirer (菲律宾)
-- ------------------------------------------------------------
INSERT INTO `news_source` (
    `resource_id`,
    `name`,
    `domain`,
    `url`,
    `country`,
    `language`,
    `status`,
    `created_at`,
    `updated_at`
) VALUES (
    'ph_inquirer',                   -- 新闻源唯一标识（对应代码中的 InquirerConfig）
    'Inquirer',                      -- 媒体名称
    'newsinfo.inquirer.net',         -- 域名
    'https://newsinfo.inquirer.net', -- 首页 URL
    'PH',                            -- 国家代码（菲律宾）
    'en',                            -- 语言代码（英语）
    0,                               -- 状态：0-正常调度
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE             -- 如果已存在则更新时间
    `updated_at` = NOW();

-- ------------------------------------------------------------
-- Jakarta Globe (印度尼西亚)
-- ------------------------------------------------------------
# TODO：这个配置文件应该是有问题的
INSERT INTO `news_source` (
    `resource_id`,
    `name`,
    `domain`,
    `url`,
    `country`,
    `language`,
    `status`,
    `created_at`,
    `updated_at`
) VALUES (
    'id_jakarta_globe',              -- 新闻源唯一标识（对应代码中的 JakartaGlobeConfig）
    'Jakarta Globe',                 -- 媒体名称
    'jakartaglobe.id',               -- 域名
    'https://jakartaglobe.id',       -- 首页 URL
    'ID',                            -- 国家代码（印度尼西亚）
    'en',                            -- 语言代码（英语）
    0,                               -- 状态：0-正常调度
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE             -- 如果已存在则更新时间
    `updated_at` = NOW();

-- ------------------------------------------------------------
-- The Business Times (新加坡)
-- ------------------------------------------------------------
INSERT INTO `news_source` (
    `resource_id`,
    `name`,
    `domain`,
    `url`,
    `country`,
    `language`,
    `status`,
    `created_at`,
    `updated_at`
) VALUES (
    'sg_business_times',                    -- 新闻源唯一标识（对应代码中的 BusinessTimesConfig）
    'The Business Times',                   -- 媒体名称
    'www.businesstimes.com.sg',             -- 域名
    'https://www.businesstimes.com.sg',     -- 首页 URL
    'SG',                                   -- 国家代码（新加坡）
    'en',                                   -- 语言代码（英语）
    0,                                      -- 状态：0-正常调度
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE                     -- 如果已存在则更新时间
    `updated_at` = NOW();

-- ====================================================
-- 新闻源 10: BeritaSatu.com（印度尼西亚综合新闻）
-- ====================================================
INSERT INTO `news_source` (
    `resource_id`,
    `name`,
    `domain`,
    `url`,
    `country`,
    `language`,
    `status`,
    `created_at`,
    `updated_at`
) VALUES (
    'id_beritasatu',                        -- 新闻源唯一标识（对应代码中的 BeritaSatuConfig）
    'BeritaSatu.com',                       -- 媒体名称
    'www.beritasatu.com',                   -- 域名
    'https://www.beritasatu.com',           -- 首页 URL
    'ID',                                   -- 国家代码（印度尼西亚）
    'id',                                   -- 语言代码（印尼语）
    0,                                      -- 状态：0-正常调度
    NOW(),
    NOW()
)
ON DUPLICATE KEY UPDATE                     -- 如果已存在则更新时间
    `updated_at` = NOW();
