# CampusMast 校园万事达

CampusMast 是一个面向校园场景的互助与众包任务平台。用户可以发布代取快递、代买餐食、搬运物品等任务，也可以接单完成任务并获得报酬。

当前项目基线是“本地测试 / 本地验收版”：不维护生产上线部署，也不使用 Alembic 数据库迁移。数据库结构由后端 SQLAlchemy 模型直接建表，图片上传保存到后端本地目录。

当前项目包含前端、后端、数据库、缓存、本地上传和本地演示数据脚本，主要功能覆盖：

- 任务发布、接单、提交证明、确认完成、取消、争议处理
- 钱包余额、资金冻结、结算和流水
- 通知、任务内聊天、信用评价
- 校园地图、智能推荐、AI 审核、本地图片上传与后台管理

## 依赖

本地开发建议使用 Docker 只启动 MySQL 和 Redis，前后端仍在本机运行。

需要安装：

- Docker / Docker Compose
- Python 3.10+
- Node.js 18+
- npm

主要技术栈：

- 前端：Vue 3 + TypeScript + Vite + Pinia + Axios
- 后端：FastAPI + SQLAlchemy 2.0 + PyMySQL
- 数据库：MySQL 8.0
- 缓存 / 实时：Redis + WebSocket
- 上传：后端本地 `uploads/` 目录
- 审核：DeepSeek API，可不配置，未配置时走关键词兜底

## 启动

### 1. 启动 MySQL 和 Redis

在项目根目录执行：

```bash
docker compose up -d
```

本地 `docker-compose.yml` 只启动 MySQL 和 Redis：

- MySQL：`127.0.0.1:3306`
- Redis：`127.0.0.1:6379`

### 2. 配置后端环境变量

```bash
cd backend
cp .env.example .env
```

默认 `.env.example` 已按本地 Docker MySQL / Redis 配好：

```env
DATABASE_URL=mysql+pymysql://campusmast:campusmast@127.0.0.1:3306/campusmast
REDIS_URL=redis://127.0.0.1:6379/0
LOCAL_UPLOAD_DIR=uploads
```

如需真实 DeepSeek 审核，在 `backend/.env` 中配置 `DEEPSEEK_API_KEY`。

### 3. 安装并启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.init_data
uvicorn app.main:app --reload --port 9000
```

后端地址：

- API：`http://localhost:9000`
- 健康检查：`http://localhost:9000/healthz`

初始化脚本说明：

- `python -m app.init_data`：清空并重建数据库，只保留 `admin / 12345` 和 `user01-user10 / 12345`，钱包余额均为 `200.00`。
- `python -m app.demo_data`：清空并重建数据库，根据当前服务层和 Schema 生成较完整的演示数据，适合联调展示。

上传说明：

- 发布任务上传的图片会保存到 `backend/uploads/`，并通过 `http://localhost:9000/uploads/...` 访问。
- `backend/uploads/` 是本地运行数据，不提交到仓库。

### 4. 安装并启动前端

另开一个终端，在项目根目录执行：

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

前端地址：

- `http://localhost:5173`

### 5. 常用测试账号

初始化后可直接登录：

```text
管理员：admin / 12345
普通用户：user01 / 12345
普通用户：user02 / 12345
...
普通用户：user10 / 12345
```

如果前端需要更丰富的任务、通知、聊天、钱包、审核和评价数据，先在后端目录执行：

```bash
python -m app.demo_data
```
