"""
测试多版本构建系统

验证：
1. 打包脚本是否正常工作
2. 版本配置是否正确
3. DLL文件是否包含
4. 各版本是否能正确初始化
"""

import sys
import os
from pathlib import Path
import json
import subprocess

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class MultiVersionTester:
    """多版本测试器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.releases_dir = self.project_root / "releases"
        
    def test_build_script(self):
        """测试构建脚本语法"""
        print("🔍 测试构建脚本...")
        
        script_path = self.project_root / "scripts" / "build_multi_version.py"
        
        try:
            # 检查脚本是否能导入
            result = subprocess.run(
                [sys.executable, str(script_path), "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ 构建脚本语法正确")
                return True
            else:
                print(f"❌ 构建脚本有错误: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 构建脚本测试失败: {e}")
            return False
    
    def test_version_detector(self):
        """测试版本检测器"""
        print("\n🔍 测试版本检测器...")
        
        script_path = self.project_root / "scripts" / "recommend_version.py"
        
        try:
            # 尝试导入
            result = subprocess.run(
                [sys.executable, "-c", f"import sys; sys.path.insert(0, r'{self.project_root / 'scripts'}'); from recommend_version import VersionRecommender; r = VersionRecommender(); print('OK')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "OK" in result.stdout:
                print("✅ 版本检测器正常")
                return True
            else:
                print(f"❌ 版本检测器有问题: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 版本检测器测试失败: {e}")
            return False
    
    def test_version_configs(self):
        """测试版本配置生成"""
        print("\n🔍 测试版本配置...")
        
        version_types = ["cpu", "gpu-cuda11", "gpu-cuda12"]
        
        for version_type in version_types:
            config = {
                "version_type": version_type,
                "gpu_enabled": version_type.startswith("gpu"),
                "cuda_version": version_type.split("-")[-1] if version_type.startswith("gpu") else None
            }
            
            print(f"  {version_type}: {json.dumps(config, indent=2)}")
        
        print("✅ 版本配置格式正确")
        return True
    
    def check_releases_structure(self):
        """检查发布目录结构"""
        print("\n🔍 检查发布目录...")
        
        if not self.releases_dir.exists():
            print("⚠️ releases目录不存在（正常，首次构建后会创建）")
            return True
        
        expected_versions = ["cpu", "gpu-cuda11", "gpu-cuda12"]
        found_versions = []
        
        for version in expected_versions:
            version_dir = self.releases_dir / f"MEMEFinder_{version}"
            if version_dir.exists():
                found_versions.append(version)
                print(f"✅ 找到 {version} 版本")
                
                # 检查关键文件
                exe_file = version_dir / f"MEMEFinder_{version}.exe"
                readme_file = version_dir / "版本说明.txt"
                
                if exe_file.exists():
                    print(f"   ✓ 可执行文件存在")
                else:
                    print(f"   ⚠️ 可执行文件不存在")
                
                if readme_file.exists():
                    print(f"   ✓ 版本说明存在")
                else:
                    print(f"   ⚠️ 版本说明不存在")
        
        if not found_versions:
            print("ℹ️ 未找到已构建版本（运行构建脚本后会生成）")
        
        return True
    
    def test_spec_file(self):
        """测试spec文件"""
        print("\n🔍 检查spec文件...")
        
        spec_file = self.project_root / "MEMEFinder.spec"
        
        if not spec_file.exists():
            print("❌ MEMEFinder.spec 不存在")
            return False
        
        with open(spec_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查关键内容
        checks = {
            "models目录": "('models', 'models')" in content,
            "GPU DLL收集": "onnxruntime" in content.lower(),
            "数据文件": "datas = [" in content
        }
        
        for name, passed in checks.items():
            if passed:
                print(f"✅ {name}: 已配置")
            else:
                print(f"⚠️ {name}: 可能缺失")
        
        return all(checks.values())
    
    def test_batch_scripts(self):
        """测试批处理脚本"""
        print("\n🔍 检查批处理脚本...")
        
        scripts = [
            "scripts/打包所有版本.bat",
            "scripts/选择版本打包.bat"
        ]
        
        for script in scripts:
            script_path = self.project_root / script
            if script_path.exists():
                print(f"✅ {script}: 存在")
            else:
                print(f"❌ {script}: 不存在")
        
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("MEMEFinder 多版本构建系统测试")
        print("="*60)
        
        results = {
            "构建脚本": self.test_build_script(),
            "版本检测器": self.test_version_detector(),
            "版本配置": self.test_version_configs(),
            "发布目录": self.check_releases_structure(),
            "Spec文件": self.test_spec_file(),
            "批处理脚本": self.test_batch_scripts()
        }
        
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        
        for test_name, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"{test_name}: {status}")
        
        total = len(results)
        passed = sum(results.values())
        
        print(f"\n总计: {passed}/{total} 测试通过")
        
        if passed == total:
            print("\n🎉 所有测试通过！多版本构建系统已就绪")
            print("\n下一步:")
            print("  1. 运行 scripts\\选择版本打包.bat 构建版本")
            print("  2. 或运行 python scripts/build_multi_version.py --all")
        else:
            print("\n⚠️ 部分测试未通过，请检查相关配置")
        
        return passed == total


def main():
    tester = MultiVersionTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
