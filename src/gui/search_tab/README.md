# 搜索标签页模块架构说明

## 📁 模块结构

搜索标签页模块已重构为多个专注的子模块，提高了代码的可读性和可维护性。

```
search_tab/
├── __init__.py                # 模块导出
├── search_tab.py              # 主标签页类（整合所有功能）
├── checkbox_dropdown.py       # 复选框下拉菜单组件
├── detail_panel.py            # 图片详情面板
├── canvas_renderer.py         # Canvas渲染器（虚拟化列表）
├── event_handlers.py          # 事件处理器
├── context_menu.py            # 右键上下文菜单
├── batch_tag_editor.py        # 批量标签编辑对话框
├── batch_emotion_editor.py    # 批量情感编辑对话框
├── batch_move_dialog.py       # 批量移动到图源对话框
└── README.md                  # 本文档
```

## 📋 各模块职责

### 1. `search_tab.py` - 主标签页类 (~500行)
- **职责**：整合所有功能，协调各个组件
- **主要功能**：
  - 创建UI布局（搜索条件、标签管理按钮、分页控件）
  - 管理搜索条件和多维度筛选（关键词、情感、图源、收藏、标签）
  - 分页控制和数据加载
  - favorite_cache 管理（从数据库实时加载）
  - 详情面板刷新控制
- **使用**：
  ```python
  from src.gui.search_tab import SearchTab
  
  tab = SearchTab(parent, db)
  ```

### 2. `checkbox_dropdown.py` - 复选框下拉菜单 (~190行)
- **职责**：提供多选下拉菜单控件
- **主要功能**：
  - 下拉菜单显示/隐藏（坐标检测点击外部）
  - 多选状态管理
  - 全选/清空操作
  - 选择变化回调
- **特点**：
  - 独立的通用组件，可复用
  - 使用坐标检测避免FocusOut误关闭
  - 支持延迟关闭（100ms）

### 3. `detail_panel.py` - 详情面板 (~560行)
- **职责**：显示和编辑图片详细信息
- **主要功能**：
  - 显示图片缩略图
  - 显示文件信息（路径、时间、大小等）
  - 编辑OCR文本（可保存）
  - 编辑情绪标签（正向/负向/中性/未分类）
  - 收藏状态切换（爱心按钮）
  - **标签显示和编辑**（彩色标签卡片）
  - 可滚动的详情区域
  - **自动刷新功能**（`refresh()` 方法）
- **交互**：通过回调函数与主类通信
- **新增**：
  - `current_file_path` - 记录当前显示的图片
  - `refresh()` - 重新加载当前图片详情

### 4. `canvas_renderer.py` - Canvas渲染器 (~450行)
- **职责**：高性能虚拟化列表渲染
- **主要功能**：
  - 虚拟化渲染（只渲染可见项）
  - 布局计算（自适应列数）
  - 缩略图加载和缓存
  - 文本截断和换行
  - **复选框渲染**（右上角）
  - **爱心图标渲染**（左上角，根据收藏状态）
  - **标签显示**（底部彩色标签）
  - 悬停高亮效果
  - 选中状态显示（蓝色边框）
- **优化**：使用虚拟化技术，支持大量图片流畅显示

### 5. `event_handlers.py` - 事件处理器 (~260行)
- **职责**：处理用户交互事件
- **主要功能**：
  - 鼠标点击（单击、双击、右键）
  - **Shift/Ctrl 多选**（范围选择和多选）
  - **单击空白取消全选**
  - 鼠标悬停和滚轮
  - 复选框点击处理
  - 爱心图标点击处理
  - **右键菜单触发**
- **解耦**：将事件处理逻辑从主类中分离

### 6. `context_menu.py` - 右键上下文菜单 (~235行)
- **职责**：处理多选图片的批量操作
- **主要功能**：
  - 显示选中图片数量
  - **智能显示收藏/取消收藏按钮**（根据选中项状态）
  - 批量编辑标签（调用 BatchTagEditor）
  - 批量编辑情感（调用 BatchEmotionEditor）
  - 批量转移到图源（调用 BatchMoveDialog）
  - 批量删除（二次确认）
- **特点**：
  - 菜单项根据选中项状态动态显示
  - 所有操作完成后刷新页面

### 7. `batch_tag_editor.py` - 批量标签编辑 (~313行)
- **职责**：批量编辑图片标签
- **主要功能**：
  - 三种操作模式：
    - 添加标签（保留原有标签）
    - 移除标签（仅移除选中的标签）
    - 替换标签（清空原有标签，设置为选中的）
  - 显示所有可用标签（带颜色）
  - **管理标签按钮**（快速打开标签管理器）
  - 全选/全不选标签
  - 应用和取消按钮
- **窗口大小**：550x550（确保所有按钮可见）

### 8. `batch_emotion_editor.py` - 批量情感编辑 (~113行)
- **职责**：批量设置图片情感标签
- **主要功能**：
  - 四种情感选择：正向/负向/中性/未分类
  - 单选按钮选择
  - 应用和取消按钮
- **窗口大小**：450x350（优化布局）

### 9. `batch_move_dialog.py` - 批量移动对话框 (~222行)
- **职责**：将图片批量转移到指定图源
- **主要功能**：
  - 显示所有可用图源
  - 选择目标图源
  - 文件移动操作（处理同名文件）
  - 更新数据库记录
  - 二次确认
- **特点**：
  - 自动处理文件路径
  - 显示操作结果统计

## 🎯 设计优势

### 1. **单一职责原则**
每个模块只负责一个特定领域：
- UI组件（checkbox_dropdown）
- 渲染（canvas_renderer）
- 事件处理（event_handlers）
- 详情显示（detail_panel）
- 批量操作对话框（batch_*）
- 右键菜单（context_menu）
- 整体协调（search_tab）

### 2. **高内聚低耦合**
- 模块内部高度内聚
- 模块间通过清晰的接口通信
- 使用回调函数和依赖注入解耦

### 3. **易于维护**
- 每个文件代码量适中（113~560行）
- 功能职责清晰
- 便于定位和修复问题
- 各模块可独立修改而不影响其他模块

### 4. **易于测试**
- 各模块可以独立测试
- 渲染器和事件处理器可以模拟测试
- 批量操作对话框可以单独验证

### 5. **便于扩展**
- 新增UI组件：添加新的组件文件
- 新增批量操作：创建新的对话框类
- 新增右键菜单项：在 context_menu.py 中添加
- 新增筛选条件：在 search_tab.py 中扩展

## 🔄 数据流

```
用户操作
    ↓
event_handlers.py (处理点击、键盘输入)
    ↓
search_tab.py (更新状态、触发数据加载)
    ↓
database (查询图片数据)
    ↓
canvas_renderer.py (渲染图片列表)
    ↓
detail_panel.py (显示选中图片详情)
```

## 🖱️ 交互流程

### 多选操作
```
1. 用户点击复选框 → event_handlers._toggle_checkbox()
2. 更新 selected_items 集合
3. canvas_renderer 重新渲染显示选中状态
```

### 批量编辑
```
1. 用户右键选中项 → event_handlers.on_right_click()
2. context_menu.show() 显示菜单
3. 用户选择操作 → 打开对应对话框
4. 对话框执行操作 → 调用 refresh_callback
5. search_tab.refresh_page() 刷新页面
6. detail_panel.refresh() 更新详情面板
```

### 标签管理
```
1. 点击"管理标签"按钮 → 打开 TagManagerDialog
2. 创建/编辑/删除标签
3. 关闭对话框 → 刷新标签筛选下拉菜单
4. 在批量编辑中点击"管理标签" → 刷新标签列表
```

## 📊 性能优化

### 虚拟化渲染
- 只渲染可见区域的图片（~20-50张）
- 滚动时动态加载/卸载
- 减少内存占用和渲染时间

### 缩略图缓存
- 使用 PIL 生成缩略图
- 缓存 PhotoImage 对象
- 避免重复加载和转换

### favorite_cache 优化
- 每次 load_page() 从数据库重新加载
- 确保收藏状态始终最新
- 支持混合状态正确显示

### 延迟操作
- 使用 after() 延迟执行非关键操作
- 避免频繁触发重新渲染
- 优化滚动性能

## 🔧 关键技术点

### 1. 坐标检测（checkbox_dropdown.py）
```python
def _on_outside_click(self, event):
    # 获取下拉菜单的绝对坐标
    x1 = self.dropdown.winfo_rootx()
    y1 = self.dropdown.winfo_rooty()
    # 判断点击是否在菜单外
    if not (x1 <= event.x_root <= x2 and y1 <= event.y_root <= y2):
        self._close_dropdown()
```

### 2. 虚拟化渲染（canvas_renderer.py）
```python
def render_visible_items(self):
    # 计算可见范围
    visible_start = scroll_y // row_height
    visible_end = (scroll_y + canvas_height) // row_height
    # 只渲染可见项
    for row in range(visible_start, visible_end + 1):
        self._render_row(row)
```

### 3. 详情面板刷新（detail_panel.py）
```python
def refresh(self):
    if self.current_file_path:
        # 重新加载当前图片
        self.show_image_detail(self.current_file_path)
```

### 4. 智能按钮显示（context_menu.py）
```python
# 检查选中项的收藏状态
need_favorite = any(not cache.get(p, False) for p in items)
need_unfavorite = any(cache.get(p, False) for p in items)
# 根据状态显示相应按钮
if need_favorite:
    menu.add_command("❤ 收藏")
if need_unfavorite:
    menu.add_command("💔 取消收藏")
```

## 📝 使用示例

### 创建搜索标签页
```python
from src.gui.search_tab import SearchTab
from src.core.database import ImageDatabase

db = ImageDatabase("meme_finder.db")
tab = SearchTab(parent_notebook, db)
```

### 自定义回调
```python
def on_favorite_changed(file_path, is_favorite):
    print(f"{file_path} 收藏状态: {is_favorite}")

detail_panel = DetailPanel(
    parent, db, favorite_cache,
    on_favorite_toggle=on_favorite_changed,
    ...
)
```

### 批量操作
```python
# 创建右键菜单
context_menu = ContextMenu(
    parent, db,
    get_selected_items_func=lambda: selected_items,
    get_favorite_cache_func=lambda: favorite_cache,
    refresh_callback=refresh_page
)

# 显示菜单
context_menu.show(event, clicked_item_path)
```
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
