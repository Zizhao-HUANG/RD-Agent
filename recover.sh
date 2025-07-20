#!/bin/bash
# rdagent 断点续跑自动化脚本
# 使用方法: ./recover.sh

set -e  # 遇到错误时退出

echo "=== rdagent 断点续跑工具 ==="

# 自动进入项目目录
PROJECT_DIR="$HOME/RD-Agent"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "错误: 找不到项目目录: $PROJECT_DIR"
    exit 1
fi

# 如果不在项目目录，自动切换
if [ "$(pwd)" != "$PROJECT_DIR" ]; then
    echo "正在切换到项目目录: $PROJECT_DIR"
    cd "$PROJECT_DIR"
    echo "✓ 已切换到项目目录"
fi

echo "正在查找最近的运行记录..."

# 检查是否有运行记录
if [ ! "$(ls -A log/ 2>/dev/null)" ]; then
    echo "错误: 没有找到任何运行记录"
    exit 1
fi

# 找到最新的运行ID
LATEST_RUN_ID=$(ls -t log/ | head -n 1)
echo "✓ 发现最近的运行ID: $LATEST_RUN_ID"

# 检查会话目录是否存在
SESSION_DIR="log/$LATEST_RUN_ID/__session__"
if [ ! -d "$SESSION_DIR" ]; then
    echo "错误: 会话目录不存在: $SESSION_DIR"
    exit 1
fi

# 找到该次运行中最后一个保存的步骤文件
LATEST_STEP_PATH=$(find "$SESSION_DIR" -type f -name "*_*" | sort -V | tail -n 1)

if [ -z "$LATEST_STEP_PATH" ]; then
    echo "错误: 没有找到可恢复的步骤文件"
    exit 1
fi

echo "✓ 发现需要恢复的步骤文件: $LATEST_STEP_PATH"
echo ""

# 显示恢复信息
echo "=== 恢复信息 ==="
echo "运行ID: $LATEST_RUN_ID"
echo "断点文件: $LATEST_STEP_PATH"
echo ""

# 询问用户是否继续
read -p "是否从该断点恢复运行? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消恢复操作"
    exit 0
fi

echo ""
echo "=== 开始恢复 ==="

# 检查conda环境
if ! command -v conda &> /dev/null; then
    echo "错误: 未找到 conda 命令"
    exit 1
fi

# 激活conda环境
echo "正在激活 conda 环境..."
source ~/anaconda3/etc/profile.d/conda.sh
conda activate rdagent4qlib

# 检查环境是否正确激活
if [[ "$CONDA_DEFAULT_ENV" != "rdagent4qlib" ]]; then
    echo "错误: 无法激活 rdagent4qlib 环境"
    exit 1
fi

echo "✓ 环境已激活: $CONDA_DEFAULT_ENV"

# 检查dotenv是否可用
if ! command -v dotenv &> /dev/null; then
    echo "错误: 未找到 dotenv 命令，请安装 python-dotenv"
    exit 1
fi

# 执行恢复命令
echo "正在执行恢复命令..."
echo "命令: dotenv run -- python -m rdagent.app.qlib_rd_loop.factor $LATEST_STEP_PATH --checkout=True"
echo ""

dotenv run -- python -m rdagent.app.qlib_rd_loop.factor "$LATEST_STEP_PATH" --checkout=True 