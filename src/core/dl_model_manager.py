#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
深度学习模型管理模块

负责MobileNetV3-Small模型的下载、验证和管理。
模型大小约2-3MB，适合集成到应用中。
"""

import requests
from pathlib import Path
from typing import Optional, Tuple
import hashlib
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger()


class DLModelManager:
    """深度学习模型管理器"""
    
    # 模型配置
    MODEL_NAME = "mobilenetv3_small_feature.onnx"
    MODEL_DOWNLOAD_URLS = [
        # 主下载源（ONNX Model Zoo - GitHub LFS）
        "https://github.com/onnx/models/raw/main/vision/classification/mobilenet/model/mobilenetv3-small-1.0.onnx",
        # 备用源1（直接链接）
        "https://media.githubusercontent.com/media/onnx/models/main/vision/classification/mobilenet/model/mobilenetv3-small-1.0.onnx",
        # 备用源2（Hugging Face镜像）
        "https://huggingface.co/onnx/mobilenet_v3_small/resolve/main/mobilenetv3-small-1.0.onnx",
    ]
    
    # 模型MD5校验（可选，用于验证完整性）
    MODEL_MD5 = None  # 首次下载后可以记录
    
    def __init__(self, models_dir: Path):
        """
        初始化模型管理器
        
        Args:
            models_dir: 模型存储目录
        """
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.models_dir / self.MODEL_NAME
    
    def is_model_available(self) -> bool:
        """
        检查模型是否已下载且可用
        
        Returns:
            模型是否可用
        """
        if not self.model_path.exists():
            return False
        
        # 检查文件大小（至少应该大于500KB）
        if self.model_path.stat().st_size < 500 * 1024:
            logger.warning(f"模型文件大小异常: {self.model_path.stat().st_size} bytes")
            return False
        
        return True
    
    def download_model(self, callback=None) -> Tuple[bool, str]:
        """
        下载模型文件
        
        Args:
            callback: 进度回调函数 callback(downloaded_bytes, total_bytes)
            
        Returns:
            (是否成功, 消息)
        """
        if self.is_model_available():
            return True, "模型已存在"
        
        logger.info(f"开始下载MobileNetV3-Small模型到: {self.model_path}")
        
        # 尝试所有下载源
        for idx, url in enumerate(self.MODEL_DOWNLOAD_URLS):
            try:
                logger.info(f"尝试下载源 {idx + 1}/{len(self.MODEL_DOWNLOAD_URLS)}: {url}")
                
                # 发起请求
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                # 获取文件大小
                total_size = int(response.headers.get('content-length', 0))
                logger.info(f"模型大小: {total_size / 1024 / 1024:.2f} MB")
                
                # 下载文件
                downloaded_size = 0
                chunk_size = 8192
                
                with open(self.model_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # 调用进度回调
                            if callback:
                                callback(downloaded_size, total_size)
                
                logger.info(f"✓ 模型下载完成: {self.model_path}")
                
                # 验证文件
                if self.is_model_available():
                    return True, "模型下载成功"
                else:
                    self.model_path.unlink(missing_ok=True)
                    raise Exception("下载的模型文件无效")
                    
            except Exception as e:
                logger.warning(f"下载源 {idx + 1} 失败: {e}")
                self.model_path.unlink(missing_ok=True)
                continue
        
        # 所有下载源都失败
        error_msg = "所有下载源均失败，请检查网络连接或手动下载模型"
        logger.error(error_msg)
        return False, error_msg
    
    def verify_model(self) -> bool:
        """
        验证模型完整性
        
        Returns:
            模型是否有效
        """
        if not self.is_model_available():
            return False
        
        # 如果有MD5校验值，进行校验
        if self.MODEL_MD5:
            try:
                md5 = hashlib.md5()
                with open(self.model_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        md5.update(chunk)
                
                calculated_md5 = md5.hexdigest()
                if calculated_md5 != self.MODEL_MD5:
                    logger.error(f"模型MD5校验失败: {calculated_md5} != {self.MODEL_MD5}")
                    return False
                
                logger.info("✓ 模型MD5校验通过")
            except Exception as e:
                logger.error(f"MD5校验失败: {e}")
                return False
        
        return True
    
    def get_model_path(self) -> Optional[Path]:
        """
        获取模型路径
        
        Returns:
            模型路径，如果模型不可用则返回None
        """
        if self.is_model_available():
            return self.model_path
        return None
    
    def delete_model(self) -> bool:
        """
        删除模型文件
        
        Returns:
            是否删除成功
        """
        try:
            if self.model_path.exists():
                self.model_path.unlink()
                logger.info(f"已删除模型: {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"删除模型失败: {e}")
            return False
    
    def get_model_info(self) -> dict:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        info = {
            'name': self.MODEL_NAME,
            'path': str(self.model_path),
            'exists': self.model_path.exists(),
            'size': 0,
            'size_mb': 0.0
        }
        
        if self.model_path.exists():
            size = self.model_path.stat().st_size
            info['size'] = size
            info['size_mb'] = size / 1024 / 1024
        
        return info


# 使用说明和手动下载指引
MANUAL_DOWNLOAD_GUIDE = """
=== MobileNetV3-Small 模型手动下载指南 ===

如果自动下载失败，您可以手动下载模型：

方法1：从GitHub下载（推荐）
1. 访问: https://github.com/onnx/models/tree/main/vision/classification/mobilenet
2. 找到并下载: mobilenetv3-small-1.0.onnx 
3. 将文件重命名为: mobilenetv3_small_feature.onnx
4. 放置到: models/ 目录下

方法2：使用替代模型
如果上述下载失败，可以使用其他轻量级模型：
- EfficientNet-Lite0: https://github.com/onnx/models/tree/main/vision/classification/efficientnet-lite4
- SqueezeNet: https://github.com/onnx/models/tree/main/vision/classification/squeezenet

方法3：网盘下载
请联系开发者获取网盘分享链接

模型大小约2-3MB，下载完成后重启应用即可。
"""


if __name__ == "__main__":
    # 测试模型管理器
    models_dir = Path(__file__).parent.parent.parent / "models"
    manager = DLModelManager(models_dir)
    
    print("模型信息:", manager.get_model_info())
    
    if not manager.is_model_available():
        print("\n正在下载模型...")
        success, msg = manager.download_model(
            callback=lambda d, t: print(f"\r下载进度: {d/1024/1024:.1f}/{t/1024/1024:.1f} MB", end="")
        )
        print(f"\n{msg}")
        
        if not success:
            print(MANUAL_DOWNLOAD_GUIDE)
    else:
        print("✓ 模型已就绪")
