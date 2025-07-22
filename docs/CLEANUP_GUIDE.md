# RD-Agent 项目清理指南

## 概述

`cleanup_project.sh` 是一个专门为 RD-Agent 项目设计的清理脚本，用于清理项目中的工作文件、缓存和备份，使项目回到崭新的状态。这对于解决项目运行问题、释放磁盘空间或准备项目部署非常有用。

## 功能特性

### 🔧 清理内容

脚本会清理以下类型的文件和目录：

#### 📁 移动的目录（保留在临时位置）
- `log/` - 日志工作文件目录
- `pickle_cache/` - Python pickle缓存目录
- `workspace_cache/` - 工作空间缓存目录
- `rdagent.egg-info/` - Python包构建缓存目录
- `rdagent_backup_*/` - 备份目录
- `github_backup/` - GitHub备份目录
- `git_ignore_folder/` - Git忽略的工作文件目录

#### 🗑️ 直接删除的文件
- `__pycache__/` - Python缓存目录
- `*.pyc`, `*.pyo`, `*.pyd` - Python编译文件
- `.pytest_cache/` - pytest缓存目录
- `*.log` - 日志文件
- `*.tmp`, `*.swp`, `*.swo`, `*~` - 临时文件和编辑器文件
- `.DS_Store` - macOS系统文件

### 🛡️ 安全特性

- **非破坏性清理**: 重要文件移动到临时目录而非直接删除
- **权限处理**: 自动处理权限不足的情况
- **错误处理**: 遇到错误时优雅退出
- **交互式确认**: 默认模式下会询问用户确认
- **恢复功能**: 支持一键恢复清理的文件

## 使用方法

### 基本用法

```bash
# 给脚本添加执行权限（首次使用）
chmod +x cleanup_project.sh

# 交互式清理（推荐）
./cleanup_project.sh
```

### 高级选项

```bash
# 显示帮助信息
./cleanup_project.sh -h

# 强制清理（不询问确认）
./cleanup_project.sh -f

# 预览模式（仅显示将要清理的内容，不实际执行）
./cleanup_project.sh -d

# 恢复最近清理的文件
./cleanup_project.sh -r
```

## 使用场景

### 1. 解决项目运行问题
当项目出现莫名其妙的错误时，清理缓存文件往往能解决问题：

```bash
# 清理所有缓存
./cleanup_project.sh -f

# 重新安装依赖
pip install -e .

# 重新运行项目
python -m rdagent
```

### 2. 释放磁盘空间
项目运行一段时间后，缓存文件可能占用大量空间：

```bash
# 查看清理前的大小
du -sh .

# 清理项目
./cleanup_project.sh

# 查看清理后的大小
du -sh .
```

### 3. 准备项目部署
部署前清理不必要的文件：

```bash
# 预览将要清理的内容
./cleanup_project.sh -d

# 确认无误后执行清理
./cleanup_project.sh -f
```

### 4. 重置开发环境
当开发环境出现问题时，完全重置：

```bash
# 清理项目文件
./cleanup_project.sh -f

# 删除虚拟环境（如果使用）
rm -rf venv/

# 重新创建虚拟环境
python -m venv venv
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

## 恢复文件

### 自动恢复
使用脚本的恢复功能：

```bash
./cleanup_project.sh -r
```

### 手动恢复
如果知道临时目录位置：

```bash
# 查看临时目录
ls -la /tmp/rdagent_cleanup_*

# 恢复文件
mv /tmp/rdagent_cleanup_YYYYMMDD_HHMMSS/* .
```

### 永久删除
如果确定不需要恢复：

```bash
# 删除临时目录
rm -rf /tmp/rdagent_cleanup_*
```

## 注意事项

### ⚠️ 重要提醒

1. **备份重要数据**: 清理前请确保重要数据已备份
2. **项目根目录**: 必须在 RD-Agent 项目根目录下运行脚本
3. **权限要求**: 某些操作可能需要 sudo 权限
4. **临时文件**: 清理的文件保存在 `/tmp/` 目录，系统重启可能丢失

### 🔍 清理前检查

```bash
# 检查当前目录
pwd
ls -la pyproject.toml rdagent/

# 预览清理内容
./cleanup_project.sh -d

# 检查磁盘空间
df -h .
```

### 🚨 常见问题

#### Q: 脚本提示权限不足怎么办？
A: 脚本会自动尝试使用 sudo，如果仍有问题，请检查文件权限：
```bash
ls -la
sudo chown -R $USER:$USER .
```

#### Q: 清理后项目无法运行怎么办？
A: 尝试恢复文件并重新安装依赖：
```bash
./cleanup_project.sh -r
pip install -e .
```

#### Q: 临时目录被删除了怎么办？
A: 如果临时目录被意外删除，可能需要重新配置项目或从备份恢复。

## 脚本维护

### 版本信息
- 版本: 1.0.0
- 作者: RD-Agent Team
- 兼容性: Linux/macOS

### 更新日志
- v1.0.0: 初始版本，支持基本清理功能

### 贡献指南
如需改进脚本，请：
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 相关文档

- [RD-Agent 项目文档](../README.md)
- [开发环境配置](../docs/DEVELOPMENT.md)
- [故障排除指南](../docs/TROUBLESHOOTING.md)

---

**提示**: 定期清理项目可以保持开发环境的整洁，提高开发效率。建议在遇到问题时或定期（如每周）运行一次清理脚本。 