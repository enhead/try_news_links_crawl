# 应用生命周期管理

**最后更新**: 2026-03-11

## 概述

应用生命周期管理是应用层的核心职责之一，负责管理应用从启动到关闭的全过程。

**核心目标**：
- ✅ 统一管理应用启动和关闭
- ✅ 确保资源正确初始化和释放
- ✅ 提供优雅关闭机制
- ✅ 处理中断信号（Ctrl+C）

## 生命周期阶段

### 完整生命周期流程

```
1. 启动阶段 (Startup)
   ├─ 创建 DI 容器
   ├─ 加载配置（.env）
   ├─ 配置日志系统
   ├─ 创建单例资源（DbEngine, HttpAdapter）
   └─ 创建 Application 实例
   
2. 初始化阶段 (Initialization)
   ├─ 创建触发器
   ├─ 触发器 setup()
   │  ├─ 加载新闻源配置
   │  ├─ 初始化客户端连接
   │  └─ 注册路由/任务
   └─ 验证依赖可用性
   
3. 运行阶段 (Running)
   ├─ 触发器 start()
   ├─ 监听触发事件
   ├─ 执行业务逻辑
   └─ 等待中断信号
   
4. 关闭阶段 (Shutdown)
   ├─ 触发器 stop()
   ├─ 停止监听
   ├─ 关闭 HTTP 连接池
   ├─ 关闭数据库引擎
   └─ 释放所有资源
```

## 核心组件

### 1. Application 类

**文件**: `src/v1/DDD/app/src/main/application.py`

**职责**：
- 持有 DI 容器
- 管理应用生命周期
- 提供优雅关闭接口

```python
class Application:
    """应用实例"""
    
    def __init__(self, container: AppContainer):
        self.container = container
        self._logger = logging.getLogger(__name__)
    
    async def shutdown(self):
        """关闭应用，释放所有资源"""
        self._logger.info("正在关闭应用...")
        await self.container.shutdown_resources()
        self._logger.info("应用已关闭")
```

### 2. create_app() 函数

**文件**: `src/v1/DDD/app/src/main/application.py`

**职责**：
- 创建并初始化应用
- 加载配置
- 配置日志
- 返回 Application 实例

```python
async def create_app(env_file: str = ".env") -> Application:
    """
    创建应用实例
    
    Args:
        env_file: .env 文件路径
    
    Returns:
        Application 实例
    
    Raises:
        FileNotFoundError: .env 文件不存在
        ValueError: 配置错误
    """
    # 1. 创建容器
    container = AppContainer()
    
    # 2. 加载配置
    config = container.config()
    
    # 3. 配置日志
    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"应用启动: env={config.env}")
    logger.info(f"数据库: {config.database.url}")
    
    # 4. 创建应用实例
    return Application(container)
```

## 启动流程

### 完整启动序列

```python
async def main():
    # 阶段1: 创建应用
    app = await create_app()
    
    try:
        # 阶段2: 创建触发器
        trigger = ManualTrigger(
            container=app.container,
            source_ids=["id_jawapos"],
            load_sources=True
        )
        
        # 阶段3: 运行触发器（完整生命周期）
        await trigger.run()
        #   ├─ setup()
        #   ├─ start()
        #   └─ stop()
        
    except KeyboardInterrupt:
        logger.info("收到中断信号")
        
    except Exception as e:
        logger.error(f"应用运行失败: {e}", exc_info=True)
        raise
        
    finally:
        # 阶段4: 关闭应用
        await app.shutdown()

# 运行
asyncio.run(main())
```

### 启动日志示例

```
2026-03-11 10:00:00 - application - INFO - 应用启动: env=dev
2026-03-11 10:00:00 - application - INFO - 数据库: mysql+asyncmy://root:***@localhost:3306/news_crawl
2026-03-11 10:00:01 - base_trigger - INFO - 初始化触发器: ManualTrigger
2026-03-11 10:00:01 - base_trigger - INFO - 加载新闻源配置...
2026-03-11 10:00:01 - base_trigger - INFO - 已加载 1 个新闻源
2026-03-11 10:00:01 - base_trigger - INFO - 启动触发器: ManualTrigger
2026-03-11 10:00:01 - base_trigger - INFO - 开始爬取指定的 1 个新闻源
2026-03-11 10:00:05 - base_trigger - INFO - 停止触发器: ManualTrigger
2026-03-11 10:00:05 - application - INFO - 正在关闭应用...
2026-03-11 10:00:05 - container - INFO - 开始关闭应用资源...
2026-03-11 10:00:05 - container - INFO - ✓ HTTP 连接池已关闭
2026-03-11 10:00:05 - container - INFO - ✓ 数据库引擎已关闭
2026-03-11 10:00:05 - container - INFO - 应用资源关闭完成
2026-03-11 10:00:05 - application - INFO - 应用已关闭
```

## 关闭流程

### 优雅关闭

**目标**：
- ✅ 停止接受新请求
- ✅ 等待当前请求完成
- ✅ 关闭所有连接
- ✅ 释放所有资源
- ✅ 记录关闭日志

### 关闭序列

```python
async def shutdown(self):
    """应用关闭流程"""
    logger.info("正在关闭应用...")
    
    # 1. 关闭容器资源
    await self.container.shutdown_resources()
    #   ├─ 关闭 HTTP 连接池
    #   └─ 关闭数据库引擎
    
    logger.info("应用已关闭")
```

### 容器资源关闭

```python
async def shutdown_resources(self):
    """容器资源关闭流程"""
    logger.info("开始关闭应用资源...")
    
    # 1. 关闭 HTTP 连接池（先关闭，避免新请求）
    try:
        http = self.http_adapter()
        if http and hasattr(http, 'close'):
            logger.debug("正在关闭 HTTP 连接池...")
            close_result = http.close()
            if asyncio.iscoroutine(close_result):
                await close_result
            logger.info("✓ HTTP 连接池已关闭")
    except Exception as e:
        logger.warning(f"✗ 关闭 HTTP 连接池失败: {e}")
    
    # 2. 关闭数据库引擎（最重要）
    try:
        engine = self.db_engine()
        if engine:
            logger.debug("正在关闭数据库引擎...")
            await engine.dispose()
            logger.info("✓ 数据库引擎已关闭")
    except Exception as e:
        logger.error(f"✗ 关闭数据库引擎失败: {e}")
    
    logger.info("应用资源关闭完成")
```

### 关闭顺序重要性

**为什么先关HTTP，后关数据库？**

1. **HTTP先关闭**：
   - 停止接受新的HTTP请求
   - 避免新请求创建数据库连接
   - 减少数据库关闭时的活跃连接

2. **数据库后关闭**：
   - 等待现有事务完成
   - 确保数据一致性
   - 避免数据丢失

## 中断处理

### Ctrl+C 信号处理

**触发器层处理**：

```python
async def run(self):
    """触发器运行（处理中断）"""
    try:
        await self.setup()
        self._is_running = True
        await self.start()
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
        
    except Exception as e:
        logger.error(f"触发器运行异常: {e}", exc_info=True)
        raise
        
    finally:
        self._is_running = False
        await self.stop()
```

**主程序层处理**：

```python
def main():
    """CLI主程序（处理中断）"""
    try:
        asyncio.run(main_async())
        
    except KeyboardInterrupt:
        logger.info("用户中断，正在退出...")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)
```

### 中断处理流程

```
1. 用户按 Ctrl+C
   ↓
2. Python 抛出 KeyboardInterrupt
   ↓
3. 触发器 run() 捕获异常
   ├─ 记录日志："收到中断信号"
   └─ 进入 finally 块
   ↓
4. 执行 trigger.stop()
   ├─ 停止监听
   └─ 清理触发器资源
   ↓
5. main_async() 中的 finally 块
   └─ app.shutdown()
       ├─ 关闭 HTTP 连接池
       └─ 关闭数据库引擎
   ↓
6. 程序优雅退出
```

## 错误处理

### 启动阶段错误

**常见错误**：
1. `.env` 文件不存在
2. 数据库连接失败
3. 配置参数错误

**处理策略**：
```python
try:
    app = await create_app()
except FileNotFoundError:
    logger.error("配置文件 .env 不存在")
    sys.exit(1)
except ValueError as e:
    logger.error(f"配置错误: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"应用启动失败: {e}", exc_info=True)
    sys.exit(1)
```

### 运行阶段错误

**常见错误**：
1. 网络请求失败
2. 数据库查询失败
3. 业务逻辑错误

**处理策略**：
```python
try:
    await trigger.run()
except KeyError:
    logger.error("新闻源未注册")
except ValueError:
    logger.error("数据验证失败")
except Exception as e:
    logger.error(f"运行异常: {e}", exc_info=True)
    raise
finally:
    await app.shutdown()  # 确保资源被释放
```

### 关闭阶段错误

**常见错误**：
1. HTTP连接池关闭失败
2. 数据库引擎关闭失败

**处理策略**：
- ✅ 每个资源独立捕获异常
- ✅ 记录警告但继续关闭流程
- ✅ 确保所有资源都尝试关闭

```python
# HTTP关闭失败 → 记录警告
try:
    await http.close()
except Exception as e:
    logger.warning(f"HTTP 关闭失败: {e}")  # 仅警告

# 数据库关闭失败 → 记录错误但继续
try:
    await engine.dispose()
except Exception as e:
    logger.error(f"数据库关闭失败: {e}")  # 记录但不中断
```

## 生命周期钩子

### 扩展点

**当前支持的钩子**：
- `create_app()`: 应用创建后
- `trigger.setup()`: 触发器初始化时
- `trigger.start()`: 触发器启动时
- `trigger.stop()`: 触发器停止时
- `app.shutdown()`: 应用关闭时

**扩展示例**：
```python
class CustomApplication(Application):
    async def shutdown(self):
        """自定义关闭逻辑"""
        # 1. 执行自定义清理
        await self._custom_cleanup()
        
        # 2. 调用父类关闭
        await super().shutdown()
    
    async def _custom_cleanup(self):
        """自定义清理逻辑"""
        # 保存状态、发送通知等
        pass
```

## 不同运行模式的生命周期

### 1. 命令行模式（ManualTrigger）

```
启动 → 加载配置 → 执行爬取 → 立即关闭
```

**特点**：
- ✅ 启动快
- ✅ 立即执行任务
- ✅ 任务完成后自动退出

### 2. API模式（APITrigger）

```
启动 → 加载配置 → 启动HTTP服务器 → 等待请求 → 收到中断 → 关闭
```

**特点**：
- ✅ 长期运行
- ✅ 按需执行任务
- ✅ 需要手动中断（Ctrl+C）或系统信号

### 3. 定时任务模式（SchedulerTrigger）

```
启动 → 加载配置 → 启动调度器 → 定时执行任务 → 收到中断 → 关闭
```

**特点**：
- ✅ 长期运行
- ✅ 自动定时执行
- ✅ 需要手动中断或系统信号

### 4. 混合模式（API + Scheduler）

```
启动 → 加载配置 → 启动API和调度器 → 并行运行 → 收到中断 → 关闭
```

**特点**：
- ✅ 长期运行
- ✅ 支持手动触发和自动触发
- ✅ 生产环境推荐

## 资源管理最佳实践

### ✅ DO

1. **总是使用 try/finally**：
   ```python
   app = await create_app()
   try:
       # 业务逻辑
       pass
   finally:
       await app.shutdown()  # 确保执行
   ```

2. **单例资源复用**：
   ```python
   # ✅ 正确：单例，全局复用
   db_engine = providers.Singleton(create_async_engine, ...)
   ```

3. **按顺序关闭资源**：
   ```python
   # ✅ 正确：先HTTP，后数据库
   await http.close()
   await engine.dispose()
   ```

4. **记录关键日志**：
   ```python
   logger.info("应用启动")
   logger.info("应用关闭")
   ```

### ❌ DON'T

1. **忘记关闭资源**：
   ```python
   # ❌ 错误：没有 finally
   app = await create_app()
   await trigger.run()
   # 可能不会执行
   await app.shutdown()
   ```

2. **多次创建单例资源**：
   ```python
   # ❌ 错误：每次都创建新引擎
   engine = create_async_engine(...)
   ```

3. **忽略关闭错误**：
   ```python
   # ❌ 错误：不处理异常
   await engine.dispose()  # 可能失败但没有处理
   ```

## 监控和日志

### 关键指标

**启动阶段**：
- 启动耗时
- 配置加载成功/失败
- 依赖初始化成功/失败

**运行阶段**：
- 任务执行次数
- 任务成功/失败率
- 平均响应时间

**关闭阶段**：
- 关闭耗时
- 资源释放成功/失败

### 日志级别使用

```python
# INFO: 关键生命周期事件
logger.info("应用启动")
logger.info("应用关闭")

# DEBUG: 详细步骤
logger.debug("正在关闭 HTTP 连接池...")
logger.debug("正在关闭数据库引擎...")

# WARNING: 可恢复的错误
logger.warning("HTTP 关闭失败: ...")

# ERROR: 严重错误
logger.error("数据库关闭失败: ...")
```

## 相关记忆

- **应用层概览** → `04-application/README`
- **DI容器** → `04-application/di_container`
- **触发器系统** → `04-application/trigger_system`
- **应用配置** → `04-application/config`