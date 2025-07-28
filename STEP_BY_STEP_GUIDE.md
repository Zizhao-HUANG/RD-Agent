# 🚀 WSL2配置分步操作指南

## ✅ 第一步：文件复制完成

文件已成功复制到您的Windows桌面：
- ✅ `wslconfig_optimized.txt` - WSL2优化配置
- ✅ `setup_windows_config.bat` - 自动配置脚本
- ✅ `WSL2_OPTIMIZATION_GUIDE.md` - 详细指南
- ✅ `OPTIMIZATION_SUMMARY.md` - 优化总结

---

## 🔧 第二步：Windows端配置

### 方法一：使用自动配置脚本（推荐）

1. **打开Windows桌面**
   - 在桌面上找到 `setup_windows_config.bat` 文件

2. **运行配置脚本**
   - 双击 `setup_windows_config.bat` 文件
   - 或者在命令提示符中运行：
     ```cmd
     cd C:\Users\thiago\Desktop
     setup_windows_config.bat
     ```

3. **等待脚本完成**
   - 脚本会自动创建 `.wslconfig` 文件
   - 自动重启WSL2
   - 显示配置结果

### 方法二：手动配置

1. **打开用户目录**
   - 按 `Win + R` 键
   - 输入 `%USERPROFILE%`
   - 按回车键

2. **创建配置文件**
   - 在打开的文件夹中，右键选择"新建" → "文本文档"
   - 将文件名改为 `.wslconfig`（注意包含点号）

3. **编辑配置文件**
   - 双击打开 `.wslconfig` 文件
   - 复制 `wslconfig_optimized.txt` 的全部内容
   - 粘贴到 `.wslconfig` 文件中
   - 保存并关闭文件

4. **重启WSL2**
   - 打开命令提示符（按 `Win + R`，输入 `cmd`）
   - 运行命令：`wsl --shutdown`
   - 等待几秒钟
   - 运行命令：`wsl`

---

## 🔍 第三步：验证配置

重启WSL2后，在Ubuntu中运行以下命令验证配置：

### 1. 检查内存配置
```bash
free -h
```
**预期结果**：应该显示约160GB内存（而不是之前的8GB）

### 2. 检查GPU配置
```bash
nvidia-smi
```
**预期结果**：应该显示RTX 4090 24GB VRAM

### 3. 检查CPU核心数
```bash
nproc
```
**预期结果**：应该显示16核心

### 4. 运行监控脚本
```bash
~/monitor_memory.sh
```
**预期结果**：显示详细的系统资源使用情况

### 5. 测试GPU性能
```bash
python -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'GPU数量: {torch.cuda.device_count()}'); print(f'当前GPU: {torch.cuda.current_device()}'); print(f'GPU名称: {torch.cuda.get_device_name()}')"
```
**预期结果**：显示CUDA可用，GPU数量为1，GPU名称为RTX 4090

---

## 🛠️ 第四步：使用监控工具

配置完成后，您可以使用以下工具监控系统：

### 实时监控命令
```bash
# 内存监控
~/monitor_memory.sh

# 系统资源监控
htop

# GPU监控
nvtop

# 内存清理
~/cleanup_memory.sh

# 查看GPU状态
nvidia-smi
```

### 性能测试
```bash
# 测试GPU内存分配
python -c "import torch; x = torch.randn(10000, 10000, device='cuda'); print(f'GPU内存使用: {torch.cuda.memory_allocated()/1024**3:.2f}GB')"
```

---

## 🔧 故障排除

### 如果WSL2启动失败
1. 检查 `.wslconfig` 文件语法是否正确
2. 尝试减少内存配置（如128GB）：
   ```ini
   memory=128GB
   ```
3. 检查Windows可用内存是否足够

### 如果GPU不可用
1. 确保安装了NVIDIA驱动
2. 检查WSL2 GPU支持是否启用
3. 重启WSL2和Windows

### 如果内存不足
1. 运行内存清理：`~/cleanup_memory.sh`
2. 检查进程内存使用：`ps aux --sort=-%mem | head -10`
3. 重启WSL2

---

## 📊 配置前后对比

| 项目 | 配置前 | 配置后 |
|------|--------|--------|
| 内存 | 8GB | 160GB |
| GPU | 24GB VRAM | 24GB VRAM（完全可用） |
| CPU | 4核心 | 16核心 |
| 系统稳定性 | 经常OOM重启 | 稳定运行 |

---

## 🎉 完成！

配置完成后，您可以：

1. **运行大型机器学习模型**
2. **处理大数据集**
3. **进行GPU密集型计算**
4. **享受稳定的系统性能**

**重要提醒**：
- 定期运行 `~/monitor_memory.sh` 监控系统资源
- 如果遇到问题，查看 `WSL2_OPTIMIZATION_GUIDE.md` 详细说明
- 保持系统更新以获得最佳性能

---

## 📞 技术支持

如果在配置过程中遇到问题：

1. 查看详细指南：`WSL2_OPTIMIZATION_GUIDE.md`
2. 运行系统诊断：`~/monitor_memory.sh`
3. 检查错误日志：`tail -f ~/memory_log.txt`
4. 参考故障排除部分

**祝您使用愉快！** 🚀 