# StarTops 轻量级业务运维集成控制台方案

**StarTops**  
始于启动，达于星顶  
*Start the service, reach the stars.*  
*Ops on the ground, StarTops in the vision.*

---

## 0. 功能说明

提供轻量级项目监控及基本运维能力。涵盖四大核心能力：

1. **统一交互入口** — 将各业务服务自带的分散的后台监控或运维页面统一管理，集中展示，减轻各服务使用不同端口及地址带来的使用成本
2. **服务健康监控** — 定期轮询检查各服务程序状态，异常时自动重启，并提供统一的手动关停、重启界面入口
3. **配置文件可视化编辑** — 将各个服务的 JSON 格式配置文件自动转换为可视化友好界面，提供必要的属性解释、范围校验等
4. **网页终端交互** — 提供 Web 版终端，实现简单系统级交互，减少对远程桌面的依赖

---

## 1. 项目定位

**StarTops** (Lightweight + Operations) 是一个小而美的轻量级运维服务。

- **轻量 (Light)**：不依赖数据库、不使用重型前端框架、不依赖 CDN，单 Python 环境运行
- **运维 (Ops)**：解决配置编辑、状态监控、服务保活、网页终端、多系统入口集成五大核心痛点

---

## 2. 核心功能架构

### 2.1 统一门户交互 (Portal Integration)

- **布局**：采用"左侧导航、右侧展示"的 Iframe 嵌套结构
- **优势**：在一个页面内集成多个业务系统的管理界面，用户无需记忆多个端口号，体验如单一系统
- **导航结构**：
  - 📊 状态总览（Dashboard）
  - 各业务服务主页（Iframe 嵌入）
  - 服务管理控制（启动/停止/重启）
  - 配置文件编辑

### 2.2 动态配置管理 (Dynamic Config Editor)

- **动态生成**：通过读取业务的 `config.json` 及配套 `config.meta.json`（配置元数据），自动转换为带校验、带说明文字的 HTML 表单
- **校验能力**：支持正则表达式校验、数值范围约束、必填项检查
- **保存回写**：表单提交后校验并写回原配置文件

### 2.3 增强型服务监控与控制 (Service Control)

- **自动保活**：定时轮询健康状态，故障时自动触发重启脚本
- **手动锁逻辑**：当用户手动点击"停止"时，系统进入静默模式，不再尝试自动拉起服务
- **交互按钮**：支持网页端一键"启动、停止、重启"各业务程序
- **状态追踪**：记录服务 PID、启动时间、最后检查时间、状态变更历史

### 2.4 网页终端交互 (Web Terminal)

- **轻便易用**：提供网页版的终端交互能力，无需安装额外客户端
- **系统级交互**：通过该终端，可以实现简单的系统级交互（如查看日志、执行脚本、检查进程等），避免对远程桌面的强依赖
- **安全控制**：支持命令白名单、操作审计日志、会话超时自动断开
- **多会话支持**：可同时开启多个终端会话，独立运行

---

## 3. 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **后端核心** | Python 3.8+ / FastAPI | 异步高性能 Web 框架 |
| **监控通信** | `httpx` | 异步 HTTP 客户端，用于健康检查 |
| **终端后端** | `asyncio` + `pty` | 伪终端支持，实现 Web Terminal |
| **WebSocket** | `websockets` / FastAPI WebSocket | 终端实时双向通信 |
| **模板渲染** | 原生 HTML 读取 | 静态 HTML 文件直接返回 |
| **前端布局** | HTML5 / CSS Flexbox | 无 JS 框架依赖，内网 100% 兼容 |
| **配置解析** | `pydantic-settings` | 类型安全的配置加载与校验 |

---

## 4. 文件结构设计

```text
star-tops/
├── main.py                      # 后端主程序入口，FastAPI 注册启动，路由定义
├── requirements.txt             # Python 依赖清单
├── README.md                    # 项目说明文档
├── docs/                        # 设计文档目录
│   └── DESIGN.md                # 本设计文档
├── deployment/                  # 部署脚本目录
│   ├── install_service.sh       # Linux 服务安装脚本
│   ├── install_service.bat      # Windows 服务安装脚本
│   ├── run.sh                   # Linux 启动脚本
│   ├── run.bat                  # Windows 启动脚本
│   ├── run.py                   # Python 启动器
│   └── ywlightops.service       # systemd 服务配置文件
├── src/                         # 源代码目录
│   ├── startops_main.py         # 程序核心逻辑，各模块调度，接口封装
│   ├── server_monitor.py        # 服务监控管理（注册、health check、启动、停止、重启）
│   ├── server_pages_manager.py  # 服务页面管理（URL 注册、页面管理）
│   ├── server_config_manager.py # 配置文件管理（路径注册、读写管理）
│   ├── config_editor_render.py  # 配置文件渲染编辑器（JSON → HTML 表单）
│   ├── web_terminal.py          # 【待实现】网页终端后端（PTY 会话管理）
│   ├── static/                  # 静态资源目录
│   │   ├── css/                 # 样式文件
│   │   ├── js/                  # JavaScript 脚本
│   │   └── images/              # 图片资源
│   ├── templates/               # HTML 模板目录
│   │   ├── index.html           # 主页面（门户框架）
│   │   ├── dashboard.html       # 状态总览页面
│   │   ├── edit_config.html     # 配置编辑页面
│   │   └── terminal.html        # 【待实现】网页终端页面
│   └── utils/                   # 工具类目录
│       ├── __init__.py
│       └── logger.py            # 日志服务（日志创建、格式化、实例化）
├── configs/                     # 配置文件目录（启动时自动创建）
│   ├── startops.json            # 主配置文件（监听地址、端口、节点获取方式等）
│   └── nodes.json               # 节点列表（当节点获取方式为 ConfigFile 时使用）
└── logs/                        # 运行日志目录（非必须，运行时自动生成）
    └── startops_YYYY-MM-DD.log  # 按日期分割的日志文件
```

**目录说明**：
- `src/` 目录集中存放所有源代码模块
- `configs/` 目录在首次启动时自动创建，若不存在则使用默认配置
- `logs/` 目录**非必须**，程序运行时根据配置自动创建，若配置关闭日志则不生成

---

## 5. 配置文件设计

### 5.1 主配置文件 `configs/startops.json`

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8300,
    "debug": false
  },
  "nodes": {
    "provider": "ConfigFile",
    "consul": {
      "host": "127.0.0.1",
      "port": 8500,
      "service_name": "startops"
    }
  },
  "logs": {
    "enabled": true,
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  },
  "terminal": {
    "enabled": true,
    "shell": "/bin/bash",
    "timeout": 300,
    "allowed_commands": []
  }
}
```

**配置项说明**：

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `server.host` | string | 监听地址 | `127.0.0.1` |
| `server.port` | int | 监听端口 | `8300` |
| `server.debug` | bool | 调试模式 | `false` |
| `nodes.provider` | string | 节点获取方式：`Consul` 或 `ConfigFile` | `ConfigFile` |
| `nodes.consul.host` | string | Consul 服务地址 | `127.0.0.1` |
| `nodes.consul.port` | int | Consul 端口 | `8500` |
| `nodes.consul.service_name` | string | Consul 服务名 | `startops` |
| `logs.enabled` | bool | 是否启用日志文件 | `true` |
| `logs.level` | string | 日志级别 | `INFO` |
| `terminal.enabled` | bool | 是否启用网页终端 | `true` |
| `terminal.shell` | string | 终端 Shell 程序 | `/bin/bash` |
| `terminal.timeout` | int | 会话超时时间（秒） | `300` |
| `terminal.allowed_commands` | array | 命令白名单（空表示不限制） | `[]` |

### 5.2 节点配置文件 `configs/nodes.json`

当 `nodes.provider` 配置为 `ConfigFile` 时，从此文件读取节点列表：

```json
{
  "nodes": [
    {
      "node_id": "node-1",
      "node_name": "节点 -1 (北京)",
      "address": "192.168.1.100",
      "port": 8300,
      "status": "healthy"
    },
    {
      "node_id": "node-2",
      "node_name": "节点 -2 (上海)",
      "address": "192.168.1.101",
      "port": 8300,
      "status": "healthy"
    }
  ]
}
```

### 5.3 启动参数优先级

启动时配置加载优先级（从高到低）：

1. **命令行参数** > 配置文件 > 默认值
2. 示例：
   ```bash
   # 命令行参数优先
   python main.py --host 0.0.0.0 --port 9000
   
   # 无参数时使用配置文件
   python main.py
   
   # 配置文件不存在时使用默认值（127.0.0.1:8300）
   ```

---

## 6. 核心逻辑实现

### 6.1 服务状态与控制逻辑

在内存中维护服务状态，区分"自动运行"与"手动停止"。

```python
# 内存状态机
SERVICES = {
    "ai_module": {
        "name": "AI 视频分析模块",
        "url": "http://127.0.0.1:8001",
        "health": "http://127.0.0.1:8001/health",
        "start_cmd": "/usr/bin/python3 /app/ai/main.py &",
        "stop_cmd": "pkill -f ai/main.py",
        "status": "Running",  # Running, Stopped (手动停止), Error
        "last_check": "N/A"
    }
}

async def monitor_task():
    async with httpx.AsyncClient() as client:
        while True:
            for s_id, svc in SERVICES.items():
                if svc["status"] == "Stopped": continue  # 手动停止不保活
                try:
                    r = await client.get(svc["health"], timeout=2.0)
                    svc["status"] = "Running" if r.status_code == 200 else "Error"
                except:
                    svc["status"] = "Error"
                    # 只有 Running 状态下发现故障才重启
                    os.system(svc["start_cmd"]) 
            await asyncio.sleep(30)
```

### 6.2 节点获取逻辑

```python
def get_nodes(config: dict) -> list:
    """获取节点列表"""
    provider = config.get("nodes", {}).get("provider", "ConfigFile")
    
    if provider == "Consul":
        # 从 Consul 获取
        consul_config = config.get("nodes", {}).get("consul", {})
        return fetch_nodes_from_consul(
            host=consul_config.get("host", "127.0.0.1"),
            port=consul_config.get("port", 8500),
            service_name=consul_config.get("service_name", "startops")
        )
    else:
        # 从配置文件获取
        nodes_file = Path("configs/nodes.json")
        if nodes_file.exists():
            with open(nodes_file) as f:
                data = json.load(f)
                return data.get("nodes", [])
        return []  # 文件不存在返回空列表
```

### 6.3 门户 UI 布局

利用 Iframe 解决多系统集成问题。

```html
<div class="sidebar">
    <div class="logo">StarTops 2.0</div>
    <nav>
        <a onclick="showPage('/dashboard')">📊 状态总览</a>
        <hr>
        {% for s_id, svc in services.items() %}
            <div class="nav-group">
                <span onclick="showPage('{{ svc.url }}')">🚀 {{ svc.name }}</span>
                <a onclick="showPage('/service/{{ s_id }}')">⚙️ 管理</a>
                <a onclick="showPage('/config/{{ s_id }}')">📝 配置</a>
            </div>
        {% endfor %}
    </nav>
</div>
<div class="main">
    <div class="top-bar">
        <span id="timestamp"></span>
        <a href="/terminal" target="_blank">🖥️ 网页终端</a>
    </div>
    <iframe id="content-frame" src="/dashboard"></iframe>
</div>
```

---

## 7. 网页终端实现方案

### 7.1 技术架构

```
┌─────────────┐     WebSocket      ┌──────────────────┐     PTY      ┌──────────────┐
│   Browser   │ ◄────────────────► │  web_terminal.py │ ◄──────────► │   /bin/bash  │
│  terminal.js│                    │  TerminalSession │              │   (Shell)    │
└─────────────┘                    └──────────────────┘              └──────────────┘
```

### 7.2 后端设计 `src/web_terminal.py`

```python
import asyncio
import pty
import os
import select
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect

class TerminalSession:
    """终端会话管理类"""
    
    def __init__(self, shell: str = "/bin/bash", timeout: int = 300):
        self.shell = shell
        self.timeout = timeout
        self.fd: Optional[int] = None
        self.pid: Optional[int] = None
        self.last_activity: float = 0
    
    async def spawn(self) -> bool:
        """创建伪终端"""
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            # 子进程：执行 Shell
            os.execvp(self.shell, [self.shell])
        else:
            # 父进程：记录 PID
            self.last_activity = asyncio.get_event_loop().time()
            return True
        return False
    
    async def read_output(self) -> Optional[str]:
        """读取终端输出"""
        if self.fd is None:
            return None
        ready, _, _ = select.select([self.fd], [], [], 0.1)
        if ready:
            try:
                return os.read(self.fd, 1024).decode('utf-8')
            except:
                return None
        return None
    
    async def write_input(self, data: str):
        """写入用户输入"""
        if self.fd is None:
            return
        os.write(self.fd, data.encode('utf-8'))
        self.last_activity = asyncio.get_event_loop().time()
    
    def check_timeout(self) -> bool:
        """检查是否超时"""
        if self.timeout <= 0:
            return False
        elapsed = asyncio.get_event_loop().time() - self.last_activity
        return elapsed > self.timeout
    
    def close(self):
        """关闭终端"""
        if self.fd is not None:
            os.close(self.fd)
        if self.pid is not None:
            os.kill(self.pid, 9)


class TerminalManager:
    """终端会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, TerminalSession] = {}
    
    async def create_session(self, session_id: str, config: dict) -> TerminalSession:
        """创建新会话"""
        session = TerminalSession(
            shell=config.get("shell", "/bin/bash"),
            timeout=config.get("timeout", 300)
        )
        await session.spawn()
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    async def remove_session(self, session_id: str):
        """移除会话"""
        session = self.sessions.pop(session_id, None)
        if session:
            session.close()
```

### 7.3 WebSocket 路由

```python
@app.websocket("/ws/terminal/{session_id}")
async def websocket_terminal(websocket: WebSocket, session_id: str):
    await websocket.accept()
    session = terminal_manager.get_session(session_id)
    
    if not session:
        await websocket.close()
        return
    
    try:
        async with asyncio.TaskGroup() as tg:
            # 读取终端输出 → 发送给前端
            async def read_loop():
                while True:
                    output = await session.read_output()
                    if output:
                        await websocket.send_text(output)
                    if session.check_timeout():
                        break
                    await asyncio.sleep(0.1)
            
            # 接收前端输入 → 写入终端
            async def write_loop():
                while True:
                    data = await websocket.receive_text()
                    await session.write_input(data)
            
            tg.create_task(read_loop())
            tg.create_task(write_loop())
    except WebSocketDisconnect:
        pass
    finally:
        await terminal_manager.remove_session(session_id)
```

### 7.4 前端设计 `templates/terminal.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>StarTops - 网页终端</title>
    <link rel="stylesheet" href="/static/css/terminal.css">
</head>
<body>
    <div class="terminal-container">
        <div class="terminal-header">
            <span>🖥️ 网页终端</span>
            <button id="disconnect">断开连接</button>
        </div>
        <div id="terminal" class="terminal-body"></div>
    </div>
    <script src="/static/js/terminal.js"></script>
    <script>
        const sessionId = generateSessionId();
        const ws = new WebSocket(`ws://${location.host}/ws/terminal/${sessionId}`);
        const term = new Terminal();
        term.open(document.getElementById('terminal'));
        
        ws.onmessage = (event) => term.write(event.data);
        term.onData((data) => ws.send(data));
    </script>
</body>
</html>
```

### 7.5 安全控制

- **命令白名单**：配置 `terminal.allowed_commands` 限制可执行命令
- **会话超时**：无操作超时后自动断开（默认 300 秒）
- **操作审计**：记录所有终端操作日志
- **权限隔离**：以当前用户权限运行，不提升权限

---

## 8. 配置编辑器核心逻辑 (Meta 驱动)

当用户访问 `/config/{service_name}` 时，后端逻辑：

1. **读数据**：读取 `config.json` 得到 `{"port": 8080}`
2. **读元数据**：读取 `config.meta.json` 得到 `{"port": {"label": "服务端口", "type": "number", "min": 1000}}`
3. **渲染**：循环生成 `<label>服务端口</label><input type="number" min="1000" value="8080">`
4. **保存**：用户点击保存，提交表单，Python 校验后写回 `config.json`

---

## 9. 部署说明

### 9.1 系统服务注册

- **Linux**: 使用 `systemd` 注册服务（`deployment/ywlightops.service`）
- **Windows**: 使用 NSSM 或任务计划程序

### 9.2 启动方式

```bash
# 方式 1：直接启动（使用配置文件）
python main.py

# 方式 2：命令行参数覆盖
python main.py --host 0.0.0.0 --port 9000

# 方式 3：使用启动脚本
./deployment/run.sh
```

### 9.3 配置文件初始化

首次启动时，若 `configs/startops.json` 不存在，自动创建默认配置：

```json
{
  "server": {"host": "127.0.0.1", "port": 8300, "debug": false},
  "nodes": {"provider": "ConfigFile"},
  "logs": {"enabled": true, "level": "INFO"},
  "terminal": {"enabled": true, "shell": "/bin/bash", "timeout": 300}
}
```

---

## 10. 待实现功能清单

| 功能 | 状态 | 说明 |
|------|------|------|
| 服务监控与健康检查 | ✅ 已完成 | `server_monitor.py` |
| 配置管理 | ✅ 已完成 | `server_config_manager.py` |
| 页面管理 | ✅ 已完成 | `server_pages_manager.py` |
| 配置渲染编辑 | ✅ 已完成 | `config_editor_render.py` |
| 主程序路由 | ✅ 已完成 | `main.py` |
| **网页终端** | ⏳ 待实现 | 需创建 `web_terminal.py` + `terminal.html` |
| Consul 集成 | ⏳ 待实现 | 节点获取的可选方式 |
| 命令白名单 | ⏳ 待实现 | 终端安全控制 |
| 操作审计日志 | ⏳ 待实现 | 终端操作记录 |

---

*文档版本：2.0*  
*最后更新：2026-03-11*
