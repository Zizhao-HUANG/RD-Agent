#!/bin/bash
# rdagent 快速断点续跑脚本
# 使用方法: ./quick_recover.sh

set -e

echo "=== rdagent 快速恢复工具 ==="

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

# 找到最新的运行和步骤
LATEST_RUN_ID=$(ls -t log/ | head -n 1)
LATEST_STEP_PATH=$(find "log/$LATEST_RUN_ID/__session__/" -type f -name "*_*" | sort -V | tail -n 1)

echo "发现最近的运行ID: $LATEST_RUN_ID"
echo "发现需要恢复的步骤文件: $LATEST_STEP_PATH"
echo ""

# 激活环境并执行恢复
echo "正在激活环境并执行恢复..."
source ~/anaconda3/etc/profile.d/conda.sh
conda activate rdagent4qlib

echo "执行恢复命令..."
dotenv run -- python -m rdagent.app.qlib_rd_loop.factor "$LATEST_STEP_PATH" --checkout=True 