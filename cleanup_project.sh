#!/bin/bash

# RD-Agent 项目清理脚本
# 用于清理项目中的工作文件、缓存和备份，使项目回到崭新状态
# 作者: RD-Agent Team
# 版本: 1.0.0

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "RD-Agent 项目清理脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -f, --force    强制清理，不询问确认"
    echo "  -d, --dry-run  仅显示将要清理的文件，不实际执行"
    echo "  -r, --restore  从临时目录恢复文件"
    echo ""
    echo "示例:"
    echo "  $0              # 交互式清理"
    echo "  $0 -f           # 强制清理"
    echo "  $0 -d           # 预览清理内容"
    echo "  $0 -r           # 恢复文件"
}

# 检查是否在项目根目录
check_project_root() {
    if [ ! -f "pyproject.toml" ] || [ ! -d "rdagent" ]; then
        print_error "请在RD-Agent项目根目录下运行此脚本"
        exit 1
    fi
}

# 创建临时目录
create_temp_dir() {
    TEMP_DIR="/tmp/rdagent_cleanup_$(date +%Y%m%d_%H%M%S)"
    print_info "创建临时目录: $TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    echo "$TEMP_DIR"
}

# 移动目录到临时位置
move_directory() {
    local source_dir="$1"
    local temp_dir="$2"
    local description="$3"
    
    if [ -d "$source_dir" ]; then
        print_info "移动 $description: $source_dir"
        if [ "$DRY_RUN" = "true" ]; then
            echo "  [DRY-RUN] 将移动: $source_dir -> $temp_dir/"
        else
            # 处理权限问题
            if [ ! -w "$source_dir" ]; then
                print_warning "权限不足，尝试使用sudo移动: $source_dir"
                sudo mv "$source_dir" "$temp_dir/" 2>/dev/null || {
                    print_error "无法移动 $source_dir，跳过"
                    return 1
                }
            else
                mv "$source_dir" "$temp_dir/" 2>/dev/null || {
                    print_error "无法移动 $source_dir，跳过"
                    return 1
                }
            fi
            print_success "已移动: $source_dir"
        fi
    else
        print_info "跳过不存在的目录: $source_dir"
    fi
}

# 删除文件
delete_files() {
    local pattern="$1"
    local description="$2"
    
    print_info "删除 $description: $pattern"
    if [ "$DRY_RUN" = "true" ]; then
        echo "  [DRY-RUN] 将删除: $pattern"
    else
        find . -name "$pattern" -delete 2>/dev/null || true
        print_success "已删除: $pattern"
    fi
}

# 删除目录
delete_directories() {
    local pattern="$1"
    local description="$2"
    
    print_info "删除 $description: $pattern"
    if [ "$DRY_RUN" = "true" ]; then
        echo "  [DRY-RUN] 将删除目录: $pattern"
    else
        find . -name "$pattern" -type d -exec rm -rf {} + 2>/dev/null || true
        print_success "已删除目录: $pattern"
    fi
}

# 恢复文件
restore_files() {
    local temp_dir="$1"
    
    if [ ! -d "$temp_dir" ]; then
        print_error "临时目录不存在: $temp_dir"
        print_info "请检查 /tmp/ 目录下的 rdagent_cleanup_* 文件夹"
        exit 1
    fi
    
    print_info "从 $temp_dir 恢复文件..."
    mv "$temp_dir"/* . 2>/dev/null || {
        print_error "恢复文件失败"
        exit 1
    }
    rmdir "$temp_dir"
    print_success "文件恢复完成"
}

# 主清理函数
main_cleanup() {
    print_info "开始清理RD-Agent项目..."
    
    # 检查项目根目录
    check_project_root
    
    # 创建临时目录
    TEMP_DIR=$(create_temp_dir)
    
    # 定义要移动的目录
    declare -A dirs_to_move=(
        ["log"]="日志工作文件目录"
        ["pickle_cache"]="Python pickle缓存目录"
        ["workspace_cache"]="工作空间缓存目录"
        ["rdagent.egg-info"]="Python包构建缓存目录"
        ["rdagent_backup_20250719_031928"]="备份目录"
        ["github_backup"]="GitHub备份目录"
        ["git_ignore_folder"]="Git忽略的工作文件目录"
    )
    
    # 移动目录
    for dir in "${!dirs_to_move[@]}"; do
        move_directory "$dir" "$TEMP_DIR" "${dirs_to_move[$dir]}"
    done
    
    # 删除Python缓存文件
    delete_directories "__pycache__" "Python缓存目录"
    delete_files "*.pyc" "Python编译文件"
    delete_files "*.pyo" "Python优化文件"
    delete_files "*.pyd" "Python动态库文件"
    
    # 删除其他缓存文件
    delete_directories ".pytest_cache" "pytest缓存目录"
    delete_files ".coverage" "测试覆盖率文件"
    delete_files "*.log" "日志文件"
    delete_files ".DS_Store" "macOS系统文件"
    
    # 删除临时文件和编辑器文件
    delete_files "*.tmp" "临时文件"
    delete_files "*.swp" "Vim交换文件"
    delete_files "*.swo" "Vim备份文件"
    delete_files "*~" "编辑器备份文件"
    
    # 检查其他可能的缓存目录
    print_info "检查其他可能的缓存目录..."
    for dir in cache caches temp tmp .cache .caches .temp .tmp; do
        if [ -d "$dir" ]; then
            move_directory "$dir" "$TEMP_DIR" "缓存目录"
        fi
    done
    
    # 检查rdagent目录中的缓存
    if [ -d "rdagent" ]; then
        print_info "检查rdagent目录中的缓存..."
        delete_files "*.cache" "缓存文件"
        delete_files "*.tmp" "临时文件"
    fi
    
    if [ "$DRY_RUN" = "true" ]; then
        print_info "DRY-RUN 模式完成，未实际执行任何操作"
    else
        print_success "清理完成！"
        echo ""
        echo "所有清理的文件已移动到: $TEMP_DIR"
        echo ""
        echo "如果您确定要删除这些文件，可以运行:"
        echo "rm -rf $TEMP_DIR"
        echo ""
        echo "如果您想恢复这些文件，可以运行:"
        echo "$0 -r"
        echo ""
        echo "或者手动恢复:"
        echo "mv $TEMP_DIR/* ."
    fi
}

# 解析命令行参数
DRY_RUN="false"
FORCE="false"
RESTORE="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--force)
            FORCE="true"
            shift
            ;;
        -d|--dry-run)
            DRY_RUN="true"
            shift
            ;;
        -r|--restore)
            RESTORE="true"
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 主程序逻辑
if [ "$RESTORE" = "true" ]; then
    # 查找最新的临时目录
    LATEST_TEMP=$(ls -td /tmp/rdagent_cleanup_* 2>/dev/null | head -1)
    if [ -z "$LATEST_TEMP" ]; then
        print_error "未找到清理临时目录"
        exit 1
    fi
    restore_files "$LATEST_TEMP"
elif [ "$DRY_RUN" = "true" ]; then
    main_cleanup
elif [ "$FORCE" = "true" ]; then
    main_cleanup
else
    # 交互式模式
    print_warning "此操作将移动以下目录到临时位置:"
    echo "  - log/ (日志文件)"
    echo "  - pickle_cache/ (缓存文件)"
    echo "  - workspace_cache/ (工作空间缓存)"
    echo "  - rdagent.egg-info/ (包构建缓存)"
    echo "  - rdagent_backup_*/ (备份目录)"
    echo "  - github_backup/ (GitHub备份)"
    echo "  - git_ignore_folder/ (Git忽略文件)"
    echo ""
    echo "并删除所有Python缓存文件和其他临时文件"
    echo ""
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        main_cleanup
    else
        print_info "操作已取消"
        exit 0
    fi
fi 