# Git 协作指南

> 适用项目：CampusMast
> 文档版本：v2.0
> 状态：冻结版本

---

## 1. 分支模型

本项目固定使用以下分支结构：

```text
main                 阶段性成果固化分支
└── check            唯一公共集成基线
    ├── feat/a-frontend
    ├── feat/b-backend-core
    └── feat/c-infra
```

### 1.1 各分支职责

| 分支 | 职责 |
|------|------|
| `main` | 存放阶段性稳定成果，只在阶段检查或里程碑时更新 |
| `check` | 唯一公共集成基线，所有功能先合入这里 |
| `feat/a-frontend` | A 同学前端开发分支 |
| `feat/b-backend-core` | B 同学核心业务分支 |
| `feat/c-infra` | 组长基础设施/后台/文档冻结分支 |

### 1.2 权限规则

- 所有人**禁止**直接向 `main` 推送
- 所有人**禁止**直接向 `check` 推送
- 所有开发分支统一向 `check` 提交 PR
- 仅组长负责 review 并合并到 `check`
- 仅组长负责在阶段节点把 `check` 合并到 `main`

---

## 2. 日常工作流

### 2.1 第一次拉代码

```bash
git clone <仓库地址>
cd CampusMast
git branch -a
```

### 2.2 从 `check` 拉出个人分支

```bash
# 先拉取远程最新分支
git fetch origin

# 切换到 check 并同步
git checkout check
git pull origin check

# A 同学
git checkout -b feat/a-frontend
git push -u origin feat/a-frontend

# B 同学
git checkout -b feat/b-backend-core
git push -u origin feat/b-backend-core

# 组长 / C 同学
git checkout -b feat/c-infra
git push -u origin feat/c-infra
```

### 2.3 每天开始开发前

```bash
# 以 A 同学为例
git checkout feat/a-frontend
git pull origin feat/a-frontend
```

如果 `check` 有新合并内容，需要同步到自己的分支：

```bash
git fetch origin
git checkout check
git pull origin check
git checkout feat/a-frontend
git merge check
```

### 2.4 开发完成后提交

```bash
git status
git add .
git commit -m "feat: 完成任务大厅地图筛选"
git push origin feat/a-frontend
```

---

## 3. Pull Request 流程

### 3.1 PR 目标分支固定为 `check`

所有 PR 一律按以下方向提交：

```text
feat/a-frontend      -> check
feat/b-backend-core  -> check
feat/c-infra         -> check
```

### 3.2 PR 要求

PR 标题建议格式：

```text
feat: 新增任务内聊天前端
fix: 修复钱包结算事务问题
docs: 冻结 API 接口规范
```

PR 描述必须包含：

```text
## 改动内容
- 

## 影响模块
- 

## 自测结果
- 

## 是否影响接口 / 状态机 / 数据字段
- 是 / 否
```

### 3.3 组长 Review 重点

组长 review 时必须重点检查：

- 是否符合冻结文档
- 是否擅自修改接口、状态机、字段含义
- 是否引入跨模块耦合
- 是否需要先改文档后改代码

---

## 4. 文档冻结后的特殊规则

以下改动一律视为“高风险变更”，必须先改文档再改代码：

- API 字段
- 任务状态枚举
- 钱包流水类型
- WebSocket 事件名
- 审核结果枚举
- 信用分字段
- 地图点位字段
- 推荐结果字段

遇到此类变更时，必须走 RFC：

```text
[RFC] 高风险变更申请
变更模块：
当前定义：
建议修改：
影响前端：
影响后端：
影响数据库：
是否阻塞开发：
```

---

## 5. `check` 合并到 `main`

只有在以下场景才允许从 `check` 合并到 `main`：

- 阶段检查前
- 课程演示前
- 里程碑功能稳定后

推荐流程：

```bash
git checkout main
git pull origin main
git merge check
git push origin main
```

> 说明：`main` 不是日常开发分支，而是阶段性成果分支。

---

## 6. 冲突处理

### 6.1 何时容易冲突

- 多人同时修改同一份冻结文档
- A 修改页面结构同时 B 修改接口字段
- 组长修改 `check` 后，个人分支长时间不同步

### 6.2 处理步骤

```bash
git fetch origin
git checkout check
git pull origin check
git checkout feat/a-frontend
git merge check
```

如果出现冲突：

1. 先看是否涉及冻结内容
2. 涉及冻结内容时，不要自行判断，先找组长确认
3. 非冻结内容按正常 Git 冲突解决流程处理

---

## 7. 提交规范

建议统一使用：

| 类型 | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复问题 |
| `docs` | 文档修改 |
| `refactor` | 重构 |
| `test` | 测试 |
| `chore` | 杂项配置 |

示例：

```bash
git commit -m "feat: 新增任务地图页"
git commit -m "fix: 修复并发接单事务"
git commit -m "docs: 更新信用分加权规则"
```

---

## 8. 三位成员的固定操作

### A 同学

```bash
git checkout feat/a-frontend
git pull origin feat/a-frontend
git merge check
git push origin feat/a-frontend
```

### B 同学

```bash
git checkout feat/b-backend-core
git pull origin feat/b-backend-core
git merge check
git push origin feat/b-backend-core
```

### 组长 / C 同学

```bash
git checkout feat/c-infra
git pull origin feat/c-infra
git merge check
git push origin feat/c-infra
```

### 组长合并到 `check`

```bash
git checkout check
git pull origin check
git merge feat/a-frontend
git merge feat/b-backend-core
git merge feat/c-infra
git push origin check
```

---

## 9. 验收标准

Git 流程文档冻结后，应满足：

- 不再出现 `develop` 作为主集成分支
- PR 目标明确为 `check`
- `main` 仅承担阶段性成果固定角色
- 组长是唯一 `check` 合并者
