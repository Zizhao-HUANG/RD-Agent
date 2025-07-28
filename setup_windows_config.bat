@echo off
echo ========================================
echo WSL2 高性能配置脚本
echo 针对192GB RAM和24GB VRAM优化
echo ========================================
echo.

REM 获取用户目录
set USERPROFILE=%USERPROFILE%
set WSLCONFIG=%USERPROFILE%\.wslconfig

echo 正在配置WSL2...
echo 配置文件位置: %WSLCONFIG%
echo.

REM 创建WSL2配置文件
echo # WSL2 高性能配置 - 针对192GB RAM和24GB VRAM优化 > "%WSLCONFIG%"
echo. >> "%WSLCONFIG%"
echo [wsl2] >> "%WSLCONFIG%"
echo # 启用GPU支持 >> "%WSLCONFIG%"
echo gpuSupport=true >> "%WSLCONFIG%"
echo. >> "%WSLCONFIG%"
echo # 内存配置 - 分配160GB给WSL2（保留32GB给Windows） >> "%WSLCONFIG%"
echo memory=160GB >> "%WSLCONFIG%"
echo. >> "%WSLCONFIG%"
echo # 处理器配置 - 根据您的CPU核心数调整 >> "%WSLCONFIG%"
echo processors=16 >> "%WSLCONFIG%"
echo. >> "%WSLCONFIG%"
echo # 交换配置 - 设置较大的交换空间 >> "%WSLCONFIG%"
echo swap=32GB >> "%WSLCONFIG%"
echo. >> "%WSLCONFIG%"
echo # 本地主机转发 >> "%WSLCONFIG%"
echo localhostForwarding=true >> "%WSLCONFIG%"
echo. >> "%WSLCONFIG%"
echo # 网络配置优化 >> "%WSLCONFIG%"
echo networkingMode=mirrored >> "%WSLCONFIG%"
echo. >> "%WSLCONFIG%"
echo # 内存页面合并优化 >> "%WSLCONFIG%"
echo pageReporting=false >> "%WSLCONFIG%"
echo. >> "%WSLCONFIG%"
echo # 启用嵌套虚拟化（如果需要） >> "%WSLCONFIG%"
echo nestedVirtualization=true >> "%WSLCONFIG%"
echo. >> "%WSLCONFIG%"
echo # 启用实验性功能 >> "%WSLCONFIG%"
echo [experimental] >> "%WSLCONFIG%"
echo networkingMode=mirrored >> "%WSLCONFIG%"
echo sparseVhd=true >> "%WSLCONFIG%"

echo ✅ WSL2配置文件已创建！
echo.
echo 配置文件内容:
echo ----------------------------------------
type "%WSLCONFIG%"
echo ----------------------------------------
echo.

echo 🔄 正在重启WSL2...
wsl --shutdown

echo.
echo ⏳ 等待5秒...
timeout /t 5 /nobreak >nul

echo.
echo 🚀 重新启动WSL2...
wsl

echo.
echo ========================================
echo 配置完成！
echo ========================================
echo.
echo 📋 下一步操作：
echo 1. 在WSL2中运行: free -h
echo 2. 检查内存是否显示约160GB
echo 3. 运行: nvidia-smi 检查GPU
echo 4. 运行: ~/monitor_memory.sh 监控系统
echo.
echo 📖 详细说明请查看: WSL2_OPTIMIZATION_GUIDE.md
echo.
pause 