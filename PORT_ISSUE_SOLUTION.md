# 端口19899被占用问题解决方案

## 问题描述
运行 `rdagent ui --log_dir ./log --debug` 时出现错误：
```
2025-07-28 21:53:28.538 Port 19899 is already in use
```

## 问题分析
1. **端口检查确认**：通过多种方法确认端口19899确实被占用
2. **进程检查**：没有找到占用该端口的进程，可能是僵尸进程或端口状态异常
3. **根本原因**：这是streamlit框架的端口检查机制，当端口被占用时会自动报错

## 解决方案

### 方案1：使用不同端口（推荐）
```bash
rdagent ui --port 19900 --log_dir ./log --debug
```

### 方案2：永久修改默认端口
已通过脚本 `fix_port_issue.py` 将默认端口从19899修改为19900，修改的文件包括：
- `rdagent/app/cli.py`
- `rdagent/log/server/app.py`
- `rdagent/log/server/debug_app.py`
- `rdagent/app/utils/health_check.py`

### 方案3：释放被占用的端口
如果确实需要继续使用19899端口，可以尝试：
```bash
# 查找占用端口的进程
sudo lsof -i :19899
sudo netstat -tlnp | grep 19899

# 杀死占用端口的进程
sudo kill -9 <PID>
```

## 验证修复
修复后，可以使用以下命令正常启动应用：
```bash
rdagent ui --log_dir ./log --debug
```

应用将在端口19900上运行，访问地址：
- 本地：http://localhost:19900
- 网络：http://192.168.1.47:19900

## 预防措施
1. 在启动应用前检查端口占用情况
2. 使用 `rdagent health_check` 命令检查系统状态
3. 考虑使用非标准端口避免冲突

## 相关文件
- `fix_port_issue.py` - 自动修复脚本
- `PORT_ISSUE_SOLUTION.md` - 本文档 