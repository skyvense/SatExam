#!/bin/bash

# 批量OCR处理脚本
# 自动枚举output目录下的所有子目录并运行OCR处理

# 配置
OUTPUT_BASE_DIR="/Volumes/ext/SatExams/data/output"
SCRIPT_DIR="/Volumes/ext/SatExams/src/ocr"
MAX_WORKERS=10
LOG_FILE="/Volumes/ext/SatExams/data/ocr_batch.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1" | tee -a "$LOG_FILE"
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

# 处理单个目录
process_directory() {
    local dir_path="$1"
    local dir_name=$(basename "$dir_path")
    
    log "开始处理目录: $dir_name"
    
    # 切换到脚本目录
    cd "$SCRIPT_DIR"
    
    # 运行OCR处理
    log "运行OCR处理: python batch_ocr.py --target-dir \"$dir_path\" --max-workers $MAX_WORKERS"
    
    if python batch_ocr.py --target-dir "$dir_path" --max-workers $MAX_WORKERS; then
        log_success "目录 $dir_name 处理完成"
        return 0
    else
        log_error "目录 $dir_name 处理失败"
        return 1
    fi
}

# 主函数
main() {
    log "=== 批量OCR处理开始 ==="
    log "输出目录: $OUTPUT_BASE_DIR"
    log "最大并行度: $MAX_WORKERS"
    log "日志文件: $LOG_FILE"
    
    # 检查运行环境
    check_prerequisites
    
    # 激活虚拟环境
    activate_venv
    
    # 获取所有子目录
    log "扫描子目录..."
    
    # 获取所有子目录，并过滤掉空目录和系统目录
    subdirs=()
    while IFS= read -r -d '' dir; do
        dir_name=$(basename "$dir")
        
        # 跳过系统目录和隐藏目录
        if [[ "$dir_name" =~ ^\. ]] || [[ "$dir_name" =~ ^_ ]]; then
            continue
        fi
        
        # 检查目录中是否有PNG文件（排除系统文件）
        png_count=$(find "$dir" -maxdepth 1 -name "*.png" -not -name "._*" 2>/dev/null | wc -l)
        
        if [ $png_count -gt 0 ]; then
            subdirs+=("$dir")
            log "发现有效目录: $dir_name ($png_count 个PNG文件)"
        else
            log_warning "跳过空目录: $dir_name (无PNG文件)"
        fi
    done < <(find "$OUTPUT_BASE_DIR" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
    
    if [ ${#subdirs[@]} -eq 0 ]; then
        log_warning "没有找到包含PNG文件的有效目录"
        exit 0
    fi
    
    log "找到 ${#subdirs[@]} 个有效目录"
    
    # 统计信息
    total_dirs=${#subdirs[@]}
    success_count=0
    failed_count=0
    failed_dirs=()
    
    # 处理每个目录
    for i in "${!subdirs[@]}"; do
        dir_path="${subdirs[$i]}"
        dir_name=$(basename "$dir_path")
        
        log "处理进度: $((i+1))/$total_dirs - $dir_name"
        
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
    log "=== 批量OCR处理完成 ==="
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
        --help|-h)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --max-workers N    设置最大并行度 (默认: 10)"
            echo "  --output-dir DIR   设置输出目录 (默认: /Volumes/ext/SatExams/data/output)"
            echo "  --help, -h         显示帮助信息"
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
