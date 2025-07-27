# WSL2 GPU支持故障排除指南

## 常见问题及解决方案

### 1. NVIDIA驱动问题
**症状**: nvidia-smi 命令失败
**解决方案**:
- 在Windows中更新NVIDIA驱动
- 确保驱动版本支持WSL2 GPU

### 2. WSL2版本问题
**症状**: GPU设备文件不存在
**解决方案**:
- 更新WSL2到最新版本
- 确保启用了GPU支持

### 3. CUDA工具包问题
**症状**: nvcc 命令未找到
**解决方案**:
- 安装CUDA工具包
- 设置正确的环境变量

### 4. 权限问题
**症状**: 无法访问GPU设备
**解决方案**:
- 检查设备文件权限
- 确保用户有适当权限

## 验证步骤

1. 检查Windows GPU:
   ```powershell
   Get-WmiObject -Class Win32_VideoController | Where-Object {$_.Name -like '*NVIDIA*'}
   ```

2. 检查WSL2 GPU:
   ```bash
   ls -la /dev/nvidia*
   nvidia-smi
   ```

3. 检查CUDA:
   ```bash
   nvcc --version
   ```

4. 测试LightGBM:
   ```python
   import lightgbm as lgb
   clf = lgb.LGBMClassifier(device='cuda')
   ```

## 联系支持

如果问题仍然存在，请提供以下信息：
- Windows版本
- WSL2版本
- NVIDIA驱动版本
- 错误日志
