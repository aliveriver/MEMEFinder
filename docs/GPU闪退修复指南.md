# GPU闪退？3步快速修复！

## 🚨 如果程序一启动就闪退

### 第1步：运行修复工具

双击或运行：
```
fix_gpu_crash.py
```

或者在命令行：
```bash
python fix_gpu_crash.py
```

### 第2步：使用生成的启动器

修复工具会自动生成启动器，然后使用：

**开发环境：**
```
双击: 运行_CPU模式.bat
```

**打包后的程序：**
```
双击: 运行_MEMEFinder_CPU模式.bat
```

### 第3步：正常使用

程序现在会以CPU模式运行，不会再闪退！

---

## 📝 详细说明

### 为什么会闪退？

您的GPU硬件虽然存在，但CUDA环境有问题，导致：
```
检测到GPU → 尝试初始化 → CUDA加载失败 → 程序崩溃
```

### CPU模式会慢吗？

**少量图片**（<100张）：几乎感觉不到差别
**大量图片**（>1000张）：会慢一些，但仍然可用

### 性能对比

| 处理数量 | GPU模式 | CPU模式 | 差异 |
|---------|---------|---------|------|
| 10张    | 5秒     | 8秒     | 感觉不明显 |
| 100张   | 30秒    | 60秒    | 可以接受 |
| 1000张  | 5分钟   | 12分钟  | 有差异但可用 |

### 如何修复GPU问题？（高级）

如果您想使用GPU加速，需要：

1. **检查CUDA版本**
   ```bash
   nvidia-smi
   ```
   查看 "CUDA Version"

2. **重新安装onnxruntime-gpu**
   ```bash
   pip uninstall onnxruntime onnxruntime-gpu
   pip install onnxruntime-gpu
   ```

3. **验证安装**
   ```bash
   python -c "import onnxruntime; print(onnxruntime.get_available_providers())"
   ```
   应该看到：`['CUDAExecutionProvider', 'CPUExecutionProvider']`

4. **运行诊断工具**
   ```bash
   python test_gpu_diagnosis.py
   ```

---

## 🆘 仍然有问题？

1. 查看日志文件：`logs/memefinder_*.log`
2. 运行诊断：`python test_gpu_diagnosis.py`
3. 提供完整的错误信息

---

## ✅ 常见问题

**Q: CPU模式安全吗？**
A: 完全安全！只是速度慢一点而已。

**Q: 会损坏我的GPU吗？**
A: 不会。只是软件环境有问题，不使用GPU而已。

**Q: 以后能用GPU吗？**
A: 可以。修复CUDA环境后，删除 `MEMEFINDER_FORCE_CPU` 环境变量即可。

**Q: 如何确认当前模式？**
A: 查看日志，会显示：
```
✓ RapidOCR 初始化成功
  配置模式: CPU/GPU
  实际设备: CPU/GPU (CUDA)
```

---

**快速链接：**
- [详细修复指南](GPU_FIX_GUIDE.md)
- [技术总结](GPU_CRASH_FIX_SUMMARY.md)
- [GPU诊断工具](test_gpu_diagnosis.py)
