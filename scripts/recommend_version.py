"""
自动检测CUDA版本并推荐合适的MEMEFinder版本

使用方法:
    python scripts/recommend_version.py
"""

import subprocess
import re
import sys
from pathlib import Path

class VersionRecommender:
    """版本推荐器"""
    
    def __init__(self):
        self.has_nvidia = False
        self.cuda_version = None
        self.driver_version = None
        
    def detect_nvidia_gpu(self):
        """检测NVIDIA GPU"""
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.has_nvidia = True
                output = result.stdout
                
                # 提取CUDA版本
                cuda_match = re.search(r"CUDA Version:\s+(\d+\.\d+)", output)
                if cuda_match:
                    self.cuda_version = cuda_match.group(1)
                
                # 提取驱动版本
                driver_match = re.search(r"Driver Version:\s+(\d+\.\d+)", output)
                if driver_match:
                    self.driver_version = driver_match.group(1)
                
                return True
            else:
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_cuda_major_version(self):
        """获取CUDA主版本号"""
        if self.cuda_version:
            major = int(float(self.cuda_version))
            return major
        return None
    
    def recommend_version(self):
        """推荐版本"""
        print("="*60)
        print("MEMEFinder 版本推荐工具")
        print("="*60)
        print()
        
        # 检测GPU
        print("🔍 正在检测您的系统...")
        self.detect_nvidia_gpu()
        
        print(f"\n📊 检测结果:")
        print(f"   NVIDIA GPU: {'✅ 已检测到' if self.has_nvidia else '❌ 未检测到'}")
        
        if self.has_nvidia:
            print(f"   驱动版本: {self.driver_version or '未知'}")
            print(f"   CUDA版本: {self.cuda_version or '未知'}")
        
        print()
        print("="*60)
        print("📌 推荐版本:")
        print("="*60)
        print()
        
        if not self.has_nvidia:
            # 无NVIDIA GPU
            print("✅ 推荐使用: CPU通用版")
            print()
            print("原因:")
            print("  - 未检测到NVIDIA显卡")
            print("  - CPU版本兼容性最好，适合所有用户")
            print()
            print("特点:")
            print("  ✓ 无需GPU，稳定可靠")
            print("  ✓ 兼容所有Windows系统")
            print("  ✓ 识别速度适中")
            
        else:
            cuda_major = self.get_cuda_major_version()
            
            if cuda_major is None:
                # 有GPU但无法确定CUDA版本
                print("⚠️ 推荐使用: CPU通用版 (安全选择)")
                print()
                print("原因:")
                print("  - 检测到NVIDIA显卡，但无法确定CUDA版本")
                print("  - CPU版本更稳定")
                print()
                print("如果您确定CUDA版本，可以选择:")
                print("  • CUDA 11.x → GPU-CUDA11版本")
                print("  • CUDA 12.x → GPU-CUDA12版本")
                
            elif cuda_major >= 12:
                # CUDA 12.x
                print("✅ 推荐使用: GPU加速版 (CUDA 12.x)")
                print()
                print("原因:")
                print(f"  - 您的CUDA版本: {self.cuda_version}")
                print("  - 支持最新的GPU特性")
                print()
                print("特点:")
                print("  ✓ 识别速度最快")
                print("  ✓ 适合RTX 30/40系列显卡")
                print("  ✓ GPU加速，大幅提升性能")
                print()
                print("备选:")
                print("  • 如遇问题可使用 CPU通用版")
                
            elif cuda_major == 11:
                # CUDA 11.x
                print("✅ 推荐使用: GPU加速版 (CUDA 11.x)")
                print()
                print("原因:")
                print(f"  - 您的CUDA版本: {self.cuda_version}")
                print("  - 兼容CUDA 11系列")
                print()
                print("特点:")
                print("  ✓ 识别速度快")
                print("  ✓ 适合GTX 10/16/20系列显卡")
                print("  ✓ GPU加速，性能优秀")
                print()
                print("备选:")
                print("  • 如遇问题可使用 CPU通用版")
                
            else:
                # CUDA版本过旧
                print("⚠️ 推荐使用: CPU通用版")
                print()
                print("原因:")
                print(f"  - 您的CUDA版本: {self.cuda_version}")
                print("  - CUDA版本较旧，可能不兼容")
                print()
                print("建议:")
                print("  • 更新NVIDIA驱动到最新版本")
                print("  • 或使用CPU版本（稳定可靠）")
        
        print()
        print("="*60)
        print()
        
        # GPU性能说明
        if self.has_nvidia and self.cuda_version:
            print("💡 性能对比:")
            print("   CPU版本:  约 2-3秒/图片")
            print("   GPU版本:  约 0.5-1秒/图片 (快3-5倍)")
            print()
        
        print("📥 下载建议:")
        print("   1. 下载推荐版本")
        print("   2. 解压到任意目录")
        print("   3. 运行 MEMEFinder_xxx.exe")
        print()
        
        print("🔧 如果遇到问题:")
        print("   • GPU版本闪退 → 使用CPU版本")
        print("   • 查看 版本说明.txt 了解详情")
        print("   • 查看 logs 目录下的日志文件")
        print()
        
        return self.has_nvidia, self.cuda_version
    
    def create_download_guide(self):
        """创建下载指南"""
        guide_file = Path("推荐版本.txt")
        
        content = f"""
MEMEFinder 推荐版本
{'='*60}

根据您的系统检测结果:

NVIDIA GPU: {'✅ 已检测到' if self.has_nvidia else '❌ 未检测到'}
"""
        
        if self.has_nvidia:
            content += f"驱动版本: {self.driver_version or '未知'}\n"
            content += f"CUDA版本: {self.cuda_version or '未知'}\n"
        
        content += f"\n{'='*60}\n\n"
        
        if not self.has_nvidia:
            content += "推荐下载: MEMEFinder_cpu.zip\n"
        else:
            cuda_major = self.get_cuda_major_version()
            if cuda_major and cuda_major >= 12:
                content += "推荐下载: MEMEFinder_gpu-cuda12.zip\n"
                content += "备选方案: MEMEFinder_cpu.zip\n"
            elif cuda_major and cuda_major == 11:
                content += "推荐下载: MEMEFinder_gpu-cuda11.zip\n"
                content += "备选方案: MEMEFinder_cpu.zip\n"
            else:
                content += "推荐下载: MEMEFinder_cpu.zip\n"
        
        content += f"\n{'='*60}\n"
        content += "生成时间: 自动检测\n"
        
        with open(guide_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ 推荐结果已保存到: {guide_file}")


def main():
    recommender = VersionRecommender()
    recommender.recommend_version()
    
    # 询问是否保存推荐结果
    try:
        save = input("\n是否保存推荐结果到文件? (y/n): ").strip().lower()
        if save == 'y':
            recommender.create_download_guide()
    except KeyboardInterrupt:
        print("\n\n已取消")


if __name__ == "__main__":
    main()
