#!/bin/bash
# Startops Linux 系统服务安装脚本
# 用于注册 Startops 为 systemd 服务
# 
# 用法:
#   sudo bash install_service.sh [install|uninstall|status]
#
# 示例:
#   sudo bash install_service.sh install      # 安装服务
#   sudo bash install_service.sh uninstall    # 卸载服务
#   sudo bash install_service.sh status       # 查看服务状态

set -e

# 配置参数
INSTALL_DIR="/opt/Startops"
SERVICE_USER="Startops"
SERVICE_GROUP="Startops"
SERVICE_NAME="Startops"
SERVICE_FILE="/etc/systemd/system/Startops.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查是否以 root 身份运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本必须以 root 身份运行"
        exit 1
    fi
}

# 检查系统要求
check_system() {
    print_info "检查系统要求..."
    
    # 检查 systemd
    if ! command -v systemctl &> /dev/null; then
        print_error "系统未安装 systemd，无法继续"
        exit 1
    fi
    
    # 检查 Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "系统未安装 Python3，请先安装 Python 3.8+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    print_info "检测到 Python 版本: $PYTHON_VERSION"
    
    print_success "系统检查通过"
}

# 创建用户和组
create_user() {
    print_info "创建系统用户和组..."
    
    # 创建组
    if ! getent group "$SERVICE_GROUP" > /dev/null; then
        groupadd -r "$SERVICE_GROUP"
        print_success "创建组: $SERVICE_GROUP"
    else
        print_info "组已存在: $SERVICE_GROUP"
    fi
    
    # 创建用户
    if ! getent passwd "$SERVICE_USER" > /dev/null; then
        useradd -r -g "$SERVICE_GROUP" -d "$INSTALL_DIR" -s /sbin/nologin -c "Startops service user" "$SERVICE_USER"
        print_success "创建用户: $SERVICE_USER"
    else
        print_info "用户已存在: $SERVICE_USER"
    fi
}

# 准备安装目录
prepare_directory() {
    print_info "准备安装目录..."
    
    if [ ! -d "$INSTALL_DIR" ]; then
        mkdir -p "$INSTALL_DIR"
        print_success "创建目录: $INSTALL_DIR"
    fi
    
    # 复制项目文件（假设脚本在 deployment 目录中）
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    if [ -f "$PROJECT_ROOT/main.py" ]; then
        print_info "复制项目文件到 $INSTALL_DIR..."
        
        # 复制所有 Python 文件
        cp "$PROJECT_ROOT"/*.py "$INSTALL_DIR/" 2>/dev/null || true
        
        # 复制其他必要目录
        for dir in utils templates static configs; do
            if [ -d "$PROJECT_ROOT/$dir" ]; then
                cp -r "$PROJECT_ROOT/$dir" "$INSTALL_DIR/"
            fi
        done
        
        # 创建 logs 目录
        mkdir -p "$INSTALL_DIR/logs"
        
        # 复制依赖文件
        if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
            cp "$PROJECT_ROOT/requirements.txt" "$INSTALL_DIR/"
        fi
        
        print_success "项目文件复制完成"
    else
        print_warning "未找到项目文件，假设已手动配置"
    fi
    
    # 设置目录权限
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR/main.py"
    
    print_success "目录权限已设置"
}

# 安装依赖
install_dependencies() {
    print_info "检查并安装 Python 依赖..."
    
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        python3 -m pip install --upgrade pip -q
        python3 -m pip install -r "$INSTALL_DIR/requirements.txt" -q
        print_success "Python 依赖安装完成"
    else
        print_warning "未找到 requirements.txt，跳过依赖安装"
    fi
}

# 安装服务
install_service() {
    print_info "安装 systemd 服务..."
    
    check_root
    check_system
    create_user
    prepare_directory
    install_dependencies
    
    # 复制 service 文件
    print_info "配置服务文件..."
    
    SCRIPT_SERVICE="$SCRIPT_DIR/Startops.service"
    if [ -f "$SCRIPT_SERVICE" ]; then
        cp "$SCRIPT_SERVICE" "$SERVICE_FILE"
        print_success "服务文件已安装: $SERVICE_FILE"
    else
        print_error "找不到 Startops.service 文件"
        exit 1
    fi
    
    # 重新加载 systemd 配置
    systemctl daemon-reload
    print_success "systemd 配置已重新加载"
    
    # 启用服务自动启动
    systemctl enable "$SERVICE_NAME"
    print_success "服务已启用自动启动"
    
    print_success "=========================================="
    print_success "Startops 服务安装完成！"
    print_success "=========================================="
    echo ""
    echo "后续命令："
    echo "  启动服务: sudo systemctl start $SERVICE_NAME"
    echo "  停止服务: sudo systemctl stop $SERVICE_NAME"
    echo "  重启服务: sudo systemctl restart $SERVICE_NAME"
    echo "  查看状态: sudo systemctl status $SERVICE_NAME"
    echo "  查看日志: sudo journalctl -u $SERVICE_NAME -f"
    echo "  禁用自动启动: sudo systemctl disable $SERVICE_NAME"
    echo ""
}

# 卸载服务
uninstall_service() {
    print_info "卸载 systemd 服务..."
    
    check_root
    
    # 停止服务
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_info "停止服务..."
        systemctl stop "$SERVICE_NAME"
        print_success "服务已停止"
    fi
    
    # 禁用服务
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        systemctl disable "$SERVICE_NAME"
        print_success "服务已禁用"
    fi
    
    # 删除服务文件
    if [ -f "$SERVICE_FILE" ]; then
        rm "$SERVICE_FILE"
        print_success "服务文件已删除: $SERVICE_FILE"
    fi
    
    # 重新加载 systemd 配置
    systemctl daemon-reload
    print_success "systemd 配置已重新加载"
    
    # 删除用户和组（可选，保留以保持权限）
    print_info "是否删除 $SERVICE_USER 用户和组？(y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        userdel "$SERVICE_USER" 2>/dev/null || true
        groupdel "$SERVICE_GROUP" 2>/dev/null || true
        print_success "用户和组已删除"
    fi
    
    print_success "=========================================="
    print_success "Startops 服务卸载完成！"
    print_success "=========================================="
}

# 查看服务状态
show_status() {
    print_info "Startops 服务状态："
    echo ""
    
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        print_success "自动启动: 已启用"
    else
        print_warning "自动启动: 已禁用"
    fi
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "运行状态: 运行中"
    else
        print_warning "运行状态: 已停止"
    fi
    
    echo ""
    print_info "详细状态:"
    systemctl status "$SERVICE_NAME" --no-pager || true
}

# 主程序
main() {
    ACTION="${1:-help}"
    
    case "$ACTION" in
        install)
            install_service
            ;;
        uninstall)
            uninstall_service
            ;;
        status)
            show_status
            ;;
        *)
            echo "Startops Linux 系统服务管理脚本"
            echo ""
            echo "用法: $0 <命令>"
            echo ""
            echo "可用命令:"
            echo "  install     - 安装并启用 Startops 系统服务"
            echo "  uninstall   - 卸载 Startops 系统服务"
            echo "  status      - 显示服务状态"
            echo "  help        - 显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  sudo bash $0 install"
            echo "  sudo bash $0 status"
            echo "  sudo bash $0 uninstall"
            echo ""
            echo "服务管理命令:"
            echo "  sudo systemctl start Startops      - 启动服务"
            echo "  sudo systemctl stop Startops       - 停止服务"
            echo "  sudo systemctl restart Startops    - 重启服务"
            echo "  sudo systemctl status Startops     - 查看状态"
            echo "  sudo journalctl -u Startops -f     - 查看实时日志"
            echo ""
            exit 0
            ;;
    esac
}

# 运行主程序
main "$@"
