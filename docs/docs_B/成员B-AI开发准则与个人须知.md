# 成员B-AI开发准则与个人须知

> 适用对象：CampusMast 项目成员 B 及协助成员 B 开发的 AI 编程助手  
> 适用范围：后端核心业务开发  
> 主要依据：`docs/产品需求文档.md`、`docs/数据库设计.md`、`docs/API接口规范.yaml`、`docs/团队分工文档.md`  
> 当前优先级：任务状态机、钱包事务、信用评价、推荐算法、核心测试

---

## 1. 成员 B 的定位

成员 B 是 CampusMast 后端核心业务负责人，核心目标是把平台的任务流转、资金流转、信用评价和推荐逻辑做成稳定、可追踪、可测试、可并发运行的业务闭环。

成员 B 的代码应当优先保证以下四件事：

1. 任务状态流转合法。
2. 钱包资金冻结、解冻、结算一致。
3. 信用分与评价数据可追踪、可复算。
4. 推荐结果清晰、可解释、字段稳定。

---

## 2. 成员 B 当前负责什么

### 2.1 任务状态机

成员 B 负责实现任务完整生命周期，包括但不限于：

- 发布任务后冻结赏金并进入 `PENDING`。
- 接单成功后写入 `helperId` 并进入 `IN_PROGRESS`。
- Helper 提交完成证明后进入 `PENDING_REVIEW`。
- Requester 确认完成后进入 `COMPLETED` 并触发资金结算。
- Requester 取消 `PENDING` 任务后进入 `CANCELLED` 并解冻资金。
- Helper 放弃 `IN_PROGRESS` 任务后回到 `PENDING`，清空 `helperId`。
- Requester 拒绝验收后进入 `DISPUTED`。
- 系统过期处理进入 `EXPIRED` 并解冻资金。
- 后续配合 Admin 争议裁决进入 `COMPLETED / CANCELLED / CLOSED_BY_ADMIN`。

状态机只能使用冻结状态：

```text
PENDING
IN_PROGRESS
PENDING_REVIEW
COMPLETED
DISPUTED
CANCELLED
EXPIRED
CLOSED_BY_ADMIN
```

允许流转固定为：

```text
PENDING -> IN_PROGRESS -> PENDING_REVIEW -> COMPLETED
PENDING -> CANCELLED
PENDING -> EXPIRED
IN_PROGRESS -> PENDING
IN_PROGRESS -> DISPUTED
PENDING_REVIEW -> DISPUTED
DISPUTED -> COMPLETED
DISPUTED -> CANCELLED
DISPUTED -> CLOSED_BY_ADMIN
```

### 2.2 钱包事务

成员 B 负责实现钱包核心事务：

- `TOP_UP`：模拟充值。
- `WITHDRAW`：模拟提现。
- `FREEZE`：发布任务时冻结赏金。
- `UNFREEZE`：取消、过期、退款时解冻赏金。
- `SETTLE_OUT`：任务完成时从 requester 冻结余额扣出。
- `SETTLE_IN`：任务完成时给 helper 增加可用余额。
- `SETTLE_SPLIT`：争议裁决时按比例拆分结算。

钱包事务必须满足：

- 不允许 `available` 为负。
- 不允许 `frozen` 为负。
- 发布任务时，任务创建和资金冻结必须在同一个业务事务中。
- 取消、过期、退款时，状态变化和资金解冻必须在同一个业务事务中。
- 完成、争议裁决时，状态变化和资金结算必须在同一个业务事务中。
- 每笔资金变化必须写入 `transactions` 流水。

### 2.3 双分制信用模型

成员 B 负责双分制信用模型：

- `requesterCreditScore`
- `helperCreditScore`
- `overallCreditScore`

默认规则：

- 新用户三项信用分均为 `100`。
- 接单门槛默认 `helperCreditScore >= 60`。
- 综合信用分默认按 `helper 60% + requester 40%` 计算。
- 信用分快照写入 `credit_snapshots`，确保可追踪。

Helper 信用分指标：

- 完成率，权重 35%。
- 平均评分，权重 25%。
- 超时率反向得分，权重 15%。
- 放弃率反向得分，权重 15%。
- 争议败诉率反向得分，权重 10%。

Requester 信用分指标：

- 完成确认率，权重 35%。
- 平均评分，权重 25%。
- 超时确认率反向得分，权重 15%。
- 恶意争议率反向得分，权重 15%。
- 接单后取消率反向得分，权重 10%。

### 2.4 评价系统

成员 B 负责任务完成后的双向评价：

- 一个完成任务支持 requester 评价 helper。
- 一个完成任务支持 helper 评价 requester。
- 评分范围固定为 1-5。
- 评价内容参与下一轮信用分计算。
- 同一用户对同一任务不能重复评价同一对象。

### 2.5 智能推荐

成员 B 负责规则加权推荐，不做机器学习。

默认推荐特征：

- 任务类别偏好。
- 楼宇距离。
- 历史完成成功率。
- 近期活跃时段。

推荐输出字段必须保持 API 冻结定义：

- `task`
- `scoreTotal`
- `scoreCategory`
- `scoreDistance`
- `scoreSuccessRate`
- `scoreActiveTime`

### 2.6 核心测试

成员 B 负责核心业务测试：

- 任务状态机测试。
- 钱包冻结、解冻、结算测试。
- 并发接单测试。
- 信用分计算测试。
- 评价系统测试。
- 推荐得分测试。

---

## 3. 成员 B 不负责什么

成员 B 不负责以下内容，除非组长明确授权：

- 用户注册、登录、JWT、刷新令牌、认证鉴权。
- Admin 后台页面与后台系统配置页面。
- WebSocket 网关底层连接管理。
- 通知系统底层推送实现。
- 聊天 IM 底层消息网关。
- DeepSeek AI 审核服务接入。
- OSS 上传签名和文件存储。
- Docker、Nginx、云主机部署。
- 前端页面、Vue 状态管理、MSW mock。
- 冻结文档拍板。
- API 字段、状态机枚举、信用分字段、推荐结果字段的擅自变更。

如果成员 B 发现必须修改接口、字段、枚举、状态流转，应先提出 RFC，不允许直接改代码后补文档。

RFC 格式：

```text
[RFC] 接口/状态/字段变更申请
模块：
当前定义：
建议修改：
影响范围：
是否阻塞开发：
```

---

## 4. 后端模块结构

后端目录为：

```text
backend/
  app/
    main.py
    config.py
    dependencies/
    models/
    routers/
    schemas/
    services/
    utils/
    websockets/
  tests/
  alembic/
```

### 4.1 `app/main.py`

FastAPI 应用入口，负责：

- 创建 FastAPI app。
- 注册 CORS。
- 挂载各业务 Router。
- 暴露 `/healthz` 健康检查。
- 挂载 WebSocket router。

成员 B 原则上不改 `main.py`，除非新增 B 负责模块的 router 挂载缺失。

### 4.2 `app/config.py`

统一配置入口，负责读取：

- 应用配置。
- 数据库连接。
- Redis 连接。
- JWT 配置。
- OSS 配置。
- DeepSeek 配置。

成员 B 原则上不新增配置项。若接单门槛、信用权重、推荐权重需要配置化，应优先读取 `system_configs`，不得硬改 API 契约。

### 4.3 `app/models/`

SQLAlchemy ORM 模型目录。

与成员 B 高相关的模型：

```text
models/enums.py
models/task.py
models/wallet.py
models/rating.py
models/recommendation.py
models/user.py
```

职责说明：

- `enums.py`：冻结枚举定义，包括任务状态、交易类型等。成员 B 不得擅自新增或改名。
- `task.py`：`Task`、`TaskLog`，承载任务状态机和流转日志。
- `wallet.py`：`Wallet`、`Transaction`，承载余额和资金流水。
- `rating.py`：`Rating`、`CreditSnapshot`，承载评价和信用分快照。
- `recommendation.py`：`RecommendationSnapshot`，承载推荐得分快照。
- `user.py`：`User`、`UserProfile`，包含三项信用分和推荐画像字段。

### 4.4 `app/schemas/`

Pydantic 请求和响应结构目录。

与成员 B 高相关：

```text
schemas/task.py
schemas/wallet.py
schemas/credit.py
schemas/recommendation.py
```

准则：

- Schema 字段必须匹配 `docs/API接口规范.yaml`。
- HTTP JSON 字段使用 camelCase。
- 金额响应统一字符串，两位小数，例如 `"10.00"`。
- 不得为了实现方便把 API 字段改成 snake_case。

### 4.5 `app/routers/`

HTTP 路由层。

成员 B 主要维护：

```text
routers/task.py
routers/wallet.py
routers/credit.py
routers/recommendation.py
```

Router 层准则：

- Router 尽量薄。
- Router 只负责接收请求、注入依赖、调用 Service、包装响应。
- 不在 Router 中写复杂状态机、资金计算、信用算法、推荐算法。
- 业务异常转换为合适 HTTP 状态码。

### 4.6 `app/services/`

业务服务层，是成员 B 的主要战场。

成员 B 主要维护：

```text
services/task_service.py
services/wallet_service.py
services/credit_service.py
services/recommendation_service.py
```

Service 层准则：

- 承载核心业务逻辑。
- 明确事务边界。
- 状态变化、资金变化、日志写入应在同一个业务事务中。
- 并发接单必须使用行锁或等价乐观并发控制。
- 信用分计算必须能从持久化数据复算。
- 推荐得分必须能解释每一项分数来源。

### 4.7 `app/dependencies/`

FastAPI 依赖目录。

常见内容：

- 数据库 session 注入。
- 当前用户注入。
- 管理员权限注入。

成员 B 可以使用，不应重写认证逻辑。

### 4.8 `app/utils/`

通用工具目录。

成员 B 可以复用：

- `response.py`：统一响应结构。
- `errors.py`：业务异常基础类。

成员 B 不应接管：

- `jwt.py`
- `oss.py`
- `redis.py`
- `security.py`

### 4.9 `tests/`

测试目录。

成员 B 主要维护：

```text
tests/test_task.py
tests/test_wallet.py
tests/test_credit.py
tests/test_recommendation.py
```

测试准则：

- 核心业务优先写 Service 层测试。
- 状态机和钱包事务必须测正常路径和失败路径。
- 并发接单必须有测试。
- 信用分必须测边界值和快照写入。
- 推荐必须测总分和分项得分。

---

## 5. 冻结约束红线

以下内容成员 B 不得擅自修改：

### 5.1 状态机枚举

只能使用：

```text
PENDING / IN_PROGRESS / PENDING_REVIEW / COMPLETED / DISPUTED / CANCELLED / EXPIRED / CLOSED_BY_ADMIN
```

不得新增：

```text
ACCEPTED
DONE
REVIEWING
REFUNDED
FAILED
```

如确实需要新增状态，必须先 RFC。

### 5.2 接单信用门槛

默认门槛：

```text
helperCreditScore >= 60
```

不得擅自改成 70、80 或仅看 `overallCreditScore`。

### 5.3 钱包一致性

不得出现：

- 任务创建成功但未冻结资金。
- 资金冻结成功但任务创建失败。
- 任务取消成功但资金仍冻结。
- 任务完成成功但 helper 未收到钱。
- 任务重复确认导致重复结算。
- `available` 或 `frozen` 小于 0。

### 5.4 信用分字段

只能使用：

```text
requesterCreditScore
helperCreditScore
overallCreditScore
```

不得新增或替换为：

```text
creditScore
score
trustScore
ratingScore
```

### 5.5 推荐字段

推荐结果字段必须保持：

```text
task
scoreTotal
scoreCategory
scoreDistance
scoreSuccessRate
scoreActiveTime
```

不得新增不可解释的黑盒字段，不做机器学习。

---

## 6. 当前已完成基础

当前已经具备以下基础实现：

- 任务发布时冻结赏金。
- `PENDING -> IN_PROGRESS` 接单。
- `IN_PROGRESS -> PENDING_REVIEW` 提交完成证明。
- `PENDING_REVIEW -> COMPLETED` 确认完成并结算。
- `PENDING -> CANCELLED` 取消并解冻。
- `IN_PROGRESS -> PENDING` helper 放弃任务。
- `PENDING_REVIEW -> DISPUTED` requester 拒绝验收。
- 接单门槛 `helperCreditScore >= 60`。
- 并发接单使用版本条件更新，确保只成功一个 helper。
- 钱包 `TOP_UP / WITHDRAW / FREEZE / UNFREEZE / SETTLE_OUT / SETTLE_IN` 基础事务。
- `tests/test_task.py` 和 `tests/test_wallet.py` 已覆盖核心主流程。

当前已知环境注意事项：

- 全量测试可能被认证占位依赖 `python-jose` 缺失阻塞。
- B 模块服务层测试可以先独立运行。
- Windows 环境下可能存在 `__pycache__` 权限问题，语法检查可用 AST 解析替代 `py_compile`。

---

## 7. 分阶段 TODO LIST

### 7.1 当务之急

目标：把“任务状态机 + 钱包事务”的主链路从可跑变成可靠。

TODO：

- [ ] 补齐任务详情接口中所有 API 冻结字段，包括 `deadline`、`createdAt`、`proofNote`、`proofImageUrls`、`logs`。
- [ ] 检查 `createTask` 返回状态码是否严格为 `201`，响应结构是否符合 `SuccessResponse`。
- [ ] 为 `acceptTask` 增加重复接单、自己接自己任务、低信用接单、过期任务接单的 API 层测试。
- [ ] 为 `confirmTask` 增加重复确认防护测试，确保不会重复结算。
- [ ] 为 `cancelTask` 增加非 `PENDING` 状态不可取消测试。
- [ ] 为 `abandonTask` 增加只有当前 helper 能放弃任务的测试。
- [ ] 为钱包增加所有金额输入边界测试：`0`、负数、超过余额、小数精度。
- [ ] 明确业务异常 code 映射，避免所有业务错误都只返回普通字符串。
- [ ] 确认 MySQL 环境下 `SELECT ... FOR UPDATE` 与 `version` 乐观条件更新都能正常工作。
- [ ] 修复或安装测试环境缺失依赖，让 `python -m pytest` 全量可运行。

验收标准：

- `tests/test_task.py` 和 `tests/test_wallet.py` 稳定通过。
- 任务主流程在数据库中能看到状态、钱包、流水、日志四者一致。
- 并发接单测试稳定保证只有一个成功。

### 7.2 第一阶段：任务状态机完善

目标：覆盖冻结文档中所有任务流转，不遗漏边界状态。

TODO：

- [ ] 实现系统过期任务处理：`PENDING -> EXPIRED`。
- [ ] 过期处理时自动解冻 requester 冻结余额。
- [ ] 补充过期任务批处理 Service 方法，但不接管调度系统。
- [ ] 完善 `TaskLog` 备注，记录每次关键业务动作。
- [ ] 增加状态机统一转移表，禁止散落 if-else。
- [ ] 增加状态机单元测试，覆盖所有允许流转。
- [ ] 增加非法流转测试，确保拒绝未冻结路径。
- [ ] 为 `DISPUTED` 状态保留 admin 裁决入口的 Service 方法，但不接管 admin router 页面。
- [ ] 预留通知事件调用点，但不实现 WebSocket 网关。

验收标准：

- 冻结文档列出的状态流转全部有 Service 方法或明确预留。
- 所有状态变化都写 `task_logs`。
- 非法状态流转不会改变任务、钱包和流水。

### 7.3 第二阶段：钱包事务完善

目标：让资金逻辑可审计、可恢复、不会重复结算。

TODO：

- [ ] 给每类交易补齐统一描述和相关任务 ID。
- [ ] 增加幂等保护，防止同一任务重复 `SETTLE_OUT / SETTLE_IN`。
- [ ] 增加 `SETTLE_SPLIT` 拆分结算逻辑。
- [ ] 支持争议裁决：全额退款、全额结算、比例拆分、管理员关闭。
- [ ] 为钱包流水列表增加分页测试。
- [ ] 为钱包事务增加数据库回滚测试：中途异常时任务和钱包都不落半截状态。
- [ ] 检查 Decimal 使用，禁止用 float 做金额计算。
- [ ] 确认所有金额输出为两位小数字符串。

验收标准：

- 任意任务资金变化都能在 `transactions` 查到完整流水。
- 钱包总额变化符合业务预期。
- 失败事务不会产生半完成状态。

### 7.4 第三阶段：互评系统

目标：任务完成后支持双向评价，并为信用分计算提供输入。

TODO：

- [ ] 实现 `POST /api/tasks/{id}/rating`。
- [ ] 只有 `COMPLETED` 任务允许评价。
- [ ] requester 只能评价该任务 helper。
- [ ] helper 只能评价该任务 requester。
- [ ] 同一任务、同一评价人只能评价一次。
- [ ] 评分必须在 1-5。
- [ ] 评价成功后触发或预留信用分快照计算。
- [ ] 增加评价接口测试。
- [ ] 增加重复评价、非参与者评价、未完成任务评价测试。

验收标准：

- 评价数据写入 `ratings`。
- 评价关系正确，不能评价无关用户。
- 信用分计算可读取评价数据。

### 7.5 第四阶段：双分制信用模型

目标：实现 requester/helper 双角色信用分和综合信用分快照。

TODO：

- [ ] 实现 helper 信用分计算。
- [ ] 实现 requester 信用分计算。
- [ ] 实现 `overallCreditScore = helper * 0.6 + requester * 0.4`。
- [ ] 每次计算写入 `credit_snapshots`。
- [ ] 支持按用户查询最新信用分。
- [ ] 支持从历史任务、评价、争议结果复算。
- [ ] 增加信用分边界测试，保证结果在 0-100。
- [ ] 增加无历史数据用户默认 100 分测试。
- [ ] 增加低分 helper 被禁止接单测试。

验收标准：

- 用户表三项信用分更新正确。
- `credit_snapshots` 能追踪每次计算输入和结果。
- 接单门槛严格使用 `helperCreditScore`。

### 7.6 第五阶段：规则加权推荐

目标：实现可解释的推荐得分，不引入机器学习。

TODO：

- [ ] 实现类别偏好得分 `scoreCategory`。
- [ ] 实现楼宇距离得分 `scoreDistance`。
- [ ] 实现历史成功率得分 `scoreSuccessRate`。
- [ ] 实现活跃时段得分 `scoreActiveTime`。
- [ ] 实现总分 `scoreTotal`。
- [ ] 推荐只返回可接任务，即 `PENDING` 且不是自己发布的任务。
- [ ] 写入 `recommendation_snapshots`。
- [ ] 增加推荐排序测试。
- [ ] 增加缺少画像数据时的默认得分测试。
- [ ] 增加推荐字段契约测试，保证 API 字段不漂移。

验收标准：

- 推荐结果字段符合 `API接口规范.yaml`。
- 每条推荐可解释分项得分。
- 权重调整不影响字段契约。

### 7.7 第六阶段：争议裁决联动

目标：配合 Admin 模块完成争议裁决的核心业务服务。

TODO：

- [ ] 在 B 的 Service 层提供争议裁决方法。
- [ ] 支持 admin 支持 helper：`DISPUTED -> COMPLETED` 并结算。
- [ ] 支持 admin 支持 requester：`DISPUTED -> CANCELLED` 并退款。
- [ ] 支持 admin 拆分结算：`DISPUTED -> CLOSED_BY_ADMIN` 或按冻结文档约定执行。
- [ ] 支持 admin 自定义关闭：`DISPUTED -> CLOSED_BY_ADMIN`。
- [ ] 裁决结果影响信用分计算输入。
- [ ] 增加争议资金流测试。
- [ ] 增加争议信用分影响测试。

验收标准：

- 争议裁决不会造成资金丢失或重复发放。
- 争议结果可被信用模型追踪。
- 不接管 Admin 页面和 Admin 权限，只提供核心业务方法。

### 7.8 第七阶段：联调和回归

目标：与 A、组长模块联调，稳定 API 契约。

TODO：

- [ ] 与 A 对齐任务大厅、任务详情、我的任务接口字段。
- [ ] 与 A 对齐钱包余额和流水接口字段。
- [ ] 与 A 对齐信用和评价接口字段。
- [ ] 与 A 对齐推荐结果字段。
- [ ] 与组长对齐认证依赖和当前用户注入。
- [ ] 与组长对齐通知事件调用点。
- [ ] 与组长对齐 Admin 争议裁决调用方式。
- [ ] 跑完整后端测试。
- [ ] 整理 B 模块验收说明。

验收标准：

- 前后端字段不需要临时兼容补丁。
- API 契约无漂移。
- B 模块核心测试全部通过。

---

## 8. AI 协作开发准则

当 AI 协助成员 B 开发时，必须遵守以下规则：

### 8.1 每次开工前先说明改哪些文件

示例：

```text
本次计划修改：
- backend/app/services/task_service.py
- backend/app/services/wallet_service.py
- backend/tests/test_task.py
- backend/tests/test_wallet.py
```

如果实际改动范围扩大，必须说明原因。

### 8.2 优先读冻结文档和现有代码

开发前至少确认：

- PRD 中的业务规则。
- 数据库设计中的字段和枚举。
- API 规范中的字段名和响应结构。
- 团队分工中的文件边界。
- 当前代码已有实现。

### 8.3 不擅自改冻结契约

AI 不能直接修改：

- API 字段。
- 状态机枚举。
- 信用分字段。
- 推荐结果字段。
- WebSocket 事件名。
- 错误码体系。

需要修改时必须先输出 RFC。

### 8.4 Service 层优先

AI 写业务逻辑时：

- 优先改 Service。
- Router 只做薄封装。
- Schema 不随意改字段。
- Model 不随意新增字段。

### 8.5 测试必须跟上

每次实现核心业务都要补测试：

- 正常路径。
- 失败路径。
- 边界值。
- 并发场景。
- 事务回滚场景。

### 8.6 输出必须对照冻结约束

每次完成后必须说明：

- 对应了哪条冻结文档。
- 是否改了 API 字段。
- 是否改了状态机。
- 是否改了信用字段。
- 是否改了推荐字段。
- 跑了哪些测试。
- 哪些测试因为环境问题未跑。

---

## 9. 开发时常见判断标准

### 9.1 判断某段逻辑是否属于 B

属于 B：

- 任务能不能接。
- 任务能不能取消。
- 任务完成后钱给谁。
- 钱包余额怎么变。
- 信用分怎么算。
- 评价是否允许提交。
- 推荐分怎么算。

不属于 B：

- 当前用户 token 怎么解析。
- 管理员页面怎么展示。
- WebSocket 怎么连接。
- 通知怎么实时推送。
- 文件怎么上传。
- DeepSeek 怎么调用。
- 前端页面怎么布局。

### 9.2 判断是否需要事务

只要一个业务动作同时改以下任意两个对象，就必须在同一事务：

- `tasks`
- `task_logs`
- `wallets`
- `transactions`
- `ratings`
- `credit_snapshots`
- `recommendation_snapshots`

典型必须事务化的动作：

- 创建任务 + 冻结资金 + 写日志。
- 取消任务 + 解冻资金 + 写日志。
- 确认完成 + 结算资金 + 写日志。
- 争议裁决 + 资金处理 + 信用输入记录。

### 9.3 判断是否需要并发控制

以下场景必须考虑并发：

- 多人同时接单。
- 同一个任务被重复确认。
- 同一个任务被同时取消和接单。
- 同一个钱包被同时提现和冻结。
- 同一个任务被重复裁决。

优先方案：

- MySQL 行锁：`SELECT ... FOR UPDATE`。
- 乐观锁：`version` 条件更新。
- 唯一约束：防重复评价、防重复会话。
- 幂等检查：防重复结算。

---

## 10. 提交前自查清单

提交 B 模块代码前，逐项确认：

- [ ] 是否只改了 B 边界内文件。
- [ ] 是否没有修改冻结 API 字段。
- [ ] 是否没有新增状态枚举。
- [ ] 是否没有绕过 `helperCreditScore >= 60`。
- [ ] 是否所有金额计算使用 Decimal 或数据库 Numeric。
- [ ] 是否所有金额响应为两位小数字符串。
- [ ] 是否任务状态变化写入 `task_logs`。
- [ ] 是否钱包变化写入 `transactions`。
- [ ] 是否关键动作在同一事务中。
- [ ] 是否考虑并发接单。
- [ ] 是否补了正常路径测试。
- [ ] 是否补了失败路径测试。
- [ ] 是否补了边界测试。
- [ ] 是否补了并发测试。
- [ ] 是否说明了未完成事项和环境阻塞。

---

## 11. 推荐工作节奏

建议成员 B 按以下节奏开发：

1. 先稳定任务状态机和钱包事务。
2. 再做评价系统。
3. 再做信用分快照。
4. 再做推荐得分。
5. 最后做争议裁决和联调收口。

不要同时铺开太多模块。B 模块的价值不在“接口数量多”，而在“核心业务闭环正确、事务一致、边界清楚、测试可靠”。

---

## 12. 当前下一步建议

建议下一次开发从以下任务开始：

1. 补齐任务状态机非法流转测试。
2. 增加重复确认防重复结算保护。
3. 增加 `EXPIRED` 过期处理。
4. 增加钱包事务回滚测试。
5. 开始实现 `POST /api/tasks/{id}/rating`。

完成这五项后，B 模块就可以从“主流程可跑”进入“核心业务可信”的阶段。
