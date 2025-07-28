# WSL2 高性能配置指南
## 针对192GB RAM和24GB VRAM优化

### 🎯 配置目标
- 分配160GB内存给WSL2（保留32GB给Windows）
- 充分利用24GB VRAM
- 优化内存管理和GPU性能
- 防止OOM Killer导致的系统重启

---

## 📋 配置步骤

### 第一步：Windows端WSL2配置

1. **打开Windows资源管理器**
   - 按 `Win + R`，输入 `%USERPROFILE%`
   - 在用户目录下创建或编辑 `.wslconfig` 文件

2. **复制以下配置到 `.wslconfig` 文件：**
```ini
# WSL2 高性能配置 - 针对192GB RAM和24GB VRAM优化
[wsl2]
# 启用GPU支持
gpuSupport=true

# 内存配置 - 分配160GB给WSL2（保留32GB给Windows）
memory=160GB

# 处理器配置 - 根据您的CPU核心数调整
processors=16

# 交换配置 - 设置较大的交换空间
swap=32GB

# 本地主机转发
localhostForwarding=true

# 网络配置优化
networkingMode=mirrored

# 内存页面合并优化
pageReporting=false

# 启用嵌套虚拟化（如果需要）
nestedVirtualization=true

# 启用实验性功能
[experimental]
networkingMode=mirrored
sparseVhd=true
```

3. **重启WSL2**
   ```cmd
   wsl --shutdown
   ```

4. **重新启动WSL2**
   ```cmd
   wsl
   ```

---

### 第二步：验证配置

在WSL2中运行以下命令验证配置：

```bash
# 检查内存配置
free -h

# 检查GPU配置
nvidia-smi

# 检查CPU核心数
nproc

# 检查系统信息
cat /proc/meminfo | grep -E "(MemTotal|MemAvailable)"
```

**预期结果：**
- 内存：约160GB
- GPU：RTX 4090 24GB VRAM
- CPU：16核心

---

### 第三步：系统优化（已完成）

系统优化脚本已经运行完成，包括：

✅ **内存管理优化**
- vm.swappiness=10（减少交换使用）
- vm.vfs_cache_pressure=50
- vm.dirty_ratio=15
- vm.dirty_background_ratio=5

✅ **GPU环境变量配置**
- CUDA_VISIBLE_DEVICES=0
- PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:2048
- OMP_NUM_THREADS=16

✅ **监控工具安装**
- htop（系统监控）
- nvtop（GPU监控）
- iotop（I/O监控）

✅ **实用脚本创建**
- `~/monitor_memory.sh` - 内存监控
- `~/cleanup_memory.sh` - 内存清理
- 定时监控任务（每5分钟）

---

### 第四步：RD-Agent优化配置

1. **更新RD-Agent环境变量**
   编辑 `~/.bashrc` 文件，确保包含以下配置：

```bash
# GPU优化配置
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:2048
export OMP_NUM_THREADS=16
export MKL_NUM_THREADS=16
export NUMEXPR_NUM_THREADS=16

# 内存优化
export PYTORCH_NO_CUDA_MEMORY_CACHING=1
export CUDA_LAUNCH_BLOCKING=1

# 显示GPU信息
alias gpuinfo='nvidia-smi'
alias meminfo='free -h && echo "---" && df -h /'
alias sysinfo='htop'
```

2. **应用配置**
   ```bash
   source ~/.bashrc
   ```

---

## 🛠️ 使用工具

### 监控命令
```bash
# 实时内存监控
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
# 测试GPU性能
python -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'GPU数量: {torch.cuda.device_count()}'); print(f'当前GPU: {torch.cuda.current_device()}'); print(f'GPU名称: {torch.cuda.get_device_name()}')"

# 测试内存分配
python -c "import torch; x = torch.randn(10000, 10000, device='cuda'); print(f'GPU内存使用: {torch.cuda.memory_allocated()/1024**3:.2f}GB')"
```

---

## 🔧 故障排除

### 如果WSL2启动失败
1. 检查 `.wslconfig` 文件语法
2. 减少内存分配（如128GB）
3. 检查Windows可用内存

### 如果GPU不可用
1. 确保安装了NVIDIA驱动
2. 检查WSL2 GPU支持是否启用
3. 重启WSL2和Windows

### 如果内存不足
1. 运行 `~/cleanup_memory.sh`
2. 检查进程内存使用：`ps aux --sort=-%mem | head -10`
3. 重启WSL2

---

## 📊 性能基准

配置完成后，您应该看到：

- **内存使用**：90GB+ 可用内存
- **GPU内存**：24GB VRAM 可用
- **CPU性能**：16核心并行处理
- **系统稳定性**：不再出现OOM Killer

---

## 🎉 完成！

现在您的WSL2已经配置为充分利用192GB RAM和24GB VRAM。您可以：

1. 运行大型机器学习模型
2. 处理大数据集
3. 进行GPU密集型计算
4. 享受稳定的系统性能

**记住**：定期运行 `~/monitor_memory.sh` 来监控系统资源使用情况。 