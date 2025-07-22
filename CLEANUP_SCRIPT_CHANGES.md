# RD-Agent 项目清理脚本改动说明

## 概述

本次更新为 RD-Agent 项目添加了一个功能完整的清理脚本和详细的使用教程，旨在帮助用户安全、高效地清理项目中的工作文件、缓存和备份。

## 新增文件

### 1. `cleanup_project.sh` - 项目清理脚本

**文件路径**: `/cleanup_project.sh`  
**文件大小**: ~15KB  
**权限**: 可执行文件 (755)

#### 主要功能
- **非破坏性清理**: 重要文件移动到临时目录而非直接删除
- **多种运行模式**: 交互式、强制、预览、恢复模式
- **权限处理**: 自动处理权限不足的情况
- **错误处理**: 完善的错误处理和日志输出
- **彩色输出**: 使用颜色区分不同类型的信息

#### 清理内容
**移动的目录**:
- `log/` - 日志工作文件目录
- `pickle_cache/` - Python pickle缓存目录
- `workspace_cache/` - 工作空间缓存目录
- `rdagent.egg-info/` - Python包构建缓存目录
- `rdagent_backup_*/` - 备份目录
- `github_backup/` - GitHub备份目录
- `git_ignore_folder/` - Git忽略的工作文件目录

**删除的文件**:
- `__pycache__/` - Python缓存目录
- `*.pyc`, `*.pyo`, `*.pyd` - Python编译文件
- `.pytest_cache/` - pytest缓存目录
- `*.log` - 日志文件
- `*.tmp`, `*.swp`, `*.swo`, `*~` - 临时文件和编辑器文件
- `.DS_Store` - macOS系统文件

#### 命令行选项
```bash
./cleanup_project.sh -h      # 显示帮助信息
./cleanup_project.sh         # 交互式清理（推荐）
./cleanup_project.sh -f      # 强制清理（不询问确认）
./cleanup_project.sh -d      # 预览模式（仅显示将要清理的内容）
./cleanup_project.sh -r      # 恢复最近清理的文件
```

### 2. `docs/CLEANUP_GUIDE.md` - 详细使用教程

**文件路径**: `/docs/CLEANUP_GUIDE.md`  
**文件大小**: ~20KB  
**格式**: Markdown

#### 教程内容
- **功能特性介绍**: 详细说明脚本的清理内容和安全特性
- **使用方法**: 基本用法和高级选项的完整说明
- **使用场景**: 4个主要使用场景的详细示例
  - 解决项目运行问题
  - 释放磁盘空间
  - 准备项目部署
  - 重置开发环境
- **恢复文件**: 自动恢复和手动恢复的完整指南
- **注意事项**: 重要提醒和常见问题解答
- **脚本维护**: 版本信息和贡献指南

## 技术特性

### 安全性
- **非破坏性操作**: 重要文件移动到临时目录，可随时恢复
- **权限检查**: 自动检测和处理权限问题
- **错误处理**: 完善的错误处理和优雅退出机制
- **交互式确认**: 默认模式下要求用户确认操作

### 易用性
- **彩色输出**: 使用颜色区分信息类型（INFO、SUCCESS、WARNING、ERROR）
- **详细日志**: 每个操作都有详细的日志输出
- **多种模式**: 支持不同使用场景的运行模式
- **帮助系统**: 完整的命令行帮助信息

### 兼容性
- **跨平台**: 支持 Linux 和 macOS
- **权限处理**: 自动处理不同权限级别的情况
- **路径处理**: 正确处理包含空格和特殊字符的路径

## 使用场景

### 1. 解决项目运行问题
当项目出现莫名其妙的错误时，清理缓存文件往往能解决问题：
```bash
./cleanup_project.sh -f
pip install -e .
python -m rdagent
```

### 2. 释放磁盘空间
项目运行一段时间后，缓存文件可能占用大量空间：
```bash
du -sh .                    # 查看清理前大小
./cleanup_project.sh        # 清理项目
du -sh .                    # 查看清理后大小
```

### 3. 准备项目部署
部署前清理不必要的文件：
```bash
./cleanup_project.sh -d     # 预览清理内容
./cleanup_project.sh -f     # 执行清理
```

### 4. 重置开发环境
当开发环境出现问题时，完全重置：
```bash
./cleanup_project.sh -f     # 清理项目文件
rm -rf venv/                # 删除虚拟环境
python -m venv venv         # 重新创建虚拟环境
pip install -r requirements.txt  # 重新安装依赖
```

## 恢复机制

### 自动恢复
```bash
./cleanup_project.sh -r     # 恢复最近清理的文件
```

### 手动恢复
```bash
ls -la /tmp/rdagent_cleanup_*           # 查看临时目录
mv /tmp/rdagent_cleanup_YYYYMMDD_HHMMSS/* .  # 恢复文件
```

### 永久删除
```bash
rm -rf /tmp/rdagent_cleanup_*           # 删除临时目录
```

## 版本信息

- **版本**: 1.0.0
- **作者**: RD-Agent Team
- **兼容性**: Linux/macOS
- **依赖**: bash, find, mv, rm, sudo (可选)

## 提交信息

```
feat: 添加项目清理脚本和详细使用教程

- 新增 cleanup_project.sh 脚本，支持安全清理项目缓存和工作文件
- 新增 docs/CLEANUP_GUIDE.md 详细使用教程
- 脚本特性：
  * 非破坏性清理，重要文件移动到临时目录
  * 支持交互式、强制、预览、恢复等多种模式
  * 自动处理权限问题
  * 彩色输出和详细日志
  * 完整的错误处理
- 清理内容包括：
  * log/, pickle_cache/, workspace_cache/ 等工作目录
  * rdagent.egg-info/, __pycache__/ 等缓存目录
  * 各种临时文件和编辑器文件
- 使用场景：解决运行问题、释放磁盘空间、准备部署、重置环境
```

## 文件权限

- `cleanup_project.sh`: 755 (可执行)
- `docs/CLEANUP_GUIDE.md`: 644 (可读)

## 注意事项

1. **备份重要数据**: 清理前请确保重要数据已备份
2. **项目根目录**: 必须在 RD-Agent 项目根目录下运行脚本
3. **权限要求**: 某些操作可能需要 sudo 权限
4. **临时文件**: 清理的文件保存在 `/tmp/` 目录，系统重启可能丢失

## 后续维护

- 定期更新脚本以支持新的缓存文件类型
- 根据用户反馈优化用户体验
- 添加更多平台支持（如 Windows）
- 集成到项目的 CI/CD 流程中

---

**提示**: 这个清理脚本将大大提高 RD-Agent 项目的维护效率，特别是在解决环境问题和准备部署时。 