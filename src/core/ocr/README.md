# OCR 模块文档

## 模块概述

OCR 模块是 MEMEFinder 的核心功能模块，负责从图片中提取文字、分析文本情绪，并提供完整的图片处理流水线。

### 设计理念

本模块采用**模块化设计**，将复杂的 OCR 处理流程分解为独立的、职责单一的组件：

- **OCR 引擎** - 专注于文字识别
- **文本处理器** - 专注于文本提取和清洗
- **情感分析器** - 专注于情绪判断
- **处理器** - 协调和整合各组件

这种设计提高了代码的可维护性、可测试性和可扩展性。

---

## 模块架构

```
src/core/ocr/
├── __init__.py              # 模块初始化
├── ocr_engine.py            # OCR 引擎（RapidOCR 封装）
├── processor.py             # OCR 处理器（主入口）
├── sentiment_analyzer.py    # 情感分析
└── text_processor.py        # 文本处理
```

### 数据流

```
图片输入
    ↓
[OCR Engine] ← 识别文字
    ↓
[Text Processor] ← 提取和过滤文本
    ↓
[Sentiment Analyzer] ← 分析情绪
    ↓
结果输出 {ocr_text, filtered_text, emotion, scores}
```

---

## 模块详解

### 1. OCR Engine (`ocr_engine.py`)

**职责**：封装 RapidOCR 库，提供文字识别功能

**核心类**：`OCREngine`

**主要功能**：
- ✅ GPU 加速支持（CUDA/DirectML）
- ✅ CPU 模式自动回退
- ✅ 图像预处理（Padding 外扩）
- ✅ 坐标系转换

**关键方法**：

```python
class OCREngine:
    def __init__(self, use_gpu: bool, model_dir: Path):
        """
        初始化 OCR 引擎
        
        Args:
            use_gpu: 是否使用 GPU
            model_dir: 模型文件目录
        """
    
    def initialize(self) -> bool:
        """初始化 RapidOCR，返回是否成功"""
    
    def recognize(self, img_input) -> Dict[str, Any]:
        """
        单张图片 OCR 识别
        
        Args:
            img_input: PIL Image 对象或图片路径
            
        Returns:
            {
                "image": "图片路径",
                "items": [
                    {"box": [[x,y]×4], "text": "...", "score": 0.xx},
                    ...
                ]
            }
        """
    
    def process_with_padding(self, image_path: Path, pad_ratio: float = 0.10):
        """
        带画布外扩的 OCR 识别（提高边缘文字识别率）
        
        Args:
            image_path: 图片路径
            pad_ratio: 外扩比例（默认 10%）
        """
```

**配置选项**：
- `use_gpu`: 是否使用 GPU
- `model_dir`: 模型文件目录
- `pad_ratio`: 画布外扩比例（提高边缘识别率）

---

### 2. Text Processor (`text_processor.py`)

**职责**：从 OCR 结果中提取和清洗文本

**核心类**：`TextProcessor`（静态方法类）

**主要功能**：
- ✅ 文本提取
- ✅ 网址过滤
- ✅ 水印关键词过滤
- ✅ 特殊符号清理

**关键方法**：

```python
class TextProcessor:
    @staticmethod
    def extract_text(ocr_result: List[Dict[str, Any]]) -> str:
        """
        从 OCR 结果中提取文本
        
        Args:
            ocr_result: OCR 识别结果列表
            
        Returns:
            提取的文本字符串
        """
    
    @staticmethod
    def filter_text(text: str) -> str:
        """
        过滤水印和网址
        
        规则：
        1. 过滤网址（http, https, www, .com, .cn等）
        2. 过滤常见水印词汇（微信、抖音、小红书等）
        3. 过滤特殊符号
        
        Args:
            text: 原始文本
            
        Returns:
            过滤后的文本
        """
```

**过滤规则**：
- **网址**: `http://`, `https://`, `www.`, `.com`, `.cn` 等
- **水印**: 微信, 抖音, 快手, 小红书, TikTok 等
- **符号**: 多余空格, 连续下划线/横线等

---

### 3. Sentiment Analyzer (`sentiment_analyzer.py`)

**职责**：分析文本情绪倾向

**核心类**：`SentimentAnalyzer`

**主要功能**：
- ✅ 多引擎支持（SnowNLP / TextBlob / 关键词匹配）
- ✅ 懒加载优化
- ✅ 自动降级策略

**关键方法**：

```python
class SentimentAnalyzer:
    def __init__(self, use_senta: bool = True):
        """
        初始化情感分析器
        
        Args:
            use_senta: 是否使用深度学习模型（SnowNLP）
        """
    
    def analyze(self, text: str) -> Tuple[str, float, float]:
        """
        情感分析
        
        Args:
            text: 文本内容
            
        Returns:
            (emotion, pos_score, neg_score)
            emotion: '正向', '负向', '中性', '未分类'
        """
```

**分析引擎**：
1. **SnowNLP**（中文，首选）
   - 目标分数：0.0-1.0
   - 分类阈值：>0.6 正向，<0.4 负向，其他中性
   - 懒加载，首次使用时加载

2. **TextBlob**（英文，备选）
   - Polarity: -1.0 到 1.0
   - 分类阈值：>0.2 正向，<-0.2 负向

3. **关键词匹配**（回退方案）
   - 基于预定义的正面/负面关键词
   - 适用于所有语言

---

### 4. Processor (`processor.py`)

**职责**：整合各组件，提供统一的处理接口

**核心类**：`OCRProcessor`

**主要功能**：
- ✅ 完整的处理流水线
- ✅ 延迟加载模型
- ✅ GPU 自动检测
- ✅ 资源监控
- ✅ 向后兼容接口

**关键方法**：

```python
class OCRProcessor:
    def __init__(
        self, 
        lang: str = 'ch', 
        use_gpu: Optional[bool] = None,
        det_side: int = 1536, 
        use_senta: bool = True,
        model_dir: Optional[Path] = None, 
        lazy_load: bool = False
    ):
        """
        初始化 OCR 处理器
        
        Args:
            lang: 语言，默认 'ch'（中文）
            use_gpu: 是否使用 GPU，None 表示自动检测
            det_side: 检测侧边长度，默认 1536
            use_senta: 是否使用情感分析，默认 True
            model_dir: 模型目录，None 使用默认
            lazy_load: 是否延迟加载（推荐）
        """
    
    def process_image(
        self, 
        image_path: Path, 
        pad_ratio: float = 0.10
    ) -> Dict[str, Any]:
        """
        处理单张图片（主入口）
        
        Args:
            image_path: 图片路径
            pad_ratio: 画布外扩比例，默认 0.10
            
        Returns:
            {
                'ocr_text': str,           # 原始 OCR 文本
                'filtered_text': str,      # 过滤后的文本
                'emotion': str,            # 情绪类别
                'emotion_positive': float, # 正向分数
                'emotion_negative': float  # 负向分数
            }
        """
```

---

## 使用示例

### 基础使用

```python
from pathlib import Path
from src.core.ocr.processor import OCRProcessor

# 1. 创建处理器（推荐延迟加载）
processor = OCRProcessor(
    lang='ch',           # 中文
    use_gpu=None,        # 自动检测 GPU
    use_senta=True,      # 启用情感分析
    lazy_load=True       # 延迟加载（节省内存）
)

# 2. 处理图片
image_path = Path("path/to/image.jpg")
result = processor.process_image(image_path)

# 3. 使用结果
print(f"识别文本: {result['ocr_text']}")
print(f"过滤文本: {result['filtered_text']}")
print(f"情绪: {result['emotion']}")
print(f"正向分数: {result['emotion_positive']:.2f}")
print(f"负向分数: {result['emotion_negative']:.2f}")
```

### 高级配置

```python
# GPU 加速（手动指定）
processor_gpu = OCRProcessor(
    use_gpu=True,        # 强制使用 GPU
    det_side=2048,       # 更大的检测尺寸
    lazy_load=False      # 立即加载模型
)

# 仅 OCR，不分析情绪
processor_ocr_only = OCRProcessor(
    use_senta=False      # 禁用情感分析
)

# 带外扩的识别（提高边缘文字识别率）
result = processor.process_image(
    image_path,
    pad_ratio=0.15       # 15% 外扩
)
```

### 批量处理

```python
from pathlib import Path
from src.core.ocr.processor import OCRProcessor

processor = OCRProcessor(lazy_load=True)

# 批量处理图片
image_folder = Path("path/to/images")
results = []

for img_path in image_folder.glob("*.jpg"):
    try:
        result = processor.process_image(img_path)
        results.append(result)
        print(f"✓ {img_path.name}: {result['emotion']}")
    except Exception as e:
        print(f"✗ {img_path.name}: {e}")

print(f"处理完成：{len(results)} 张图片")
```

---

## 配置说明

### GPU 配置

**自动检测**（推荐）：
```python
processor = OCRProcessor(use_gpu=None)  # 自动检测
```

**手动指定**：
```python
processor = OCRProcessor(use_gpu=True)   # 强制 GPU
processor = OCRProcessor(use_gpu=False)  # 强制 CPU
```

**检测逻辑**：
1. 检查是否安装 `onnxruntime-gpu`
2. 检查NVIDIA GPU 是否可用
3. 检查 CUDA 运行时是否存在
4. 自动回退到 CPU（如果任一条件不满足）

### 模型配置

**默认模型目录**：
- 开发环境: `项目根目录/models/`
- 打包环境: `sys._MEIPASS/models/`

**自定义模型目录**：
```python
processor = OCRProcessor(
    model_dir=Path("/custom/path/to/models")
)
```

### 内存优化

**延迟加载**（推荐）：
```python
processor = OCRProcessor(lazy_load=True)
# 模型在首次调用 process_image() 时才加载
```

**立即加载**：
```python
processor = OCRProcessor(lazy_load=False)
# 初始化时立即加载模型
```

---

## 性能优化建议

### 1. 使用 GPU 加速
- 安装 `onnxruntime-gpu`
- 确保系统有 NVIDIA GPU 和 CUDA 运行时
- 速度提升：2-5 倍

### 2. 延迟加载模型
- 设置 `lazy_load=True`
- 节省初始内存：~385MB（SnowNLP）

### 3. 调整检测尺寸
- 默认：1536（平衡速度和精度）
- 快速：1024（速度优先）
- 精确：2048（精度优先）

### 4. 批量处理
- 复用同一个 `OCRProcessor` 实例
- 避免重复初始化模型

---

## 常见问题

### Q1: 如何提高边缘文字识别率？

**A**: 使用画布外扩功能：
```python
result = processor.process_image(image_path, pad_ratio=0.15)
```

### Q2: 情感分析不准确怎么办？

**A**: 
1. 检查是否安装了 SnowNLP：`pip install snownlp`
2. 使用关键词匹配作为回退：设置 `use_senta=False`
3. 考虑使用自定义情感词典

### Q3: GPU 加速不工作？

**A**: 检查以下条件：
1. 安装 `onnxruntime-gpu`：`pip install onnxruntime-gpu`
2. 安装 CUDA 运行时（11.x 或 12.x）
3. 确认 NVIDIA GPU 驱动正常
4. 查看日志了解具体错误

### Q4: 内存占用过高？

**A**:
1. 使用延迟加载：`lazy_load=True`
2. 禁用情感分析：`use_senta=False`
3. 处理后手动清理：`import gc; gc.collect()`

---

## 向后兼容

为保持与旧代码的兼容性，`OCRProcessor` 提供了以下属性：

```python
# 旧代码（仍然支持）
processor.ocr              # 访问 OCR 引擎
processor.filter_text()    # 文本过滤
processor.analyze_emotion() # 情感分析

# 新代码（推荐）
processor.process_image()  # 完整流水线
```

---

## 相关文档

- [项目概述](../../../docs/项目概述.md)
- [主 README](../../../README.md)
- [数据库模块](../database.py)
- [工具模块](../../utils/)

---

*最后更新: 2025-11-29*
