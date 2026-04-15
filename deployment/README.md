# Startops 部署和系统服务管理

本目录包含 Startops 的启动脚本和系统服务注册脚本。

## 目录结构

```
deployment/
├── run.py                    # Python 启动脚本（跨平台）
├── run.bat                   # Windows 批处理启动脚本
├── run.sh                    # Linux/Mac Shell 启动脚本
├── Startops.service        # Linux systemd 服务文件
├── install_service.sh        # Linux 系统服务安装脚本
├── install_service.bat       # Windows 系统服务安装脚本
└── README.md                 # 本文件
```

---

## 快速启动

### Windows

```batch
run.bat
```

### Linux/Mac

```bash
bash run.sh
```

### Python（通用）

```bash
python run.py
```

---

## 系统服务安装（Linux）

### 前置要求

- Linux 系统（CentOS/Ubuntu/Debian 等）
- systemd（大多数现代 Linux 发行版都已包含）
- Python 3.8+
- 需要 root 权限

### 安装步骤

#### 1. 运行安装脚本

```bash
sudo bash deployment/install_service.sh install
```

该脚本将：
- 检查系统要求
- 创建 `Startops` 系统用户和组
- 复制项目文件到 `/opt/Startops`
- 安装 Python 依赖
- 复制 systemd 服务文件
- 启用服务自动启动

#### 2. 启动服务

```bash
# 启动服务
sudo systemctl start Startops

# 查看状态
sudo systemctl status Startops

# 查看实时日志
sudo journalctl -u Startops -f
```

#### 3. 验证安装

服务安装完成后，应该可以访问：
```
http://localhost:8000
```

### 常用命令

```bash
# 启动服务
sudo systemctl start Startops

# 停止服务
sudo systemctl stop Startops

# 重启服务
sudo systemctl restart Startops

# 查看服务状态
sudo systemctl status Startops

# 启用开机自启
sudo systemctl enable Startops

# 禁用开机自启
sudo systemctl disable Startops

# 查看实时日志
sudo journalctl -u Startops -f

# 查看历史日志
sudo journalctl -u Startops --lines=50

# 查看完整日志
sudo journalctl -u Startops -a
```

### 卸载服务

```bash
sudo bash deployment/install_service.sh uninstall
```

该脚本将：
- 停止运行中的服务
- 禁用开机自启
- 删除 systemd 服务文件
- 可选：删除系统用户和组

### Linux 服务文件说明

`Startops.service` 文件配置：

```ini
[Unit]
Description=Startops 2.0 - Lightweight Ops Console
# 服务描述
After=network.target
# 网络启动后再启动此服务

[Service]
Type=simple
# 简单类型的服务
User=Startops
Group=Startops
# 运行用户和组
WorkingDirectory=/opt/Startops
# 工作目录

ExecStart=/usr/bin/python3 /opt/Startops/main.py
# 启动命令

Restart=on-failure
RestartSec=10
# 失败后自动重启，间隔10秒

StandardOutput=journal
StandardError=journal
# 输出到系统日志

KillMode=process
KillSignal=SIGTERM
# 进程终止方式

[Install]
WantedBy=multi-user.target
# 在多用户启动级别启用
```

### 自动重启机制

systemd 服务配置中包含：
```ini
Restart=on-failure
RestartSec=10
```

这意味着：
- **Restart=on-failure**：服务异常退出时自动重启
- **RestartSec=10**：重启间隔为 10 秒

如果需要无条件重启，可修改为：
```ini
Restart=always
```

---

## 系统服务安装（Windows）

### 前置要求

- Windows 7 / Windows Server 2008 或更高版本
- Python 3.8+
- 需要管理员权限

### 方法一：使用脚本（推荐）

#### 1. 运行安装脚本

```batch
# 右键选择"以管理员身份运行"
install_service.bat install
```

#### 2. 启动服务

```batch
# 启动服务
net start Startops

# 停止服务
net stop Startops

# 查看服务状态
sc query Startops
```

### 方法二：使用 NSSM（更推荐）

NSSM 是一个强大的 Windows 服务管理工具。

#### 1. 下载 NSSM

访问 https://nssm.cc/download 下载 NSSM

#### 2. 安装 NSSM

```batch
# 将 nssm.exe 放在 Program Files 下
mkdir "C:\Program Files\nssm"
copy nssm.exe "C:\Program Files\nssm\"
```

#### 3. 创建服务

```batch
"C:\Program Files\nssm\nssm.exe" install Startops "C:\path\to\python.exe" "C:\path\to\main.py"
"C:\Program Files\nssm\nssm.exe" set Startops AppDirectory "C:\Startops"
"C:\Program Files\nssm\nssm.exe" set Startops AppRestartDelay 5000
```

#### 4. 启动服务

```batch
net start Startops
```

#### 5. 管理服务

```batch
# 查看 NSSM 服务编辑窗口
"C:\Program Files\nssm\nssm.exe" edit Startops

# 删除服务
"C:\Program Files\nssm\nssm.exe" remove Startops confirm
```

### Windows 服务常用命令

```batch
# 查看所有服务
sc query type= service

# 查看特定服务
sc query Startops

# 启动服务
net start Startops

# 停止服务
net stop Startops

# 设置服务为自动启动
sc config Startops start= auto

# 设置服务为手动启动
sc config Startops start= demand

# 查看服务配置
sc qc Startops

# 删除服务
sc delete Startops

# 查看事件日志
eventvwr
```

---

## 故障排查

### Linux

#### 服务无法启动

```bash
# 查看详细错误日志
sudo journalctl -u Startops -n 50 -p err

# 尝试直接运行看是否有错误
cd /opt/Startops
python3 main.py
```

#### 权限问题

```bash
# 检查文件所有权
ls -la /opt/Startops

# 修复所有权
sudo chown -R Startops:Startops /opt/Startops

# 修复权限
sudo chmod -R 755 /opt/Startops
```

#### 端口被占用

```bash
# 查看占用端口 8000 的进程
sudo lsof -i :8000

# 杀死占用端口的进程
sudo kill -9 <PID>
```

### Windows

#### 查看事件日志

```batch
# 打开事件查看器
eventvwr

# 在"Windows 日志" -> "系统"中查找 Startops 相关错误
```

#### 端口被占用

```batch
# 查看占用端口 8000 的进程
netstat -ano | findstr :8000

# 根据 PID 查看进程
tasklist | findstr <PID>

# 杀死进程
taskkill /PID <PID> /F
```

---

## 监控和日志

### Linux

```bash
# 实时监控日志
sudo journalctl -u Startops -f

# 查看最近 100 行
sudo journalctl -u Startops -n 100

# 查看特定时间范围的日志
sudo journalctl -u Startops --since "2024-01-28 10:00:00" --until "2024-01-28 11:00:00"

# 导出日志
sudo journalctl -u Startops > Startops.log
```

### Windows

应用日志在：
```
%INSTALL_DIR%\logs\
```

可以使用文本编辑器查看。

---

## 性能调优

### Linux

编辑 `/etc/systemd/system/Startops.service` 配置：

```ini
[Service]
# 增加文件描述符限制
LimitNOFILE=65536

# 增加进程限制
LimitNPROC=4096

# 增加内存限制（可选）
MemoryLimit=2G

# 增加 CPU 配额（可选）
CPUQuota=80%
```

然后重新加载配置：
```bash
sudo systemctl daemon-reload
sudo systemctl restart Startops
```

### Windows

通过"服务"管理工具或 NSSM 设置：

```batch
# 通过 NSSM 设置内存限制
"C:\Program Files\nssm\nssm.exe" set Startops AppThrottle 1024

# 设置优先级
"C:\Program Files\nssm\nssm.exe" set Startops AppPriority high
```

---

## 备份和恢复

### 备份服务配置

```bash
# Linux
sudo cp /etc/systemd/system/Startops.service ~/Startops.service.bak
sudo cp -r /opt/Startops ~/Startops.bak
```

### 恢复服务配置

```bash
# Linux
sudo cp ~/Startops.service.bak /etc/systemd/system/Startops.service
sudo cp -r ~/Startops.bak /opt/Startops
sudo chown -R Startops:Startops /opt/Startops
sudo systemctl daemon-reload
sudo systemctl restart Startops
```

---

## 参考资源

- [systemd 官方文档](https://www.freedesktop.org/wiki/Software/systemd/)
- [NSSM 官方网站](https://nssm.cc/)
- [Linux 服务管理](https://wiki.archlinux.org/title/Systemd)
- [Windows 服务创建](https://docs.microsoft.com/en-us/windows/win32/services/creating-a-service)

---

## 许可证

Startops 2.0 - Lightweight Ops Console
