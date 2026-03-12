# 应用配置

> AppConfig - 从 .env 文件加载配置

## 配置类

### AppConfig
**主配置类**

**字段**：
- `env` - 环境（development/production/test）
- `log_level` - 日志级别
- `database` - 数据库配置
- `http` - HTTP 配置

### DatabaseConfig
**数据库配置**

**字段**：
- `host`, `port`, `user`, `password`, `database`
- `pool_size` - 连接池大小
- `pool_recycle` - 连接回收时间
- `echo` - 是否打印 SQL

**属性**：
- `url` - 构建数据库连接 URL

### HttpConfig
**HTTP 客户端配置**

**字段**：
- `timeout` - 总超时
- `connect_timeout` - 连接超时
- `read_timeout` - 读取超时
- `max_connections` - 最大连接数
- `max_keepalive_connections` - 最大保活连接数

## 配置文件

### .env（不提交 Git）
```bash
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=news_crawl

HTTP_TIMEOUT=30
HTTP_MAX_CONNECTIONS=20

APP_ENV=development
LOG_LEVEL=INFO
```

### .env.example（提交 Git）
配置模板，隐藏敏感信息

## 加载方式
```python
config = AppConfig.from_env(".env")
```

## 设计原则

### 12-Factor App
- 所有配置从环境变量加载
- 配置与代码分离
- 支持多环境

### 类型安全
- 使用 dataclass + 类型注解
- 编译时类型检查

### 不可变性
- `@dataclass(frozen=True)`
- 防止意外修改

## 相关链接

- [依赖注入](di_container) - 配置注入
- [快速开始](../../quick_start) - 环境配置
