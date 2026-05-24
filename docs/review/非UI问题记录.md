p0:高优先级 p1:中优先级 p2:低优先级
**5-24**
- [ ] [p0]1.新增了 `Task.latitude` / `Task.longitude` 字段，但没有提供对应 Alembic 数据库迁移。现有数据库的 `tasks` 表缺少这两列时，后端查询任务会直接 500，已观察到 `/api/tasks/my/posted?page=1&limit=1&status=COMPLETED` 报 `500 Internal Server Error`，首页因此显示“任务加载失败”。涉及代码：`backend/app/models/task.py`、`backend/app/services/task_service.py`，但 `backend/alembic/versions` 中没有新增迁移文件。
- [ ] [p0]2.首页统计接口依赖多个任务接口并发请求，其中一个任务接口 500 会导致首页整体加载失败。当前 `frontend/src/pages/TaskHallPage.vue` 的 `fetchHomepageStats()` 会调用“我发布的任务”等接口，后端异常没有被降级处理，导致一个后端字段/迁移问题直接暴露为首页不可用。
- [ ] [p1]3.本轮提交名义上是“优化首页任务大厅视觉与筛选体验”，但实际改动包含后端模型、服务、启动数据、对象存储配置等内容，范围过大。UI 修复 PR 中混入数据库结构变更，会提高审查难度，也容易遗漏迁移、兼容性和回归测试。
- [ ] [p1]4.`backend/app/bootstrap.py` 中出现了疑似误粘贴的本地 SQLite 配置代码：`database_url: str = "sqlite:///./campusmast.db"`。该变量写在 `_ensure_homepage_blocks()` 逻辑里，没有实际作用，容易误导后续维护者，以为这里控制开发数据库配置。
- [ ] [p1]5.初始化演示任务的数据状态不一致：任务状态是 `PENDING`，但同时写入了 `helper_id`、`proof_note`、`needs_admin_review=True` 等更像“已接单/已提交证明/等待审核”的字段。该类数据会影响首页统计、任务筛选和测试判断，建议按真实业务流转重新设置。
- [ ] [p1]6.本轮至少需要补充后端回归验证：`GET /api/tasks`、`GET /api/tasks/my/posted?status=COMPLETED`、`GET /api/tasks/my/accepted?status=IN_PROGRESS`，并在已有数据库上执行 `alembic upgrade head` 后再测试。不能只通过新库或前端静态页面判断通过。



---
结论：这次 PR 不能只按 UI 问题处理，核心阻塞是后端模型变更缺少数据库迁移，已经造成接口 500 和首页加载失败。应先补齐迁移与接口回归测试，再继续讨论视觉和交互优化。
