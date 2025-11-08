#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR调试测试 - 查看原始OCR返回结果
"""

import sys
from pathlib import Path
import json

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from paddleocr import PaddleOCR


def test_paddle_ocr_direct():
    """直接测试PaddleOCR"""
    print("=" * 60)
    print("PaddleOCR 直接测试")
    print("=" * 60)
    
    # 初始化OCR
    print("\n初始化PaddleOCR...")
    ocr = PaddleOCR(
        lang='ch',
        use_textline_orientation=True,
        use_doc_orientation_classify=True,
        use_doc_unwarping=True,
        text_det_limit_side_len=1536,
        text_det_limit_type="max",
        text_det_box_thresh=0.30,
        text_det_unclip_ratio=2.30
    )
    print("✓ 初始化完成\n")
    
    # 测试图片
    imgs_dir = Path("./imgs")
    test_images = list(imgs_dir.glob("*.jpg"))[:3]
    
    for idx, img_path in enumerate(test_images, 1):
        print(f"\n{'='*60}")
        print(f"[{idx}] {img_path.name}")
        print('='*60)
        
        try:
            # OCR识别 (新版本使用predict)
            result = ocr.predict(str(img_path))
            
            print(f"\n原始返回结果类型: {type(result)}")
            
            if result and isinstance(result, dict):
                print(f"\n字典键: {result.keys()}")
                
                # 提取文本
                if 'rec_texts' in result:
                    texts = result.get('rec_texts', [])
                    scores = result.get('rec_scores', [])
                    print(f"\n识别到 {len(texts)} 行文本:")
                    for i, (text, score) in enumerate(zip(texts, scores)):
                        print(f"  [{i+1}] {text} (置信度: {score:.2f})")
                else:
                    print(f"\n完整结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
            else:
                print("  (无文本或格式未知)")
                
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_paddle_ocr_direct()
