# B 成员任务汇报

汇报日期：2026-05-14  
负责范围：后端核心业务，包括任务状态机、钱包事务、双分制信用模型、评价系统、规则推荐、争议裁决联动与核心测试。

## 1. 完成了什么

### 1.1 任务状态机与任务 API

- 完成任务状态流转：`PENDING / IN_PROGRESS / PENDING_REVIEW / COMPLETED / DISPUTED / CANCELLED / EXPIRED / CLOSED_BY_ADMIN`。
- 实现发布任务冻结赏金、接单、提交完成证明、确认完成、取消、放弃、过期、发起争议等核心流程。
- 补齐任务大厅冻结 API 查询参数：`category / keyword / buildingCode / nearBuildingCode / sortBy / page / limit`。
- 补齐“我的发布”和“我的接单”接口。
- 接单门槛改为优先读取 `system_configs`，默认回退 `helperCreditScore >= 60`。

对应文件：

- `backend/app/routers/task.py`
- `backend/app/services/task_service.py`
- `backend/tests/test_task.py`

### 1.2 钱包事务与资金一致性

- 完成钱包充值、提现、冻结、解冻、结算、拆分结算。
- 任务创建、取消、完成、争议裁决中的资金流与任务状态保持同一业务事务。
- 增加 `transactions.settlement_key`，用于任务结算幂等保护。
- 明确 `SETTLE_SPLIT.amount` 语义为“裁决分配额”，拆分结算审计按 `related_task_id` 合并查看。

对应文件：

- `backend/app/routers/wallet.py`
- `backend/app/services/wallet_service.py`
- `backend/tests/test_wallet.py`
- `backend/alembic/versions/20260514_02_add_wallet_settlement_key.py`

### 1.3 双分制信用模型与评价系统

- 实现 `requesterCreditScore / helperCreditScore / overallCreditScore`。
- 实现 `overallCreditScore = helper * 0.6 + requester * 0.4`。
- 支持从历史任务、评价、争议结果复算信用分。
- 每次复算写入 `credit_snapshots`。
- 支持无历史用户默认 100 分。
- 评价系统支持完成任务后的双向评价，并通过唯一约束防重复评价。
- 信用权重支持从 `system_configs` 读取，异常配置回退默认值。

对应文件：

- `backend/app/routers/credit.py`
- `backend/app/services/credit_service.py`
- `backend/tests/test_credit.py`
- `backend/alembic/versions/20260514_01_add_rating_unique_constraint.py`

### 1.4 规则加权推荐

- 实现可解释推荐得分：`scoreCategory / scoreDistance / scoreSuccessRate / scoreActiveTime / scoreTotal`。
- 推荐只返回可接任务：`PENDING` 且不是自己发布的任务。
- 推荐快照写入 `recommendation_snapshots`。
- 推荐权重支持从 `system_configs` 读取，缺字段、非法值、权重不等于 100 时回退默认值。
- 增加 Redis 推荐缓存，缓存失败不影响主流程。

对应文件：

- `backend/app/routers/recommendation.py`
- `backend/app/services/recommendation_service.py`
- `backend/tests/test_recommendation.py`

### 1.5 争议裁决联动

- 在 B 的 Service 层提供争议裁决核心方法。
- 支持 admin 支持 helper：`DISPUTED -> COMPLETED` 并结算。
- 支持 admin 支持 requester：`DISPUTED -> CANCELLED` 并退款。
- 支持拆分结算与自定义关闭：`DISPUTED -> CLOSED_BY_ADMIN`。
- 裁决结果可进入信用分复算输入。
- 仅提供核心业务能力，不接管 Admin 页面和权限体系。

对应文件：

- `backend/app/services/task_service.py`
- `backend/app/routers/admin.py`
- `backend/tests/test_admin_dispute.py`

### 1.6 数据库迁移与索引

- 修复 Alembic 编码与 online 迁移可执行问题。
- 补基础 schema 迁移，使空 MySQL schema 可执行 `alembic upgrade head`。
- 补冻结文档要求的核心索引：
  - `tasks(status, created_at)`
  - `tasks(building_code, status)`
  - `transactions(wallet_id, created_at)`
  - `recommendation_snapshots(user_id, snapshot_date)`

对应文件：

- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/20260514_00_create_base_schema.py`
- `backend/alembic/versions/20260514_03_add_frozen_indexes.py`
- `backend/app/models/task.py`
- `backend/app/models/wallet.py`
- `backend/app/models/recommendation.py`

### 1.7 清理 fake/stub 风险

- 移除 B-owned service 中的 `build_stub_task()`、`build_stub_wallet()`。
- 避免生产 Service 层暴露伪造业务数据。
- 冻结 API 未声明的 `/api/credit/profile` 不再作为对外接口挂载，信用能力保留在 Service 层。

对应文件：

- `backend/app/services/task_service.py`
- `backend/app/services/wallet_service.py`
- `backend/app/routers/map.py`
- `backend/app/main.py`
- `backend/app/routers/credit.py`

## 2. 提交了什么

当前工作区无法读取 git 历史：

```text
git log --oneline -5
fatal: not a git repository (or any of the parent directories): .git
```

因此本次汇报不伪造 commit。待项目在带 `.git` 元数据的仓库中提交后，建议拆成以下提交：

- `feat(task): complete task state machine and frozen task APIs`
  - 任务状态机、任务大厅过滤排序、我的发布、我的接单、接单门槛配置化。
- `feat(wallet): add settlement idempotency and split settlement audit`
  - 钱包冻结/解冻/结算一致性、结算幂等、拆分结算审计语义。
- `feat(credit): implement dual-role credit scoring`
  - requester/helper 双分制信用模型、快照、评价输入、默认分和边界测试。
- `feat(recommendation): add explainable weighted recommendation`
  - 规则加权推荐、推荐快照、权重配置、Redis 缓存。
- `feat(dispute): add dispute resolution service hooks`
  - 争议支持 helper/requester、拆分结算、自定义关闭、信用联动。
- `test(mysql): verify alembic migrations and concurrency on MySQL`
  - Alembic online 迁移、MySQL 行锁并发、重复确认、取消/接单竞争测试。
- `chore(cleanup): remove production stubs and non-frozen credit API exposure`
  - 清理 fake/stub 风险和冻结 API 外露点。

## 3. 自测结果

### 3.1 普通后端全量测试

命令：

```powershell
cd backend
python -m pytest -q
```

结果：

```text
79 passed, 4 skipped
```

说明：4 个 skipped 为真实 MySQL 专项测试，未设置 `CAMPUSMAST_MYSQL_TEST_URL` 时按设计跳过。

### 3.2 真实 MySQL 并发与迁移集成测试

命令：

```powershell
cd backend
$env:CAMPUSMAST_MYSQL_TEST_URL='mysql+pymysql://root:root@127.0.0.1:3307/campusmast_concurrency_test'
python -m pytest tests\test_mysql_concurrency.py -q
```

结果：

```text
4 passed
```

已覆盖：

- 空 MySQL schema 执行 Alembic `upgrade head`。
- 检查 `uq_ratings_task_id_from_user_id`。
- 检查 `uq_transactions_settlement_key`。
- 检查冻结索引是否落库。
- 并发接单只允许一个 helper 成功。
- 重复确认只结算一次。
- 取消和接单竞争只产生一个有效终态。

### 3.3 Alembic online 迁移验证

命令：

```powershell
cd backend
$env:DATABASE_URL='mysql+pymysql://root:root@127.0.0.1:3307/campusmast_test'
python -m alembic upgrade head
python -m alembic current
```

结果：

```text
20260514_03 (head)
```

### 3.4 专项测试

已单独验证：

- `tests/test_task.py`：任务状态机、接单门槛、任务列表过滤、我的任务。
- `tests/test_wallet.py`：冻结、解冻、结算、幂等、拆分结算审计。
- `tests/test_credit.py`：双分制信用、快照、边界分、默认 100 分、评价约束。
- `tests/test_recommendation.py`：推荐排序、默认画像得分、字段契约、权重异常回退。
- `tests/test_admin_dispute.py`：争议裁决资金流与信用联动。

### 3.5 截图、接口返回或录屏证据

- 本次主要为后端核心业务开发，无页面截图或录屏。
- 证据以可复现测试命令和 pytest/Alembic 输出为准。
- 接口契约通过 `tests/test_task.py`、`tests/test_recommendation.py` 等字段契约测试覆盖。

## 4. 存在的问题

- 当前工作目录不是 git 仓库，无法直接粘贴真实 commit。
- 普通全量测试默认不跑 MySQL 专项；CI 或本地验收需要显式提供 `CAMPUSMAST_MYSQL_TEST_URL`。
- Admin 页面、权限体系、通知网关/WebSocket 实际推送不属于 B 单独交付范围，已保留核心 Service 能力和事件触发点，后续需要联调。

## 5. 注意事项

- 不得修改冻结任务状态枚举。
- 接单门槛必须使用 `helperCreditScore`，默认值为 60。
- 钱包结算必须通过事务保护，避免重复发放或资金丢失。
- 信用分字段固定为 `requesterCreditScore / helperCreditScore / overallCreditScore`。
- 推荐采用规则加权，不引入机器学习。
- MySQL 并发验收必须设置真实 `CAMPUSMAST_MYSQL_TEST_URL` 后执行专项测试。
