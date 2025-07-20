#!/bin/bash
# rdagent 交互式选择恢复脚本
# 使用方法: ./select_recover.sh

set -e

echo "=== rdagent 交互式选择恢复工具 ==="

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

# 检查是否有运行记录
if [ ! "$(ls -A log/ 2>/dev/null)" ]; then
    echo "错误: 没有找到任何运行记录"
    exit 1
fi

echo "正在扫描运行记录..."

# 第一步：选择运行文件夹
echo ""
echo "=== 第一步：选择运行文件夹 ==="
echo "可用的运行记录："

# 获取所有运行文件夹并编号
RUN_FOLDERS=($(ls -t log/))
for i in "${!RUN_FOLDERS[@]}"; do
    echo "  $((i+1)). ${RUN_FOLDERS[$i]}"
done

# 获取用户选择
while true; do
    read -p "请选择运行文件夹 (1-${#RUN_FOLDERS[@]}): " choice
    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#RUN_FOLDERS[@]}" ]; then
        SELECTED_RUN="${RUN_FOLDERS[$((choice-1))]}"
        break
    else
        echo "请输入有效的数字 (1-${#RUN_FOLDERS[@]})"
    fi
done

echo "✓ 已选择运行: $SELECTED_RUN"

# 第二步：选择会话
echo ""
echo "=== 第二步：选择会话 ==="
SESSION_DIR="log/$SELECTED_RUN/__session__"
if [ ! -d "$SESSION_DIR" ]; then
    echo "错误: 会话目录不存在: $SESSION_DIR"
    exit 1
fi

echo "可用的会话："

# 获取所有会话文件夹并编号
SESSIONS=($(ls -d "$SESSION_DIR"/*/ 2>/dev/null | sed 's|/$||' | sed 's|.*/||' | sort -V))
if [ ${#SESSIONS[@]} -eq 0 ]; then
    echo "错误: 没有找到任何会话"
    exit 1
fi

for i in "${!SESSIONS[@]}"; do
    echo "  $((i+1)). ${SESSIONS[$i]}"
done

# 获取用户选择
while true; do
    read -p "请选择会话 (1-${#SESSIONS[@]}): " choice
    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#SESSIONS[@]}" ]; then
        SELECTED_SESSION="${SESSIONS[$((choice-1))]}"
        break
    else
        echo "请输入有效的数字 (1-${#SESSIONS[@]})"
    fi
done

echo "✓ 已选择会话: $SELECTED_SESSION"

# 第三步：选择步骤
echo ""
echo "=== 第三步：选择步骤 ==="
STEP_DIR="$SESSION_DIR/$SELECTED_SESSION"
if [ ! -d "$STEP_DIR" ]; then
    echo "错误: 步骤目录不存在: $STEP_DIR"
    exit 1
fi

echo "可用的步骤："

# 获取所有步骤文件并编号
STEPS=($(find "$STEP_DIR" -type f -name "*_*" | sort -V | sed 's|.*/||'))
if [ ${#STEPS[@]} -eq 0 ]; then
    echo "错误: 没有找到任何步骤文件"
    exit 1
fi

for i in "${!STEPS[@]}"; do
    echo "  $((i+1)). ${STEPS[$i]}"
done

# 获取用户选择
while true; do
    read -p "请选择步骤 (1-${#STEPS[@]}): " choice
    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#STEPS[@]}" ]; then
        SELECTED_STEP="${STEPS[$((choice-1))]}"
        break
    else
        echo "请输入有效的数字 (1-${#STEPS[@]})"
    fi
done

echo "✓ 已选择步骤: $SELECTED_STEP"

# 构建完整的断点路径
SELECTED_PATH="$STEP_DIR/$SELECTED_STEP"

echo ""
echo "=== 恢复信息 ==="
echo "运行ID: $SELECTED_RUN"
echo "会话: $SELECTED_SESSION"
echo "步骤: $SELECTED_STEP"
echo "断点文件: $SELECTED_PATH"
echo ""

# 确认执行
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
echo "命令: dotenv run -- python -m rdagent.app.qlib_rd_loop.factor $SELECTED_PATH --checkout=True"
echo ""

dotenv run -- python -m rdagent.app.qlib_rd_loop.factor "$SELECTED_PATH" --checkout=True 