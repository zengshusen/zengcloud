# ZengCloud

面向真实运维现场的智能运维平台。把资产登记、平台管理、可观测性、事件中心、任务中心、工单系统、AIOps 与 RBAC 组织成**可审计、可确认、可执行**的工作流。

## 产品定位

ZengCloud 不是单一告警看板或脚本仓库，而是把「看见问题 → 确认责任 → 审批执行 → 复盘留痕」串成闭环：

- **可审计**：操作、审批、执行、模型调用均有记录
- **可确认**：关键变更与发布需人工确认与权限校验
- **可执行**：主机 / K8s 任务、工单动作、智能体 Action 可真正落地到现场

## 功能模块

| 模块 | 说明 |
|------|------|
| **运行概览** | 智能运维驾驶舱，聚焦 SLA、产品 SLA、工单及时率、告警与风险项 |
| **资产登记** | 维护一级业务、环境、资产、运维负责人与项目负责人 |
| **平台管理** | K8s 集群、kubeconfig 引导、容器环境、容器与镜像管理 |
| **可观测性** | 平台总览、监控看板、日志中心、告警中心 |
| **任务中心** | 主机与 K8s 执行任务、批量命令、Playbook、任务模板与执行记录 |
| **工单系统** | 应用发布、审批流、SQL 审计与事务工单 |
| **事件中心** | 平台事件、外部事件、事件环境、事件源与排障复盘时间线 |
| **AIOps** | 智能助手、知识图谱、模型 / MCP / Skill / Action 配置、智能体审计 |
| **权限审计** | 后端 RBAC，前端路由 / 菜单 / 按钮与 WebSocket 权限统一控制 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Django、Django REST framework、Channels、Daphne |
| 前端 | Vue 3、Vue Router、Pinia、Element Plus、ECharts、Vite |
| 数据库 | MySQL |
| 缓存与实时通信 | Redis、Channels Redis |
| 平台集成 | Kubernetes API、Docker、SSH、Prometheus 兼容接口、Loki、ELK、ClickHouse |

## 仓库结构

```text
zengcloud/
├── backend/                 # Django 后端
│   ├── apps/accounts/       # 登录认证（JWT）
│   ├── config/              # 项目配置、ASGI/WSGI、路由
│   ├── requirements.txt
│   └── manage.py
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── views/           # 登录页、运行概览等
│   │   ├── stores/          # Pinia（含 auth）
│   │   ├── router/          # 路由与登录守卫
│   │   └── api/             # REST 客户端
│   └── vite.config.ts
├── docs/                    # 架构与设计文档
│   └── ARCHITECTURE.md
└── README.md
```

## 架构速览

```text
┌─────────────────────────────────────────────────────────────┐
│                     Vue 3 控制台（Vite）                      │
│         路由 / 菜单 / 按钮权限  ×  Pinia  ×  ECharts           │
└───────────────┬─────────────────────────────┬───────────────┘
                │ REST / WebSocket            │
┌───────────────▼─────────────────────────────▼───────────────┐
│              Django + DRF + Channels（Daphne）               │
│     RBAC · 审计日志 · 审批/确认 · 任务调度 · AIOps 编排        │
└─┬──────┬──────┬──────┬──────┬──────┬──────┬────────────────┘
  │      │      │      │      │      │      │
  ▼      ▼      ▼      ▼      ▼      ▼      ▼
MySQL  Redis  K8s  Docker  SSH  Prometheus  Loki/ELK/CH
```

更完整的分层、数据流、权限与模块边界见：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 设计原则

1. **现场优先**：能力围绕真实运维动作（登录集群、下发命令、发版、审 SQL、复盘）设计，而非仅展示指标。
2. **权限统一**：同一套 RBAC 同时约束 API、页面路由、菜单、按钮与 WebSocket。
3. **变更可确认**：发布、批量命令、高危 Action 必须经过工单 / 审批 / 二次确认之一。
4. **链路可追溯**：从告警 / 事件 → 工单 / 任务 → 执行结果 → 复盘时间线可贯通。
5. **智能可审计**：模型、MCP、Skill、Action 的调用与结果进入智能体审计，避免黑盒运维。

## 快速开始

本地默认使用 **SQLite**（无需 MySQL）。生产可在 `backend/.env` 中设置 `DB_ENGINE=mysql`。

### 1. 后端

必须先激活仓库根目录的 `.venv`，不要用系统全局 `python`（否则会缺依赖如 `dotenv`）。

```powershell
# 在仓库根目录（若尚未创建虚拟环境）
cd D:\zengcloud
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

cd backend
copy .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

未激活时也可直接指定解释器：

```powershell
cd D:\zengcloud\backend
D:\zengcloud\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

开发账号（首次初始化已创建时可自行重置）：

- 用户名：`admin`
- 密码：`admin123`

认证接口：

- `POST /api/auth/login/` — 登录，返回 JWT `access` / `refresh` 与用户信息
- `GET /api/auth/me/` — 当前用户
- `POST /api/auth/refresh/` — 刷新 access token
- `POST /api/auth/logout/` — 退出（客户端清 token）

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173 ，未登录会进入登录页。Vite 已将 `/api` 代理到 `http://127.0.0.1:8000`。

依赖服务（按需）：MySQL、Redis；以及 Kubernetes、Prometheus、Loki / ELK、ClickHouse 等外部集成。

## GitHub 上传（免手写命令）

双击根目录 **`打开GitHub上传面板.bat`**，在浏览器里用按钮完成 `init / remote / add / commit / push`。说明见 [tools/github-panel/README.md](tools/github-panel/README.md)。

## 文档

- [架构说明](docs/ARCHITECTURE.md) — 分层、模块边界、权限模型、集成与数据流
- [MySQL 初始化 SQL](docs/sql/init_zengcloud.sql) — 按当前脚手架生成的建库建表与种子数据
- 后续可补充：API 约定、部署手册、贡献指南

## 许可

内部项目，使用范围以团队约定为准。
