# StarTops

轻量级业务运维集成控制台，统一提供：

- 服务监控与启停重启
- 配置文件可视化编辑
- 工具页面聚合入口
- Web 终端（Windows/Linux）

## 主要功能

- 仪表盘总览：查看服务状态、PID、检查时间与描述
- 服务管理：注册、注销、启动、停止、重启、守护开关
- 配置管理：注册配置并在线编辑 JSON 配置
- 工具页面：注册业务页面并在统一入口打开
- 自重启控制：支持 `restart_by_self=true/false`

## 环境要求

- Python 3.8+
- Windows / Linux

## 快速开始

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 启动服务

```bash
python main.py
```

或使用参数覆盖配置：

```bash
python main.py -l 0.0.0.0 -p 8765
```

3. 打开页面

- 首页：`/`
- 仪表盘：`/dashboard`

## 核心配置

主配置文件：`configs/startops.json`

- `server.host` / `server.port`：监听地址和端口
- `server.debug`：调试模式
- `server.restart_by_self`：
	- `true`：通过部署脚本自拉起再退出
	- `false`：仅优雅退出，交给 systemd/NSSM 等外部守护拉起
- `terminal.shell`：终端 Shell（Windows 建议 `cmd.exe`）

## 目录结构

```text
main.py                # FastAPI 入口
src/                   # 业务代码
configs/               # 配置文件
deployment/            # 启动/服务/重启脚本
docs/                  # 设计文档
test/                  # 测试代码
```

## 界面截图

### 主页面

![主页面](./scheenshot/main.png)

### 服务列表

![服务列表](./scheenshot/service_list.png)

### 工具页面

![工具页面](./scheenshot/tool_page.png)

### Web 终端

![Web 终端](./scheenshot/terminal.png)

## 说明

- 详细设计见 `docs/DESIGN.md`
- 当前环境若未安装 `pytest`，测试命令会失败，请先安装后再执行
