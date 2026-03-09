-- ------------------------------------------------------------
-- 1. news_source — 新闻源元数据表
--    职责：描述一个新闻源"是什么"，静态配置，低频变更
--    写入方：人工初始化；status 字段由程序在解析持续异常时自动更新
-- ------------------------------------------------------------
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
    COMMENT = '新闻源元数据表，仅存静态描述信息；请求配置（RequestConfig）与 Layer 结构在代码中维护，不在此处存储';



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


-- ============================================================
-- 3. news_content — 新闻内容表
--    职责：存储解析后的结构化内容与翻译结果
--    写入时机：is_parse=1（解析成功）后由解析器写入
--    主键与 news_link.id 完全对应（1:1），无独立自增
--    无显式外键约束，应用层保证 id 存在于 news_link
-- ============================================================
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