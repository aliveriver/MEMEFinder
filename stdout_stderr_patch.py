"""
标准输出/错误流补丁
在打包环境中修复 sys.stdout/sys.stderr 为 None 导致的问题
"""

import sys
import io


class DummyFile:
    """虚拟文件对象，用于替代 None 的 stdout/stderr"""
    
    def __init__(self):
        self.closed = False
        self.mode = 'w'
        self.encoding = 'utf-8'
        self.errors = 'strict'
        self.newlines = None
        self.line_buffering = False
        self.buffer = None
    
    def write(self, s):
        """写入操作（静默处理，避免错误）"""
        # 在打包环境中，我们不输出到控制台
        # 如果需要，可以写入日志文件
        pass
    
    def flush(self):
        """刷新操作"""
        pass
    
    def close(self):
        """关闭操作"""
        self.closed = True
    
    def isatty(self):
        """检查是否是终端"""
        return False
    
    def readable(self):
        """是否可读"""
        return False
    
    def writable(self):
        """是否可写"""
        return True
    
    def seekable(self):
        """是否可定位"""
        return False
    
    def fileno(self):
        """返回文件描述符（虚拟）"""
        return -1
    
    def read(self, size=-1):
        """读取操作"""
        raise io.UnsupportedOperation('read')
    
    def readline(self, size=-1):
        """读取一行"""
        raise io.UnsupportedOperation('readline')
    
    def readlines(self, hint=-1):
        """读取所有行"""
        raise io.UnsupportedOperation('readlines')
    
    def seek(self, offset, whence=0):
        """定位操作"""
        raise io.UnsupportedOperation('seek')
    
    def tell(self):
        """返回当前位置"""
        return 0
    
    def truncate(self, size=None):
        """截断操作"""
        raise io.UnsupportedOperation('truncate')


def patch_stdout_stderr():
    """修复打包环境中 sys.stdout/sys.stderr 为 None 的问题"""
    
    # 检查是否是打包环境
    is_frozen = getattr(sys, "frozen", False)
    
    # 在打包环境中，设置环境变量禁用 tqdm 进度条（避免 stdout/stderr 问题）
    if is_frozen:
        import os
        os.environ['TQDM_DISABLE'] = '1'
        os.environ['TQDM_MININTERVAL'] = '999999'  # 设置一个很大的最小间隔，实际上禁用更新
    
    # 即使不是打包环境，也检查并修复 None 的情况
    if sys.stdout is None:
        sys.stdout = DummyFile()
        print("[补丁] sys.stdout 为 None，已创建虚拟文件对象", file=sys.stderr if sys.stderr else None)
    
    if sys.stderr is None:
        sys.stderr = DummyFile()
        # 注意：此时不能使用 print，因为 stdout 可能也是 None
        # 但我们已经修复了 stdout，所以可以安全使用
        try:
            print("[补丁] sys.stderr 为 None，已创建虚拟文件对象", file=sys.stderr)
        except:
            pass
    
    # 同时修复 tqdm 可能遇到的问题
    patch_tqdm()


def patch_tqdm():
    """修复 tqdm 在打包环境中的问题"""
    
    # tqdm 在初始化时会检查 sys.stdout/sys.stderr
    try:
        import tqdm
        import tqdm.std
        
        # 确保 tqdm.std 使用有效的流
        if tqdm.std.sys is None or tqdm.std.sys.stdout is None:
            import sys as sys_module
            tqdm.std.sys = sys_module
        
        # 修复 tqdm.std.tqdm 的初始化
        original_tqdm_init = tqdm.std.tqdm.__init__
        
        def patched_tqdm_init(self, *args, **kwargs):
            """修复后的 tqdm 初始化"""
            # 确保 file 参数不是 None
            if 'file' not in kwargs or kwargs.get('file') is None:
                kwargs['file'] = sys.stdout if sys.stdout is not None else DummyFile()
            
            # 确保 disable 参数设置正确（在打包环境中禁用进度条可能更好）
            if getattr(sys, "frozen", False):
                # 在打包环境中，默认禁用进度条以避免问题
                if 'disable' not in kwargs:
                    kwargs['disable'] = True
            
            try:
                return original_tqdm_init(self, *args, **kwargs)
            except (AttributeError, OSError) as e:
                # 如果还是失败，禁用进度条并重试
                if 'write' in str(e) or 'NoneType' in str(e):
                    kwargs['disable'] = True
                    kwargs['file'] = DummyFile()
                    return original_tqdm_init(self, *args, **kwargs)
                else:
                    raise
        
        tqdm.std.tqdm.__init__ = patched_tqdm_init
        
        # 修复 tqdm.asyncio 模块
        try:
            import tqdm.asyncio as tqdm_asyncio
            # tqdm.asyncio.tqdm 继承自 tqdm.std.tqdm，所以上面的修复应该已经生效
        except ImportError:
            pass
        except Exception:
            pass
        
    except ImportError:
        pass  # tqdm 未安装，忽略
    except Exception as e:
        # 其他错误也忽略，不影响主程序
        pass


def patch_paddlex_download():
    """修复 PaddleX 下载函数中的 sys.stderr.write 问题"""
    
    try:
        import paddlex.utils.download as download_module
    except ImportError:
        return  # PaddleX 未安装，忽略
    
    # 修复 download.py 中的 Printer 类
    if hasattr(download_module, 'Printer'):
        original_print = download_module.Printer.print
        
        def patched_print(self, *args, **kwargs):
            """修复后的 print 方法"""
            try:
                return original_print(self, *args, **kwargs)
            except (AttributeError, OSError) as e:
                # 如果 sys.stderr.write 失败，静默处理
                if 'write' in str(e) or 'NoneType' in str(e):
                    pass  # 静默忽略
                else:
                    raise
        
        download_module.Printer.print = patched_print
    
    # 修复 download.py 中的 _download 函数
    if hasattr(download_module, '_download'):
        original_download = download_module._download
        
        def patched_download(*args, **kwargs):
            """修复后的下载函数"""
            try:
                return original_download(*args, **kwargs)
            except (AttributeError, OSError) as e:
                # 如果遇到 stdout/stderr 相关的错误，尝试继续
                if 'write' in str(e) or 'NoneType' in str(e):
                    # 设置 print_progress=False 重试
                    kwargs['print_progress'] = False
                    try:
                        return original_download(*args, **kwargs)
                    except:
                        # 如果还是失败，返回 None 或抛出更友好的错误
                        raise Exception("模型下载失败：无法访问输出流。请检查网络连接或使用本地模型文件。")
                else:
                    raise
        
        download_module._download = patched_download


def patch_paddlex_official_models():
    """修复 PaddleX official_models 中的下载问题"""
    
    try:
        import paddlex.inference.utils.official_models as official_models_module
    except ImportError:
        return  # PaddleX 未安装，忽略
    
    # 修复 _download_from_hoster 方法，使其在遇到 stdout/stderr 错误时能够继续
    if hasattr(official_models_module, 'OfficialModels'):
        original_getitem = official_models_module.OfficialModels.__getitem__
        
        def patched_getitem(self, model_name):
            """修复后的 __getitem__ 方法"""
            try:
                return original_getitem(self, model_name)
            except Exception as e:
                # 如果是 stdout/stderr 相关的错误，尝试禁用进度条后重试
                if 'write' in str(e) or 'NoneType' in str(e) or 'AttributeError' in str(type(e).__name__):
                    # 设置环境变量禁用进度条
                    import os
                    os.environ['TQDM_DISABLE'] = '1'
                    try:
                        return original_getitem(self, model_name)
                    except:
                        # 如果还是失败，抛出更友好的错误
                        raise Exception(
                            f"模型下载失败：无法访问输出流。\n"
                            f"请检查网络连接或使用本地模型文件。\n"
                            f"模型名称: {model_name}"
                        )
                else:
                    raise
        
        official_models_module.OfficialModels.__getitem__ = patched_getitem


def apply_all_patches():
    """应用所有补丁"""
    patch_stdout_stderr()
    patch_paddlex_download()
    patch_paddlex_official_models()


# 自动应用补丁
if __name__ != "__main__":
    apply_all_patches()

