# 搜索标签页模块架构说明

## 📁 模块结构

搜索标签页模块已重构为多个专注的子模块，提高了代码的可读性和可维护性。

```
search_tab/
├── __init__.py              # 模块导出
├── search_tab.py            # 主标签页类（整合所有功能）
├── checkbox_dropdown.py     # 复选框下拉菜单组件
├── detail_panel.py          # 图片详情面板
├── canvas_renderer.py       # Canvas渲染器（虚拟化列表）
├── event_handlers.py        # 事件处理器
└── README.md                # 本文档
```

## 📋 各模块职责

### 1. `search_tab.py` - 主标签页类 (~450行)
- **职责**：整合所有功能，协调各个组件
- **主要功能**：
  - 创建UI布局
  - 管理搜索条件和筛选
  - 分页控制
  - 数据加载和状态管理
- **使用**：
  ```python
  from src.gui.search_tab import SearchTab
  
  tab = SearchTab(parent, db)
  ```

### 2. `checkbox_dropdown.py` - 复选框下拉菜单 (~170行)
- **职责**：提供多选下拉菜单控件
- **主要功能**：
  - 下拉菜单显示/隐藏
  - 多选状态管理
  - 全选/清空操作
  - 选择变化回调
- **特点**：独立的通用组件，可复用

### 3. `detail_panel.py` - 详情面板 (~450行)
- **职责**：显示和编辑图片详细信息
- **主要功能**：
  - 显示图片缩略图
  - 显示文件信息（路径、时间等）
  - 编辑OCR文本
  - 编辑情绪标签
  - 收藏状态切换
  - 可滚动的详情区域
- **交互**：通过回调函数与主类通信

### 4. `canvas_renderer.py` - Canvas渲染器 (~450行)
- **职责**：高性能虚拟化列表渲染
- **主要功能**：
  - 虚拟化渲染（只渲染可见项）
  - 布局计算（自适应列数）
  - 缩略图加载和缓存
  - 文本截断和换行
  - 复选框/爱心图标渲染
  - 悬停高亮效果
- **优化**：使用虚拟化技术，支持大量图片流畅显示

### 5. `event_handlers.py` - 事件处理器 (~250行)
- **职责**：处理用户交互事件
- **主要功能**：
  - 鼠标点击（单击、双击、右键）
  - Shift/Ctrl 多选
  - 鼠标悬停和滚轮
  - 右键菜单（打开、删除、复制路径等）
  - 文件操作（打开图片/文件夹）
- **解耦**：将事件处理逻辑从主类中分离

## 🎯 设计优势

### 1. **单一职责原则**
每个模块只负责一个特定领域：
- UI组件（checkbox_dropdown）
- 渲染（canvas_renderer）
- 事件处理（event_handlers）
- 详情显示（detail_panel）
- 整体协调（search_tab）

### 2. **高内聚低耦合**
- 模块内部高度内聚
- 模块间通过清晰的接口通信
- 使用回调函数解耦

### 3. **易于维护**
- 每个文件代码量适中（170~450行）
- 功能职责清晰
- 便于定位和修复问题

### 4. **易于测试**
- 各模块可以独立测试
- 渲染器和事件处理器可以模拟测试

### 5. **便于扩展**
- 新增UI组件：添加新的组件文件
- 修改渲染逻辑：只需修改 canvas_renderer
- 新增事件：只需修改 event_handlers

## 🔄 模块间通信

### 主类 → 子模块
```python
# 通过构造函数传递依赖
renderer = CanvasRenderer(canvas, thumb_size_var)
detail_panel = DetailPanel(frame, db, favorite_cache, callbacks...)
```

### 子模块 → 主类
```python
# 通过回调函数通信
def on_favorite_toggle(file_path, new_state):
    # 主类处理收藏状态变化
    pass

detail_panel = DetailPanel(..., on_favorite_toggle=on_favorite_toggle)
```

### 模块间协作示例
```
用户点击图片
    ↓
EventHandlers 捕获点击事件
    ↓
判断点击位置（使用 CanvasRenderer 的方法）
    ↓
调用主类的回调函数
    ↓
主类更新数据和状态
    ↓
通知 DetailPanel 显示详情
    ↓
通知 CanvasRenderer 更新显示
```

## 📊 代码行数对比

| 模块 | 行数 | 占比 |
|-----|------|------|
| 原 search_tab.py | ~1800 | 100% |
| 新 search_tab.py | ~450 | 25% |
| checkbox_dropdown.py | ~170 | 9% |
| detail_panel.py | ~450 | 25% |
| canvas_renderer.py | ~450 | 25% |
| event_handlers.py | ~250 | 14% |
| **总计** | **~1770** | **98%** |

**结果**：拆分后总行数略少（得益于去除重复代码），但可读性和维护性大幅提升！

## 🔧 使用示例

### 基本使用
```python
from src.gui.search_tab import SearchTab
from src.core.database import ImageDatabase

# 初始化数据库
db = ImageDatabase("meme_finder.db")

# 创建搜索标签页
search_tab = SearchTab(parent_widget, db)

# 访问主框架
search_tab.frame.pack(fill=tk.BOTH, expand=True)
```

### 从外部设置筛选条件
```python
# 设置图源筛选（从图源页面跳转过来）
search_tab.set_source_filter([1, 2, 3])

# 设置关键词搜索
search_tab.search_keyword.set("搞笑")
search_tab.search_images()
```

### 访问选中的图片
```python
# 获取当前选中的图片路径
selected_paths = search_tab.selected_items

# 获取当前页的所有结果
all_results = search_tab.all_results
```

## 🎨 UI组件层次

```
SearchTab (主类)
├── 搜索条件框架
│   ├── 关键词输入框
│   ├── CheckboxDropdown (情感筛选)
│   ├── CheckboxDropdown (图源筛选)
│   └── 收藏筛选复选框
├── 结果显示区 (PanedWindow)
│   ├── 左侧：图片列表
│   │   ├── Canvas (由 CanvasRenderer 管理)
│   │   └── 滚动条
│   └── 右侧：DetailPanel (详情面板)
└── 分页控件框架
    ├── 每页条数选择
    ├── 缩略图大小滑块
    ├── 上一页/下一页按钮
    └── 跳转输入框
```

## 🚀 性能优化

1. **虚拟化渲染**：只渲染可见区域的图片，支持数千张图片流畅显示
2. **延迟GC**：在清空大量缩略图后延迟垃圾回收，避免UI卡顿
3. **缩略图压缩**：使用JPEG压缩缩略图，减少内存占用
4. **延迟重新加载**：用户调整缩略图大小时，延迟重新加载避免频繁操作

## 📝 维护建议

1. **修改UI布局**：在 `search_tab.py` 的 `_create_*_frame` 方法中修改
2. **修改渲染效果**：在 `canvas_renderer.py` 中修改
3. **新增事件处理**：在 `event_handlers.py` 中添加
4. **修改详情显示**：在 `detail_panel.py` 中修改
5. **新增筛选条件**：在 `search_tab.py` 中添加，可能需要新增 `CheckboxDropdown` 实例

## 🐛 常见问题

### Q: 如何添加新的筛选条件？
A: 在 `_create_search_frame` 中添加UI控件，在 `load_page` 中添加查询参数。

### Q: 如何修改缩略图样式？
A: 修改 `canvas_renderer.py` 中的 `render_visible_items` 方法。

### Q: 如何添加新的右键菜单项？
A: 修改 `event_handlers.py` 中的 `show_context_menu` 方法。

### Q: 详情面板滚动有问题怎么办？
A: 检查 `detail_panel.py` 中的 `_configure_scroll_region` 和 `_configure_canvas_width` 方法。

## 🔗 相关文档

- [数据库模块文档](../../core/database/README.md)
- [主窗口文档](../main_window.py)
- [图源管理文档](../source_tab.py)
