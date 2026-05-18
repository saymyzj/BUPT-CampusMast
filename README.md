# CampusMast 校园万事达 —— 互助与众包任务平台

> Web 开发技术基础课程设计 · 阶段三 · 2026 春季学期
>
> 当前状态：文档已冻结、项目脚手架已完成，可直接并行进入前后端开发。

## 项目简介

CampusMast 是一个面向北京邮电大学校园场景的互助与众包任务平台。需求方可以发布代取快递、代买餐食、搬运重物等任务，接单方可以接单完成并获取报酬。平台围绕任务状态机、资金托管、实时通知、信用评价、任务内 IM、校园地图、AI 审核和智能推荐构建完整业务闭环。

当前冻结基线如下：

- 必做模块：任务全生命周期管理、虚拟账户与资金系统、实时通知系统、信用与评价体系
- 进阶模块：任务内 IM、北邮楼宇级校园地图、DeepSeek AI 审核、智能任务推荐
- 技术基线：`WebSocket` 实时通信、双分制加权信用模型、完整运营后台、云主机/容器主部署
- Git 基线：`main / check / feat/*`

## 当前技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS + DaisyUI + Pinia + Axios + MSW |
| 后端 | Python 3.10 + FastAPI + SQLAlchemy 2.0 + Alembic |
| 数据库 | MySQL 8.0 |
| 缓存 / 实时 | Redis + WebSocket |
| 认证 | JWT (`python-jose` + `passlib[bcrypt]`) |
| 文件存储 | 阿里云 OSS（前端直传） |
| AI 审核 | DeepSeek API |
| 本地基础设施 | Docker Compose（MySQL + Redis） |

## 当前项目结构

脚手架已经创建完毕，当前结构与分工已经对齐：

```text
CampusMast/
├── frontend/
│   ├── src/
│   │   ├── api/                # API 请求封装与模块入口
│   │   ├── components/         # 全局布局与通用组件
│   │   ├── composables/        # WebSocket 等组合式逻辑
│   │   ├── mock/               # MSW 启动入口
│   │   ├── pages/              # 页面级组件占位
│   │   ├── router/             # 路由配置
│   │   ├── stores/             # Pinia 状态仓库
│   │   ├── styles/             # 全局样式入口
│   │   ├── types/              # TypeScript 类型定义
│   │   └── utils/              # 环境变量等工具
│   ├── .env.example
│   ├── .env.production.example
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── dependencies/       # 鉴权、数据库依赖注入
│   │   ├── models/             # ORM 模型骨架
│   │   ├── routers/            # HTTP 路由骨架
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── services/           # 核心业务服务骨架
│   │   ├── utils/              # JWT / Redis / OSS / 响应工具
│   │   ├── websockets/         # WebSocket 网关与事件定义
│   │   ├── config.py           # 配置管理
│   │   └── main.py             # FastAPI 应用入口
│   ├── alembic/
│   ├── tests/
│   ├── .env.example
│   ├── .env.production.example
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
│
├── docs/
│   ├── 产品需求文档.md
│   ├── 系统架构设计.md
│   ├── 数据库设计.md
│   ├── API接口规范.yaml
│   ├── 团队分工文档.md
│   ├── Git协作指南.md
│   └── designs/
│       └── 2026-04-14-阶段三文档冻结.md
│
├── deploy/
│   └── nginx.conf
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

## 本地开发启动

### 1. 启动 MySQL 和 Redis（仅本地开发）

```bash
docker compose up -d
```

### 2. 启动前端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

默认地址：

- 前端：`http://localhost:5173`

### 3. 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 9000
```

默认地址：

- 后端：`http://localhost:9000`
- 健康检查：`http://localhost:9000/healthz`

> 当前脚手架阶段已配置 Alembic、ORM、Router、Service、WebSocket 网关和最小冒烟测试。
> 数据库迁移脚本仍需在你和 B 同学完善模型后生成。

## 生产 / 演示环境部署

当前仓库已经补齐“单台 Linux 服务器可部署”的最小交付物：

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `docker-compose.prod.yml`
- `deploy/nginx.conf`
- `backend/.env.production.example`
- `frontend/.env.production.example`

推荐部署方式：

```text
单台 Linux 云服务器
  ├── Nginx（80 端口）
  ├── 前端静态站点容器
  ├── FastAPI 后端容器
  ├── MySQL 容器（Docker volume 持久化）
  └── Redis 容器（Docker volume 持久化）
```

生产/演示环境启动步骤：

```bash
# 1. 复制并填写生产环境变量
cp backend/.env.production.example backend/.env.production
cp frontend/.env.production.example frontend/.env.production

# 2. 按实际域名和密码修改配置后启动
docker compose -f docker-compose.prod.yml up -d --build

# 3. 当迁移脚本生成后，执行数据库迁移
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

部署约束与说明：

- 本地 `docker-compose.yml` 只用于开发，不用于服务器直接上线
- 生产 `docker-compose.prod.yml` 使用 Docker volume 持久化 MySQL/Redis 数据
- MySQL 和 Redis 在生产编排中不直接暴露公网端口
- 反向代理统一由 `deploy/nginx.conf` 处理，根路径走前端，`/api` 和 `/ws` 走后端
- 若后续预算允许，也可把 MySQL/Redis 替换成托管服务，但当前单机方案已足够支撑课程项目

## 当前分工摘要

| 成员 | 当前职责 | 开发分支 |
|------|------|------|
| 组长 / C | 文档冻结、静态 HTML 原型、后端基础设施、认证、WebSocket、后台、部署、最终集成 | `feat/c-infra` |
| A | 前端工程实现、Vue 页面/组件、路由、状态管理、MSW、前端联调 | `feat/a-frontend` |
| B | 任务状态机、钱包事务、双分制信用模型、评价、智能推荐、核心测试 | `feat/b-backend-core` |

完整说明见：[团队分工文档](docs/团队分工文档.md)。

## Git 协作基线

固定分支结构：

```text
main
└── check
    ├── feat/a-frontend
    ├── feat/b-backend-core
    └── feat/c-infra
```

固定规则：

- 所有开发分支统一向 `check` 提交 PR
- 仅组长 review 并合并到 `check`
- 阶段检查或里程碑时，再将 `check` 合并到 `main`

完整说明见：[Git协作指南](docs/Git协作指南.md)。

## 文档索引

| 文档 | 说明 |
|------|------|
| [产品需求文档](docs/产品需求文档.md) | 冻结后的业务范围、状态机、信用体系、后台范围 |
| [系统架构设计](docs/系统架构设计.md) | 云主机/容器主部署、Redis、WebSocket、DeepSeek、推荐链路 |
| [数据库设计](docs/数据库设计.md) | 双信用分、IM、地图、审核、配置与推荐数据模型 |
| [API 接口规范](docs/API接口规范.yaml) | 冻结版 HTTP 接口 + WebSocket 事件契约 |
| [团队分工文档](docs/团队分工文档.md) | 当前 owner、边界、高耦合规避方式 |
| [Git协作指南](docs/Git协作指南.md) | `main / check / feat/*` 流程 |
| [阶段三文档冻结设计说明](docs/designs/2026-04-14-阶段三文档冻结.md) | 本轮冻结工作的背景、TODO 与验证结果 |

## 提供给成员 A 的 AI Prompt

下面这段可以直接发给 A 自己使用的 AI 助手，帮助他快速开始前端开发：

```text
你正在参与 CampusMast 项目的前端开发，你的角色是 A 同学。

请严格遵守以下上下文：

1. 项目根目录中已有完整脚手架，前端目录是 `frontend/`。
2. 你只负责“前端工程实现”，不负责重新定义页面结构、交互流程、接口字段名。
3. 页面结构、核心交互和字段含义以组长提供的静态 HTML 原型和冻结文档为准。
4. 你的主要参考文档：
   - `docs/产品需求文档.md`
   - `docs/API接口规范.yaml`
   - `docs/团队分工文档.md`
5. 你的工作边界：
   - 实现 Vue 页面和组件
   - 完善 Router、Pinia、Axios、MSW、WebSocket 客户端
   - 可以微调样式、响应式细节和组件拆分
   - 不得擅自修改接口、状态机、信用分字段、WebSocket 事件名
6. 你当前优先级最高的页面：
   - `frontend/src/pages/TaskHallPage.vue`
   - `frontend/src/pages/PostTaskPage.vue`
   - `frontend/src/pages/TaskDetailPage.vue`
   - `frontend/src/pages/CampusMapPage.vue`
   - `frontend/src/pages/ChatPage.vue`
7. 你需要优先补的能力：
   - 任务大厅列表 + 推荐入口 + 地图/列表切换
   - 发布任务表单 + 楼宇选择 + 审核反馈提示
   - 任务详情状态流转 UI
   - 聊天会话页与消息窗口
   - 校园地图楼宇点位展示
8. 开发原则：
   - 优先基于现有脚手架文件继续写，不要另起炉灶
   - API 调用统一放在 `frontend/src/api/`
   - WebSocket 封装优先复用 `frontend/src/composables/useWebSocket.ts`
   - 状态管理统一放在 `frontend/src/stores/`
   - 页面只承载展示和交互，不直接裸写复杂网络逻辑
9. 输出要求：
   - 每次先说明你要改哪些文件
   - 改完后说明与冻结文档的对应关系
   - 如果发现接口或字段设计问题，不要擅自修改，直接给出 RFC 建议

请先从“任务大厅页 + 地图页”的前端实现开始。
```

## 提供给成员 B 的 AI Prompt

下面这段可以直接发给 B 自己使用的 AI 助手，帮助他快速开始后端核心业务开发：

```text
你正在参与 CampusMast 项目的后端核心业务开发，你的角色是 B 同学。

请严格遵守以下上下文：

1. 项目根目录中已有完整脚手架，后端目录是 `backend/`。
2. 你只负责核心业务：任务状态机、钱包事务、双分制信用模型、评价系统、智能推荐与核心测试。
3. 你不负责认证、部署、后台系统配置页面、文档拍板。
4. 你的主要参考文档：
   - `docs/产品需求文档.md`
   - `docs/数据库设计.md`
   - `docs/API接口规范.yaml`
   - `docs/团队分工文档.md`
5. 你的主要文件边界：
   - `backend/app/routers/task.py`
   - `backend/app/routers/wallet.py`
   - `backend/app/routers/credit.py`
   - `backend/app/services/task_service.py`
   - `backend/app/services/wallet_service.py`
   - `backend/app/services/credit_service.py`
   - `backend/app/services/recommendation_service.py`
   - `backend/tests/test_task.py`
   - `backend/tests/test_wallet.py`
   - `backend/tests/test_credit.py`
   - `backend/tests/test_recommendation.py`
6. 你的冻结约束：
   - 任务状态机只能使用：
     `PENDING / IN_PROGRESS / PENDING_REVIEW / COMPLETED / DISPUTED / CANCELLED / EXPIRED / CLOSED_BY_ADMIN`
   - 接单门槛默认 `helperCreditScore >= 60`
   - 钱包事务必须保证冻结、解冻、结算一致性
   - 信用分采用双分制：
     `requesterCreditScore / helperCreditScore / overallCreditScore`
   - 推荐采用规则加权，不做机器学习
   - 不得擅自改 API 字段、状态机枚举、信用分字段、推荐结果字段
7. 你当前优先级最高的任务：
   - 实现任务状态机主流程
   - 实现钱包冻结/解冻/结算事务
   - 实现互评与信用分快照计算
   - 实现推荐得分计算
   - 补单元测试和并发场景测试
8. 开发原则：
   - Service 层承载核心业务逻辑，Router 层尽量薄
   - 并发接单必须考虑事务和锁
   - 评价和信用分更新必须可追踪
   - 推荐逻辑先清晰可解释，再考虑优化
9. 输出要求：
   - 每次先说明改哪些文件
   - 改完后明确说明对应了哪条冻结文档
   - 如果发现要改状态机、字段或接口，不能直接改，必须先给 RFC 建议

请先从“任务状态机 + 钱包事务”开始。
```

## 远程仓库

`https://github.com/saymyzj/BUPT-CampusMast`

## License

本项目为北京邮电大学 Web 开发技术基础课程设计作品。
