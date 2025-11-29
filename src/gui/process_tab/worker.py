#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多进程/多线程工作函数
负责在子进程中处理图片
"""

import gc
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


def _process_images_in_subprocess(image_list, enable_ocr, enable_sentiment, use_gpu, db_path, max_workers, progress_queue=None):
    """
    在单个子进程中使用多线程处理多张图片
    
    这是一个混合模式：
    - 使用1个子进程隔离主进程内存
    - 在子进程内使用多线程并行处理
    - OCR模型只加载一次，所有线程共享
    - 数据库连接只创建一次，使用锁保护并发访问
    
    Args:
        image_list: 图片信息列表
        enable_ocr: 是否启用OCR
        enable_sentiment: 是否启用情感分析
        use_gpu: 是否使用GPU
        db_path: 数据库路径
        max_workers: 子进程内的线程数
        progress_queue: 进度队列，用于实时更新UI
    
    Returns:
        处理结果列表
    """
    from ...core.database import ImageDatabase
    from ...core.ocr_processor import OCRProcessor
    import logging
    import threading
    
    # 子进程中配置日志
    logging.basicConfig(level=logging.WARNING)
    
    results = []
    ocr_processor = None
    db = None  # 共享数据库实例
    db_lock = threading.Lock()  # 数据库操作锁
    
    try:
        # 初始化共享数据库连接（只创建一次）
        db = ImageDatabase(db_path)
        
        # 在子进程中初始化OCR处理器（只初始化一次）
        if enable_ocr:
            ocr_processor = OCRProcessor(
                use_gpu=use_gpu,
                use_senta=enable_sentiment,
                lazy_load=True
            )
            
            if not ocr_processor.load_ocr_model():
                return [
                    {
                        'success': False,
                        'id': img['id'],
                        'path': img['file_path'],
                        'error': 'OCR模型加载失败'
                    }
                    for img in image_list
                ]
        
        # 定义线程工作函数
        def process_one_image(img_info, index):
            img_id = img_info['id']
            img_path = img_info['file_path']
            
            try:
                if not Path(img_path).exists():
                    result = {
                        'success': False,
                        'id': img_id,
                        'path': img_path,
                        'error': '文件不存在'
                    }
                elif not enable_ocr:
                    # 不启用OCR时直接写入空数据
                    with db_lock:
                        db.update_image_data(
                            image_id=img_id,
                            ocr_text='',
                            filtered_text='',
                            emotion='未处理',
                            pos_score=0.0,
                            neg_score=0.0
                        )
                    
                    result = {
                        'success': True,
                        'id': img_id,
                        'path': img_path,
                        'result': {
                            'ocr_text': '',
                            'filtered_text': '',
                            'emotion': '未处理',
                            'emotion_positive': 0.0,
                            'emotion_negative': 0.0
                        }
                    }
                else:
                    # 使用共享的OCR处理器处理图片
                    ocr_result = ocr_processor.process_image(Path(img_path))
                    
                    # 使用锁保护数据库写入操作
                    with db_lock:
                        db.update_image_data(
                            image_id=img_id,
                            ocr_text=ocr_result['ocr_text'],
                            filtered_text=ocr_result['filtered_text'],
                            emotion=ocr_result['emotion'],
                            pos_score=ocr_result['emotion_positive'],
                            neg_score=ocr_result['emotion_negative']
                        )
                    
                    result = {
                        'success': True,
                        'id': img_id,
                        'path': img_path,
                        'result': ocr_result
                    }
                
                # 发送进度更新到主进程
                if progress_queue:
                    try:
                        progress_queue.put({
                            'type': 'progress',
                            'index': index,
                            'total': len(image_list),
                            'result': result
                        })
                    except Exception:
                        pass
                
                return result
                
            except Exception as e:
                import traceback
                result = {
                    'success': False,
                    'id': img_id,
                    'path': img_path,
                    'error': f"{str(e)}\n{traceback.format_exc()}"
                }
                
                # 即使失败也发送进度更新
                if progress_queue:
                    try:
                        progress_queue.put({
                            'type': 'progress',
                            'index': index,
                            'total': len(image_list),
                            'result': result
                        })
                    except Exception:
                        pass
                
                return result
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_one_image, img, idx): idx 
                      for idx, img in enumerate(image_list, 1)}
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    import traceback
                    results.append({
                        'success': False,
                        'error': f"线程异常: {str(e)}\n{traceback.format_exc()}"
                    })
        
        return results
        
    except Exception as e:
        import traceback
        return [
            {
                'success': False,
                'error': f"子进程异常: {str(e)}\n{traceback.format_exc()}"
            }
            for _ in image_list
        ]
    finally:
        # 清理资源
        try:
            if ocr_processor:
                del ocr_processor
            if db:
                db.close()
                del db
        except Exception:
            pass
        
        # 强制垃圾回收
        gc.collect()


def _process_image_worker(img_info, enable_ocr, enable_sentiment, use_gpu, db_path):
    """
    子进程中处理单张图片的工作函数（保留用于单进程模式）
    
    Args:
        img_info: 图片信息字典
        enable_ocr: 是否启用OCR
        enable_sentiment: 是否启用情感分析
        use_gpu: 是否使用GPU
        db_path: 数据库路径
    
    Returns:
        处理结果字典
    """
    from ...core.database import ImageDatabase
    from ...core.ocr_processor import OCRProcessor
    import logging
    
    # 子进程中重新配置日志（避免与主进程冲突）
    logging.basicConfig(level=logging.WARNING)
    
    img_id = img_info['id']
    img_path = img_info['file_path']
    
    try:
        if not Path(img_path).exists():
            return {
                'success': False,
                'id': img_id,
                'path': img_path,
                'error': '文件不存在'
            }
        
        if not enable_ocr:
            # 不启用OCR时直接写入空数据
            db = ImageDatabase(db_path)
            db.update_image_data(
                image_id=img_id,
                ocr_text='',
                filtered_text='',
                emotion='未处理',
                pos_score=0.0,
                neg_score=0.0
            )
            db.close()
            
            return {
                'success': True,
                'id': img_id,
                'path': img_path,
                'result': {
                    'ocr_text': '',
                    'filtered_text': '',
                    'emotion': '未处理',
                    'emotion_positive': 0.0,
                    'emotion_negative': 0.0
                }
            }
        
        # 初始化OCR处理器
        ocr_processor = OCRProcessor(
            use_gpu=use_gpu,
            use_senta=enable_sentiment,
            lazy_load=True
        )
        
        # 加载OCR模型
        if not ocr_processor.load_ocr_model():
            return {
                'success': False,
                'id': img_id,
                'path': img_path,
                'error': 'OCR模型加载失败'
            }
        
        # 处理图片
        result = ocr_processor.process_image(Path(img_path))
        
        # 更新数据库
        db = ImageDatabase(db_path)
        db.update_image_data(
            image_id=img_id,
            ocr_text=result['ocr_text'],
            filtered_text=result['filtered_text'],
            emotion=result['emotion'],
            pos_score=result['emotion_positive'],
            neg_score=result['emotion_negative']
        )
        db.close()
        
        # 清理OCR处理器
        del ocr_processor
        gc.collect()
        
        return {
            'success': True,
            'id': img_id,
            'path': img_path,
            'result': result
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'id': img_id,
            'path': img_path,
            'error': f"{str(e)}\n{traceback.format_exc()}"
        }
