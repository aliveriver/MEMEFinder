# 数据库模块架构说明

## 📁 模块结构

数据库模块已重构为多个专注的子模块，提高了代码的可读性和可维护性。

```
database/
├── __init__.py              # 模块导出
├── database.py              # 主数据库类（整合所有功能）
├── connection_pool.py       # 数据库连接池管理
├── schema.py                # 数据库表结构和初始化
├── source_manager.py        # 图源管理
├── image_manager.py         # 图片管理
├── search_manager.py        # 搜索和查询功能
├── state_manager.py         # 应用状态管理
└── README.md                # 本文档
```

## 📋 各模块职责

### 1. `database.py` - 主数据库类
- **职责**：整合所有功能，提供统一的对外接口
- **特点**：使用委托模式，将具体功能委托给各个管理器
- **使用**：
  ```python
  from src.core.database import ImageDatabase
  
  db = ImageDatabase("meme_finder.db")
  db.add_source("path/to/images")
  ```

### 2. `connection_pool.py` - 连接池管理
- **职责**：管理SQLite数据库连接池，提供线程安全的连接复用
- **主要功能**：
  - 连接池初始化和管理
  - 线程本地存储，避免跨线程使用连接
  - 连接获取和归还
  - SQLite性能优化（WAL模式、缓存设置等）

### 3. `schema.py` - 表结构管理
- **职责**：定义和初始化数据库表结构
- **主要功能**：
  - 创建所有数据表
  - 创建索引以优化查询性能
  - 表结构集中管理，便于维护

### 4. `source_manager.py` - 图源管理
- **职责**：管理图源文件夹
- **主要功能**：
  - 添加/删除图源
  - 获取图源列表
  - 启用/禁用图源
  - 更新扫描时间

### 5. `image_manager.py` - 图片管理
- **职责**：管理图片数据的增删改查
- **主要功能**：
  - 图片的添加（单个/批量）
  - 获取未处理的图片
  - 更新图片处理结果（批量更新）
  - 更新图片详细信息（OCR文本、收藏状态、情绪标签）
  - 获取图片详情
  - 清理旧数据

### 6. `search_manager.py` - 搜索查询
- **职责**：处理图片搜索和分页查询
- **主要功能**：
  - 关键词搜索
  - 情绪筛选（支持多选）
  - 图源筛选（支持多选）
  - 收藏筛选
  - 分页查询
  - 统计信息

### 7. `state_manager.py` - 状态管理
- **职责**：持久化应用状态
- **主要功能**：
  - 保存应用状态键值对
  - 读取应用状态
  - 用于断点续传等场景

## 🔧 使用示例

### 基本使用
```python
from src.core.database import ImageDatabase

# 初始化数据库
db = ImageDatabase("meme_finder.db", pool_size=5)

# 图源管理
db.add_source("/path/to/images")
sources = db.get_sources()
db.toggle_source(source_id=1, enabled=True)

# 图片管理
db.add_image("/path/to/image.jpg", "hash123", source_id=1)
images = db.get_unprocessed_images(limit=100)

# 搜索功能
results = db.search_images(keyword="搞笑", emotion="正向")
count = db.get_images_count(keyword="搞笑", emotions=["正向", "负向"])
page_data = db.get_images_page(page=1, page_size=20)

# 状态管理
db.set_app_state("last_scan_time", "2025-12-04")
last_scan = db.get_app_state("last_scan_time")

# 关闭数据库
db.close()
```

### 批量操作
```python
# 批量添加图片
images_to_add = [
    ("/path/img1.jpg", "hash1", 1),
    ("/path/img2.jpg", "hash2", 1),
]
added_count = db.add_images_batch(images_to_add)

# 批量更新图片数据
updates = [
    (1, "ocr_text1", "filtered1", "正向", 0.9, 0.1),
    (2, "ocr_text2", "filtered2", "负向", 0.2, 0.8),
]
updated_count = db.update_images_batch(updates)
```

## 🎯 设计优势

1. **单一职责原则**：每个模块只负责一个特定领域的功能
2. **高内聚低耦合**：相关功能集中在同一模块，模块间依赖清晰
3. **易于测试**：各个管理器可以独立测试
4. **便于扩展**：新增功能只需添加新的管理器
5. **代码清晰**：每个文件代码量适中，便于阅读和维护

## 🔄 向后兼容

由于使用了委托模式，`ImageDatabase` 类的对外接口保持不变，所有现有代码无需修改即可使用新的模块结构。

## 📝 维护建议

1. **添加新功能**：考虑是否适合现有管理器，或创建新的管理器
2. **修改功能**：在对应的管理器中修改，保持职责单一
3. **性能优化**：优先考虑批量操作，减少数据库往返次数
4. **日志记录**：所有管理器都使用统一的日志系统

## 🚀 未来改进方向

1. 考虑使用异步数据库操作（aiosqlite）
2. 添加数据库迁移工具
3. 实现更精细的查询缓存
4. 支持数据库分片（大规模数据场景）
