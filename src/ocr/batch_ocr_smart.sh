#!/bin/bash

# 智能批量OCR处理脚本
# 自动枚举output目录下的所有子目录并运行OCR处理，支持嵌套目录

# 配置
OUTPUT_BASE_DIR="/Volumes/ext/SatExams/data/output"
SCRIPT_DIR="/Volumes/ext/SatExams/src/ocr"
MAX_WORKERS=10
LOG_FILE="/Volumes/ext/SatExams/data/ocr_batch_smart.log"
MIN_PNG_COUNT=1  # 最少PNG文件数量才处理

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" >> "$LOG_FILE"
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅${NC} $1" >> "$LOG_FILE"
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌${NC} $1" >> "$LOG_FILE"
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1" >> "$LOG_FILE"
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1"
}

# 检查必要的目录和文件
check_prerequisites() {
    log "检查运行环境..."
    
    if [ ! -d "$OUTPUT_BASE_DIR" ]; then
        log_error "输出目录不存在: $OUTPUT_BASE_DIR"
        exit 1
    fi
    
    if [ ! -d "$SCRIPT_DIR" ]; then
        log_error "脚本目录不存在: $SCRIPT_DIR"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/batch_ocr.py" ]; then
        log_error "batch_ocr.py 不存在: $SCRIPT_DIR/batch_ocr.py"
        exit 1
    fi
    
    # 检查虚拟环境
    if [ ! -d "$SCRIPT_DIR/../venv" ]; then
        log_error "虚拟环境不存在: $SCRIPT_DIR/../venv"
        exit 1
    fi
    
    log_success "环境检查通过"
}

# 激活虚拟环境
activate_venv() {
    log "激活虚拟环境..."
    source "$SCRIPT_DIR/../venv/bin/activate"
    if [ $? -eq 0 ]; then
        log_success "虚拟环境激活成功"
    else
        log_error "虚拟环境激活失败"
        exit 1
    fi
}

# 检查目录是否应该被处理
should_process_directory() {
    local dir_path="$1"
    local dir_name=$(basename "$dir_path")
    
    # 跳过系统目录和隐藏目录
    if [[ "$dir_name" =~ ^\. ]] || [[ "$dir_name" =~ ^_ ]]; then
        return 1
    fi
    
    # 跳过一些常见的非内容目录
    if [[ "$dir_name" =~ ^(A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z)$ ]]; then
        return 1
    fi
    
    # 检查是否有足够的PNG文件
    local png_count=$(find "$dir_path" -maxdepth 1 -name "*.png" -not -name "._*" 2>/dev/null | wc -l)
    
    if [ $png_count -ge $MIN_PNG_COUNT ]; then
        return 0
    else
        return 1
    fi
}

# 获取所有需要处理的目录
get_directories_to_process() {
    local directories=()
    
    log "扫描目录结构..."
    
    # 使用find命令递归查找所有目录，正确处理包含空格的目录名
    while IFS= read -r -d '' dir; do
        if should_process_directory "$dir"; then
            local png_count=$(find "$dir" -maxdepth 1 -name "*.png" -not -name "._*" 2>/dev/null | wc -l)
            directories+=("$dir")
            log "发现有效目录: \"$(basename "$dir")\" ($png_count 个PNG文件)"
        fi
    done < <(find "$OUTPUT_BASE_DIR" -type d -print0 | sort -z)
    
    # 返回数组，使用printf确保正确处理空格
    printf '%s\0' "${directories[@]}"
}

# 处理单个目录
process_directory() {
    local dir_path="$1"
    local dir_name=$(basename "$dir_path")
    
    log "开始处理目录: \"$dir_name\""
    
    # 切换到脚本目录
    cd "$SCRIPT_DIR"
    
    # 运行OCR处理（重定向stderr避免日志干扰）
    log "运行OCR处理: python batch_ocr.py --target-dir \"$dir_path\" --max-workers $MAX_WORKERS"
    
    # 使用临时文件来捕获输出，避免日志干扰
    local temp_output=$(mktemp)
    local exit_code=0
    
    if python batch_ocr.py --target-dir "$dir_path" --max-workers $MAX_WORKERS > "$temp_output" 2>&1; then
        log_success "目录 \"$dir_name\" 处理完成"
        exit_code=0
    else
        log_error "目录 \"$dir_name\" 处理失败"
        exit_code=1
    fi
    
    # 显示Python脚本的输出（但不包含在日志中）
    cat "$temp_output"
    rm -f "$temp_output"
    
    return $exit_code
}

# 主函数
main() {
    log "=== 智能批量OCR处理开始 ==="
    log "输出目录: $OUTPUT_BASE_DIR"
    log "最大并行度: $MAX_WORKERS"
    log "最少PNG文件数: $MIN_PNG_COUNT"
    log "日志文件: $LOG_FILE"
    
    # 检查运行环境
    check_prerequisites
    
    # 激活虚拟环境
    activate_venv
    
    # 获取所有需要处理的目录
    directories=()
    while IFS= read -r -d '' dir; do
        directories+=("$dir")
    done < <(get_directories_to_process)
    
    if [ ${#directories[@]} -eq 0 ]; then
        log_warning "没有找到需要处理的目录"
        exit 0
    fi
    
    log "找到 ${#directories[@]} 个需要处理的目录"
    
    # 统计信息
    total_dirs=${#directories[@]}
    success_count=0
    failed_count=0
    failed_dirs=()
    
    # 处理每个目录
    for i in "${!directories[@]}"; do
        dir_path="${directories[$i]}"
        dir_name=$(basename "$dir_path")
        
        log "处理进度: $((i+1))/$total_dirs - \"$dir_name\""
        
        if process_directory "$dir_path"; then
            ((success_count++))
        else
            ((failed_count++))
            failed_dirs+=("$dir_name")
        fi
        
        log "当前统计: 成功 $success_count, 失败 $failed_count"
        echo
    done
    
    # 输出最终统计
    log "=== 智能批量OCR处理完成 ==="
    log "总目录数: $total_dirs"
    log_success "成功处理: $success_count"
    
    if [ $failed_count -gt 0 ]; then
        log_error "失败处理: $failed_count"
        log_error "失败的目录: ${failed_dirs[*]}"
    else
        log_success "所有目录处理成功！"
    fi
    
    log "详细日志请查看: $LOG_FILE"
}

# 处理命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --max-workers)
            MAX_WORKERS="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_BASE_DIR="$2"
            shift 2
            ;;
        --min-png-count)
            MIN_PNG_COUNT="$2"
            shift 2
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --max-workers N      设置最大并行度 (默认: 10)"
            echo "  --output-dir DIR     设置输出目录 (默认: /Volumes/ext/SatExams/data/output)"
            echo "  --min-png-count N    设置最少PNG文件数 (默认: 1)"
            echo "  --help, -h           显示帮助信息"
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 运行主函数
main "$@"
