<template>
  <div class="admin-page">
    <aside class="admin-sidebar">
      <RouterLink class="admin-brand" to="/admin">
        <span class="brand-mark"><AppIcon name="layers" /></span>
        <span>
          <strong>CampusMast</strong>
          <small>管理后台</small>
        </span>
      </RouterLink>

      <nav class="admin-nav">
        <button
          v-for="item in navItems"
          :key="item.key"
          type="button"
          :class="{ active: isNavActive(item.key) }"
          @click="handleNav(item.key)"
        >
          <AppIcon :name="item.icon" />
          <span>{{ item.label }}</span>
          <i v-if="item.badge">{{ item.badge }}</i>
        </button>
      </nav>

      <section class="admin-account">
        <span>{{ adminInitial }}</span>
        <div>
          <strong>{{ adminName }}</strong>
          <small>超级管理员</small>
        </div>
        <button type="button" @click="logout"><AppIcon name="logout" /> 退出登录</button>
      </section>
    </aside>

    <main class="admin-main">
      <section class="dashboard-shell">
        <header class="dashboard-head">
          <div>
            <h1>{{ panelTitle }}</h1>
            <p>{{ panelSubtitle }}</p>
          </div>
          <div class="head-actions">
            <label class="range-select">
              <AppIcon name="calendar" />
              <select v-model="trendRange">
                <option value="7">近7天</option>
                <option value="14">近14天</option>
                <option value="30">近30天</option>
              </select>
            </label>
            <button type="button" @click="exportReport"><AppIcon name="download" />导出报表</button>
          </div>
        </header>

        <p v-if="loadError" class="admin-error">{{ loadError }}</p>

        <template v-if="activePanel === 'overview'">
          <section class="kpi-grid">
            <article v-for="card in metricCards" :key="card.label" class="kpi-card">
              <span class="kpi-icon" :class="card.tone"><AppIcon :name="card.icon" /></span>
              <div>
                <small>{{ card.label }}</small>
                <strong>{{ card.value }}</strong>
                <em>{{ card.caption }}</em>
              </div>
            </article>
          </section>

          <section class="dashboard-grid">
            <article class="dash-card trend-card">
              <header>
                <h2>平台趋势</h2>
                <div class="trend-tools">
                  <p><i></i>任务数<i class="orange"></i>金额</p>
                  <div class="axis-toggle" aria-label="切换纵坐标">
                    <button :class="{ active: trendMetric === 'tasks' }" type="button" @click="trendMetric = 'tasks'">任务轴</button>
                    <button :class="{ active: trendMetric === 'amount' }" type="button" @click="trendMetric = 'amount'">金额轴</button>
                  </div>
                </div>
              </header>
              <div class="trend-body">
                <div class="y-axis">
                  <span v-for="tick in trendTicks" :key="tick.value">{{ tick.label }}</span>
                </div>
                <div class="chart-area">
                  <svg viewBox="0 0 320 160" preserveAspectRatio="none">
                    <line v-for="tick in trendTicks" :key="`g-${tick.value}`" x1="0" x2="320" :y1="trendTickY(tick.value)" :y2="trendTickY(tick.value)" class="grid-line" />
                    <polyline :points="taskLinePoints" class="task-line" :class="{ muted: trendMetric !== 'tasks' }" />
                    <polyline :points="amountLinePoints" class="amount-line" :class="{ muted: trendMetric !== 'amount' }" />
                    <circle v-for="point in taskPointPositions" :key="point.label" :cx="point.x" :cy="point.y" r="2.8" class="task-dot" />
                    <circle v-for="point in amountPointPositions" :key="`a-${point.label}`" :cx="point.x" :cy="point.y" r="2.8" class="amount-dot" />
                  </svg>
                  <div class="axis-row" :style="{ gridTemplateColumns: `repeat(${trendPoints.length}, minmax(0, 1fr))` }">
                    <span v-for="point in trendPoints" :key="point.label">{{ point.label }}</span>
                  </div>
                </div>
              </div>
            </article>

            <article class="dash-card status-card">
              <header>
                <h2>任务状态分布</h2>
              </header>
              <div class="status-body">
                <div class="donut" :style="donutStyle">
                  <span>任务总数<strong>{{ taskTotal }}</strong></span>
                </div>
                <ul>
                  <li v-for="item in statusStats" :key="item.label">
                    <i :style="{ background: item.color }"></i>
                    <strong>{{ item.label }}</strong>
                    <span>{{ item.percent }}%</span>
                  </li>
                </ul>
              </div>
            </article>

            <article class="dash-card hot-card">
              <header>
                <h2>热门地点</h2>
              </header>
              <div v-if="hotLocations.length" class="rank-list">
                <div v-for="(item, index) in hotLocations" :key="item.name" class="rank-row">
                  <span>{{ index + 1 }}</span>
                  <strong>{{ item.name }}</strong>
                  <small>{{ item.count }} 个任务</small>
                </div>
              </div>
              <p v-else class="empty-line compact">暂无地点数据</p>
            </article>

            <article class="dash-card table-card">
              <header>
                <h2>待处理争议</h2>
                <button type="button" @click="activePanel = 'disputes'">前往处理</button>
              </header>
              <table v-if="disputeTasks.length">
                <thead><tr><th>争议任务</th><th>发布者</th><th>金额</th><th>时间</th></tr></thead>
                <tbody>
                  <tr v-for="task in disputeTasks" :key="task.id">
                    <td>{{ task.title }}</td>
                    <td>{{ task.requester.nickname }}</td>
                    <td>¥{{ task.reward }}</td>
                    <td>{{ relativeTime(task.createdAt) }}</td>
                  </tr>
                </tbody>
              </table>
              <p v-else class="empty-line compact">暂无待处理争议</p>
            </article>

            <article class="dash-card table-card">
              <header>
                <h2>AI 审核队列</h2>
                <button type="button" @click="activePanel = 'review'">前往处理</button>
              </header>
              <div class="scroll-table">
                <table v-if="pendingModerationRows.length">
                  <thead><tr><th>任务编号</th><th>初审结果</th><th>状态</th><th>提交时间</th></tr></thead>
                  <tbody>
                    <tr v-for="record in pendingModerationRows" :key="record.id">
                      <td>{{ record.taskId || "未关联任务" }}</td>
                      <td :class="`risk-${record.riskLevel}`">{{ moderationLabel(record.riskLevel) }}</td>
                      <td>{{ reviewLabel(record.adminReviewStatus) }}</td>
                      <td>{{ relativeTime(record.createdAt) }}</td>
                    </tr>
                  </tbody>
                </table>
                <p v-else class="empty-line compact">暂无待复审记录</p>
              </div>
            </article>
          </section>
        </template>

        <section v-else-if="activePanel === 'manage'" class="manage-grid">
          <article class="dash-card table-card">
            <header>
              <h2>用户管理</h2>
              <span>{{ usersTotal }} 位用户</span>
            </header>
            <div class="scroll-table">
              <table v-if="users.length">
                <thead><tr><th>用户</th><th>邮箱</th><th>角色</th><th>信用分</th><th>状态</th><th>操作</th></tr></thead>
                <tbody>
                  <tr v-for="user in users" :key="user.id">
                    <td>{{ user.nickname }}</td>
                    <td>{{ user.studentEmail }}</td>
                    <td>{{ roleLabel(user.role) }}</td>
                    <td>{{ user.overallCreditScore }}</td>
                    <td>{{ userActiveLabel(user) }}</td>
                    <td class="actions">
                      <button type="button" @click="adjustUserCredit(user)">调分</button>
                      <button type="button" @click="toggleUserActive(user)">{{ userActiveLabel(user) === "正常" ? "停用" : "启用" }}</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <p v-else class="empty-line">暂无用户数据</p>
            </div>
          </article>

          <article class="dash-card table-card">
            <header>
              <h2>任务管理</h2>
              <span>{{ taskTotal }} 个任务</span>
            </header>
            <div class="scroll-table">
              <table v-if="tasks.length">
                <thead>
                  <tr>
                    <th><button type="button" @click="toggleTaskSort('title')">任务 {{ sortMark('title') }}</button></th>
                    <th><button type="button" @click="toggleTaskSort('requester')">发布者 {{ sortMark('requester') }}</button></th>
                    <th><button type="button" @click="toggleTaskSort('status')">状态 {{ sortMark('status') }}</button></th>
                    <th><button type="button" @click="toggleTaskSort('reward')">金额 {{ sortMark('reward') }}</button></th>
                    <th><button type="button" @click="toggleTaskSort('location')">地点 {{ sortMark('location') }}</button></th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="task in sortedTasks" :key="task.id">
                    <td>{{ task.title }}</td>
                    <td>{{ task.requester.nickname }}</td>
                    <td>{{ statusLabel(task.status) }}</td>
                    <td>¥{{ task.reward }}</td>
                    <td>{{ task.locationDetail || task.buildingCode || "校内地点" }}</td>
                    <td class="actions">
                      <button type="button" @click="goTask(task.id)">查看</button>
                      <button v-if="task.status === 'DISPUTED'" type="button" @click="activePanel = 'disputes'">处理争议</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <p v-else class="empty-line">暂无任务数据</p>
            </div>
          </article>
        </section>

        <section v-else-if="activePanel === 'disputes'" class="dash-card table-card work-card">
          <header>
            <h2>争议裁决</h2>
            <span>{{ disputeTasks.length }} 条待处理</span>
          </header>
          <div class="scroll-table">
            <table v-if="disputeTasks.length">
              <thead><tr><th>任务</th><th>发布者</th><th>接单者</th><th>金额</th><th>操作</th></tr></thead>
              <tbody>
                <tr v-for="task in disputeTasks" :key="task.id">
                  <td>{{ task.title }}</td>
                  <td>{{ task.requester.nickname }}</td>
                  <td>{{ task.helper?.nickname || "未接单" }}</td>
                  <td>¥{{ task.reward }}</td>
                    <td class="actions">
                    <button type="button" @click="goTask(task.id)">详情</button>
                      <button type="button" @click="resolveDispute(task.id, 'settle')">支持接单者</button>
                    <button type="button" @click="resolveDispute(task.id, 'refund')">退款发布者</button>
                    <button type="button" @click="resolveDispute(task.id, 'close')">关闭争议</button>
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-else class="empty-line">暂无待处理争议</p>
          </div>
        </section>

        <section v-else-if="activePanel === 'review'" class="dash-card table-card work-card">
          <header>
            <h2>AI 审核队列</h2>
            <span>{{ pendingModerationRows.length }} 条待复审</span>
          </header>
          <div class="scroll-table">
            <table v-if="pendingModerationRows.length">
              <thead><tr><th>任务编号</th><th>初审结果</th><th>命中标签</th><th>提交时间</th><th>操作</th></tr></thead>
              <tbody>
                <tr v-for="record in pendingModerationRows" :key="record.id">
                  <td>{{ record.taskId || "未关联任务" }}</td>
                  <td :class="`risk-${record.riskLevel}`">{{ moderationLabel(record.riskLevel) }}</td>
                  <td>{{ record.hitTags.join("、") || "无" }}</td>
                  <td>{{ relativeTime(record.createdAt) }}</td>
                    <td class="actions">
                    <button v-if="record.taskId" type="button" @click="goTask(record.taskId)">详情</button>
                    <button type="button" @click="reviewModeration(record.id, 'approve')">通过</button>
                    <button type="button" @click="reviewModeration(record.id, 'reject')">拒绝</button>
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-else class="empty-line">暂无待复审记录</p>
          </div>
        </section>
      </section>
    </main>

    <div v-if="devNotice" class="admin-modal" @click.self="devNotice = ''">
      <section>
        <header>
          <h3>功能开发中</h3>
          <button type="button" @click="devNotice = ''">×</button>
        </header>
        <p>{{ devNotice }} 模块正在开发中。</p>
      </section>
    </div>

    <div v-if="selectedTask" class="admin-modal task-modal" @click.self="selectedTask = null">
      <section>
        <header>
          <h3>任务详情</h3>
          <button type="button" @click="selectedTask = null">×</button>
        </header>
        <div class="task-detail-grid">
          <div>
            <small>任务标题</small>
            <strong>{{ selectedTask.title }}</strong>
          </div>
          <div>
            <small>当前状态</small>
            <strong>{{ statusLabel(selectedTask.status) }}</strong>
          </div>
          <div>
            <small>发布者</small>
            <strong>{{ selectedTask.requester.nickname }}</strong>
          </div>
          <div>
            <small>接单者</small>
            <strong>{{ selectedTask.helper?.nickname || "未接单" }}</strong>
          </div>
          <div>
            <small>赏金</small>
            <strong>¥{{ selectedTask.reward }}</strong>
          </div>
          <div>
            <small>截止时间</small>
            <strong>{{ formatDateTime(selectedTask.deadline) }}</strong>
          </div>
          <div class="wide">
            <small>地点</small>
            <strong>{{ selectedTask.locationDetail || selectedTask.buildingCode || "校内地点" }}</strong>
          </div>
          <div class="wide">
            <small>任务描述</small>
            <p>{{ selectedTask.description }}</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import {
  adminListHomepageBlocks,
  adminListModerationRecords,
  adminListTasks,
  adminListUsers,
  adminResolveDispute,
  adminReviewModerationRecord,
  adminUpdateUser,
} from "@/api/modules/admin";
import AppIcon from "@/components/ui/AppIcon.vue";
import { useAuthStore } from "@/stores/auth";
import type { AdminReviewStatus, HomepageBlock, ModerationRecord, ModerationResult, Role, Task, TaskStatus, User } from "@/types/api";

type PanelKey = "overview" | "manage" | "disputes" | "review";
type NavKey = PanelKey | "users" | "tasks" | "notice" | "rules";
type TaskSortKey = "title" | "requester" | "status" | "reward" | "location";

const router = useRouter();
const authStore = useAuthStore();

const activePanel = ref<PanelKey>("overview");
const devNotice = ref("");
const trendRange = ref("14");
const trendMetric = ref<"tasks" | "amount">("tasks");
const loadError = ref("");
const taskSortKey = ref<TaskSortKey>("status");
const taskSortDir = ref<"asc" | "desc">("asc");
const usersTotal = ref(0);
const taskTotal = ref(0);
const users = ref<User[]>([]);
const tasks = ref<Task[]>([]);
const selectedTask = ref<Task | null>(null);
const moderationRows = ref<ModerationRecord[]>([]);
const homepageBlocks = ref<HomepageBlock[]>([]);

const adminName = computed(() => authStore.currentUser?.nickname || "管理员");
const adminInitial = computed(() => adminName.value.slice(0, 1));
const pendingModerationRows = computed(() => moderationRows.value.filter((item) => item.adminReviewStatus === "PENDING"));
const disputeTasks = computed(() => tasks.value.filter((task) => task.status === "DISPUTED"));
const pendingReviewCount = computed(() => tasks.value.filter((task) => task.needsAdminReview).length + pendingModerationRows.value.length);
const completedTasks = computed(() => tasks.value.filter((task) => task.status === "COMPLETED"));
const disputedCount = computed(() => disputeTasks.value.length);
const turnover = computed(() => completedTasks.value.reduce((sum, task) => sum + Number(task.reward || 0), 0));
const sortedTasks = computed(() => {
  const direction = taskSortDir.value === "asc" ? 1 : -1;
  return [...tasks.value].sort((a, b) => compareTask(a, b, taskSortKey.value) * direction);
});
const passRate = computed(() => {
  if (!moderationRows.value.length) return "--";
  const pass = moderationRows.value.filter((item) => item.riskLevel === "ALLOW").length;
  return `${Math.round((pass / moderationRows.value.length) * 100)}%`;
});

const rangeLabel = computed(() => {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - Number(trendRange.value) + 1);
  return `${formatDate(start.toISOString())} ~ ${formatDate(end.toISOString())}`;
});

const panelTitle = computed(() => {
  if (activePanel.value === "manage") return "管理";
  if (activePanel.value === "disputes") return "争议裁决";
  if (activePanel.value === "review") return "AI 审核队列";
  return "总览控制台";
});

const panelSubtitle = computed(() => {
  if (activePanel.value === "manage") return "用户管理与任务管理统一处理";
  if (activePanel.value === "disputes") return "处理用户发起的任务争议";
  if (activePanel.value === "review") return "收纳并复审 AI 标记的任务";
  return "系统整体运行概览与关键指标";
});

const navItems = computed(() => [
  { key: "overview" as NavKey, label: "总览控制台", icon: "chart", badge: 0 },
  { key: "manage" as NavKey, label: "管理", icon: "users", badge: 0 },
  { key: "disputes" as NavKey, label: "争议裁决", icon: "alert", badge: disputeTasks.value.length },
  { key: "review" as NavKey, label: "AI 审核队列", icon: "shield", badge: pendingModerationRows.value.length },
  { key: "notice" as NavKey, label: "通知与消息", icon: "bell", badge: pendingReviewCount.value },
  { key: "rules" as NavKey, label: "运营规则", icon: "settings", badge: 0 },
]);

const metricCards = computed(() => [
  { label: "用户总量", value: usersTotal.value.toLocaleString("zh-CN"), caption: "来自用户管理接口", icon: "users", tone: "green" },
  { label: "任务总量", value: taskTotal.value.toLocaleString("zh-CN"), caption: "来自任务管理接口", icon: "clipboard", tone: "orange" },
  { label: "成交额", value: `¥ ${money(turnover.value)}`, caption: "已完成任务金额", icon: "yen", tone: "green" },
  { label: "争议数量", value: disputedCount.value, caption: "当前争议任务", icon: "alert", tone: "red" },
  { label: "审核命中率", value: passRate.value, caption: "基于复审记录", icon: "shield", tone: "blue" },
  { label: "待处理", value: pendingReviewCount.value, caption: "任务与审核队列", icon: "spark", tone: "purple" },
]);

const statusColors: Record<string, string> = {
  PENDING: "#6f835f",
  IN_PROGRESS: "#f1a64d",
  PENDING_REVIEW: "#7fa6cf",
  COMPLETED: "#a9bf99",
  DISPUTED: "#d96d5f",
  OTHER: "#cbd5df",
};

const statusNames: Record<TaskStatus | "OTHER", string> = {
  PENDING: "待领取",
  IN_PROGRESS: "进行中",
  PENDING_REVIEW: "待验收",
  COMPLETED: "已完成",
  DISPUTED: "争议中",
  CANCELLED: "已取消",
  EXPIRED: "已过期",
  CLOSED_BY_ADMIN: "后台关闭",
  OTHER: "其他",
};

const statusStats = computed(() => {
  const total = Math.max(tasks.value.length, 1);
  const keys: Array<TaskStatus | "OTHER"> = ["PENDING", "IN_PROGRESS", "PENDING_REVIEW", "COMPLETED", "DISPUTED"];
  return keys.map((key) => {
    const count = tasks.value.filter((task) => task.status === key).length;
    return {
      label: statusNames[key],
      count,
      percent: Math.round((count / total) * 100),
      color: statusColors[key] || statusColors.OTHER,
    };
  });
});

const donutStyle = computed(() => {
  let start = 0;
  const parts = statusStats.value.map((item) => {
    const end = start + item.percent;
    const segment = `${item.color} ${start}% ${end}%`;
    start = end;
    return segment;
  });
  return { background: `conic-gradient(${parts.join(", ") || "#e8e4da 0 100%"})` };
});

const hotLocations = computed(() => {
  const counts = new Map<string, number>();
  tasks.value.forEach((task) => {
    const name = task.locationDetail?.trim() || task.buildingCode || "校内地点";
    counts.set(name, (counts.get(name) || 0) + 1);
  });
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
});

const trendPoints = computed(() => {
  const days = Number(trendRange.value);
  return Array.from({ length: days }, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() - (days - index - 1));
    const key = date.toISOString().slice(0, 10);
    const dayTasks = tasks.value.filter((task) => task.createdAt.slice(0, 10) === key);
    return {
      key,
      label: `${date.getMonth() + 1}/${date.getDate()}`,
      tasks: dayTasks.length,
      amount: dayTasks.reduce((sum, task) => sum + Number(task.reward || 0), 0),
    };
  });
});

const taskTrendMax = computed(() => Math.max(...trendPoints.value.map((point) => point.tasks), 1));
const amountTrendMax = computed(() => Math.max(...trendPoints.value.map((point) => point.amount), 1));
const trendMax = computed(() => (trendMetric.value === "tasks" ? taskTrendMax.value : amountTrendMax.value));
const trendTicks = computed(() => {
  const max = trendMax.value;
  return [max, Math.ceil(max * 0.75), Math.ceil(max * 0.5), Math.ceil(max * 0.25), 0]
    .filter((v, i, arr) => arr.indexOf(v) === i)
    .map((value) => ({
      value,
      label: trendMetric.value === "amount" ? `¥${money(value)}` : money(value),
    }));
});
const taskPointPositions = computed(() => {
  const points = trendPoints.value;
  const max = taskTrendMax.value;
  return points.map((point, index) => ({
    label: point.label,
    x: 10 + (index / Math.max(points.length - 1, 1)) * 300,
    y: 148 - (point.tasks / max) * 128,
  }));
});
const taskLinePoints = computed(() => taskPointPositions.value.map((point) => `${point.x},${point.y}`).join(" "));
const amountPointPositions = computed(() => {
  const points = trendPoints.value;
  const max = amountTrendMax.value;
  return points.map((point, index) => ({
    label: point.label,
    x: 10 + (index / Math.max(points.length - 1, 1)) * 300,
    y: 148 - (point.amount / max) * 128,
  }));
});
const amountLinePoints = computed(() => amountPointPositions.value.map((point) => `${point.x},${point.y}`).join(" "));

function trendTickY(tick: number) {
  return 148 - (tick / trendMax.value) * 128;
}

function handleNav(key: NavKey) {
  if (key === "users" || key === "tasks" || key === "manage") {
    activePanel.value = "manage";
    return;
  }
  if (key === "overview" || key === "disputes" || key === "review") {
    activePanel.value = key;
    return;
  }
  const item = navItems.value.find((nav) => nav.key === key);
  devNotice.value = item?.label || "该";
}

function isNavActive(key: NavKey) {
  if ((key === "users" || key === "tasks" || key === "manage") && activePanel.value === "manage") return true;
  return key === activePanel.value;
}

function toggleTaskSort(key: TaskSortKey) {
  if (taskSortKey.value === key) {
    taskSortDir.value = taskSortDir.value === "asc" ? "desc" : "asc";
    return;
  }
  taskSortKey.value = key;
  taskSortDir.value = key === "reward" ? "desc" : "asc";
}

function sortMark(key: TaskSortKey) {
  if (taskSortKey.value !== key) return "";
  return taskSortDir.value === "asc" ? "↑" : "↓";
}

function compareTask(a: Task, b: Task, key: TaskSortKey) {
  if (key === "reward") return Number(a.reward || 0) - Number(b.reward || 0);
  const av = taskSortValue(a, key);
  const bv = taskSortValue(b, key);
  return av.localeCompare(bv, "zh-CN", { numeric: true, sensitivity: "base" });
}

function taskSortValue(task: Task, key: TaskSortKey) {
  if (key === "title") return task.title;
  if (key === "requester") return task.requester.nickname;
  if (key === "status") return statusLabel(task.status);
  if (key === "location") return task.locationDetail || task.buildingCode || "校内地点";
  return "";
}

async function loadAdminData() {
  loadError.value = "";
  try {
    const [userResult, taskResult, moderationResult, blockResult] = await Promise.all([
      adminListUsers({ page: 1, limit: 100 }),
      adminListTasks({ page: 1, limit: 100 }),
      adminListModerationRecords({ page: 1, limit: 100 }),
      adminListHomepageBlocks(),
    ]);
    usersTotal.value = userResult.meta.total;
    taskTotal.value = taskResult.meta.total;
    users.value = userResult.data;
    tasks.value = taskResult.data;
    moderationRows.value = moderationResult.data;
    homepageBlocks.value = blockResult;
  } catch (err: any) {
    loadError.value = err?.response?.data?.error?.message || "后台数据加载失败";
  }
}

async function resolveDispute(taskId: string, resolution: "refund" | "settle" | "close") {
  const note = prompt("请输入处理备注：");
  if (!note) return;
  await adminResolveDispute(taskId, { resolution, note });
  await loadAdminData();
}

async function reviewModeration(id: string, decision: "approve" | "reject") {
  const note = prompt("请输入复审备注：") || undefined;
  await adminReviewModerationRecord(id, { decision, note });
  await loadAdminData();
}

async function adjustUserCredit(user: User) {
  const nextScore = prompt("请输入新的综合信用分：", String(user.overallCreditScore));
  if (nextScore === null) return;
  const score = Number(nextScore);
  if (!Number.isFinite(score) || score < 0) {
    alert("请输入有效的信用分");
    return;
  }
  await adminUpdateUser(user.id, {
    requesterCreditScore: score,
    helperCreditScore: score,
  });
  await loadAdminData();
}

async function toggleUserActive(user: User) {
  const current = userActiveLabel(user) === "正常";
  const action = current ? "停用" : "启用";
  if (!confirm(`确认${action}用户「${user.nickname}」？`)) return;
  await adminUpdateUser(user.id, { isActive: !current });
  await loadAdminData();
}

function goTask(id: string) {
  selectedTask.value = tasks.value.find((task) => task.id === id) || null;
}

function roleLabel(role: Role) {
  return role === "ADMIN" ? "管理员" : "普通用户";
}

function userActiveLabel(user: User) {
  return user.isActive === false ? "停用" : "正常";
}

function statusLabel(status: TaskStatus) {
  return statusNames[status] || status;
}

function money(value: number) {
  return value.toLocaleString("zh-CN", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" }).replace(/\//g, "-");
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function relativeTime(value: string) {
  const delta = Date.now() - new Date(value).getTime();
  const minutes = Math.max(1, Math.floor(delta / 60000));
  if (minutes < 60) return `${minutes} 分钟前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} 小时前`;
  return `${Math.floor(hours / 24)} 天前`;
}

function moderationLabel(value: ModerationResult) {
  return value === "ALLOW" ? "通过" : value === "REVIEW" ? "待复审" : "不通过";
}

function reviewLabel(value: AdminReviewStatus) {
  return value === "PENDING" ? "待处理" : value === "APPROVED" ? "已通过" : "已拒绝";
}

function exportReport() {
  const rows: string[][] = [];
  addReportSection(rows, "总览指标", ["指标", "数值", "说明"], metricCards.value.map((item) => [item.label, String(item.value), item.caption]));
  addReportSection(
    rows,
    "任务状态分布",
    ["状态", "占比"],
    statusStats.value.map((item) => [item.label, `${item.percent}%`]),
  );
  addReportSection(
    rows,
    `平台趋势（近 ${trendRange.value} 天）`,
    ["日期", "任务数", "金额"],
    trendPoints.value.map((point) => [point.label, String(point.tasks), `¥${money(point.amount)}`]),
  );
  addReportSection(
    rows,
    "热门地点",
    ["排名", "地点", "任务数"],
    hotLocations.value.map((item, index) => [String(index + 1), item.name, String(item.count)]),
  );
  addReportSection(
    rows,
    "待处理争议",
    ["任务标题", "发布者", "金额", "创建时间", "状态"],
    disputeTasks.value.map((task) => [task.title, task.requester.nickname, `¥${task.reward}`, formatDateTime(task.createdAt), statusLabel(task.status)]),
  );
  addReportSection(
    rows,
    "AI 审核记录",
    ["记录编号", "任务编号", "风险等级", "复审状态", "命中标签", "创建时间"],
    pendingModerationRows.value.map((record) => [
      record.id,
      record.taskId || "",
      moderationLabel(record.riskLevel),
      reviewLabel(record.adminReviewStatus),
      record.hitTags.join(" / "),
      formatDateTime(record.createdAt),
    ]),
  );
  addReportSection(
    rows,
    "任务清单",
    ["任务标题", "发布者", "接单者", "状态", "金额", "地点", "截止时间", "创建时间"],
    sortedTasks.value.map((task) => [
      task.title,
      task.requester.nickname,
      task.helper?.nickname || "未接单",
      statusLabel(task.status),
      `¥${task.reward}`,
      task.locationDetail || task.buildingCode || "校内地点",
      formatDateTime(task.deadline),
      formatDateTime(task.createdAt),
    ]),
  );
  const csv = rows.map((row) => row.map(csvCell).join(",")).join("\n");
  const blob = new Blob([`\ufeff${csv}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "campusmast-admin-report.csv";
  anchor.click();
  URL.revokeObjectURL(url);
}

function addReportSection(rows: string[][], title: string, headers: string[], body: string[][]) {
  if (rows.length) rows.push([]);
  rows.push([title]);
  rows.push(headers);
  if (body.length) {
    rows.push(...body);
  } else {
    rows.push(["暂无数据"]);
  }
}

function csvCell(cell: string) {
  return `"${cell.replace(/"/g, '""')}"`;
}

async function logout() {
  authStore.logout();
  await router.push("/login");
}

onMounted(loadAdminData);
</script>

<style scoped>
.admin-page {
  --green: #6f835f;
  --green-soft: #eef1e8;
  --line: #ebe7df;
  min-height: 100dvh;
  display: grid;
  grid-template-columns: clamp(220px, 15vw, 260px) minmax(0, 1fr);
  background: #f7f5ef;
  color: #252720;
}

.admin-sidebar {
  position: sticky;
  top: 0;
  height: 100dvh;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 24px;
  padding: 22px 16px;
  border-right: 1px solid var(--line);
  background: rgba(255, 254, 251, 0.9);
}

.admin-brand {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  color: inherit;
  text-decoration: none;
}

.brand-mark {
  width: 48px;
  height: 48px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: linear-gradient(145deg, #758a65, #596e4e);
  color: #fff;
  font-size: 24px;
}

.admin-brand span:last-child {
  min-width: 0;
}

.admin-brand strong,
.admin-brand small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-brand strong {
  font-size: 18px;
  font-weight: 950;
}

.admin-brand small {
  color: #7e8178;
  font-size: 13px;
}

.admin-nav {
  display: grid;
  align-content: start;
  gap: 10px;
  margin-top: 12px;
}

.admin-nav button {
  min-width: 0;
  height: 42px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #52564e;
  cursor: pointer;
  font: inherit;
  font-weight: 800;
}

.admin-nav button.active {
  background: var(--green-soft);
  color: var(--green);
}

.admin-nav span {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-nav i {
  min-width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: #ee4f5c;
  color: #fff;
  font-size: 10px;
  font-style: normal;
  font-weight: 950;
}

.admin-account {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fffefa;
}

.admin-account > span {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #c3c7a7;
  color: #fff;
  font-weight: 950;
}

.admin-account div {
  min-width: 0;
}

.admin-account strong,
.admin-account small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-account small {
  color: #7e8178;
  font-size: 12px;
}

.admin-account button {
  grid-column: 1 / -1;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid #d9dfd0;
  border-radius: 8px;
  background: #fff;
  color: #617650;
  cursor: pointer;
  font-weight: 850;
}

.admin-main {
  min-width: 0;
}

.dashboard-shell {
  padding: clamp(20px, 2.4vw, 34px);
}

.dashboard-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 18px;
}

.dashboard-head h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 950;
}

.dashboard-head p {
  margin: 6px 0 0;
  color: #85887f;
}

.head-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.head-actions span,
.head-actions button,
.range-select {
  height: 40px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fffefa;
  color: #3f443b;
  font-weight: 800;
}

.head-actions button {
  cursor: pointer;
}

.range-select select {
  border: 0;
  outline: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  font-weight: 800;
}

.admin-error {
  margin: 0 0 14px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff1ef;
  color: #b8544a;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.kpi-card,
.dash-card {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: rgba(255, 254, 251, 0.94);
  box-shadow: 0 16px 38px rgba(60, 52, 42, 0.06);
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 86px;
  padding: 14px 12px;
}

.kpi-icon {
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-size: 22px;
}

.kpi-icon.green { background: #eef1e8; color: var(--green); }
.kpi-icon.orange { background: #fbf0df; color: #c77923; }
.kpi-icon.red { background: #fae7e3; color: #cf6254; }
.kpi-icon.blue { background: #e8f1fb; color: #4d7db9; }
.kpi-icon.purple { background: #eee9fb; color: #8371c8; }

.kpi-card div {
  min-width: 0;
}

.kpi-card small,
.kpi-card em {
  display: block;
  max-width: 100%;
  overflow: hidden;
  color: #7e8178;
  font-size: clamp(10px, 0.72vw, 11px);
  font-style: normal;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kpi-card strong {
  display: block;
  max-width: 100%;
  margin: 3px 0;
  overflow: hidden;
  font-size: clamp(18px, 1.45vw, 24px);
  font-weight: 950;
  line-height: 1.08;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(360px, 1.35fr) minmax(280px, 0.9fr) minmax(240px, 0.72fr);
  gap: 14px;
}

.dash-card {
  padding: 16px;
}

.dash-card header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.dash-card h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 950;
}

.dash-card header button,
.dash-card header span {
  margin-left: auto;
  border: 0;
  background: transparent;
  color: var(--green);
  cursor: pointer;
  font-size: 13px;
  font-weight: 850;
}

.trend-card header select {
  height: 32px;
  padding: 0 28px 0 10px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: #fffefa;
}

.trend-tools {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  margin-left: auto;
}

.trend-card header p {
  margin: 0;
  color: #7e8178;
  font-size: 12px;
}

.axis-toggle {
  display: inline-flex;
  gap: 3px;
  padding: 3px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f7f5ef;
}

.axis-toggle button {
  width: auto;
  height: 24px;
  margin-left: 0;
  padding: 0 8px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #777a72;
  cursor: pointer;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.axis-toggle button.active {
  background: #fffefa;
  color: var(--green);
  box-shadow: 0 6px 12px rgba(54, 48, 38, 0.08);
}

.trend-card header i {
  width: 7px;
  height: 7px;
  display: inline-block;
  margin-right: 5px;
  border-radius: 50%;
  background: var(--green);
}

.trend-card header i.orange {
  margin-left: 12px;
  background: #ef9b32;
}

.trend-body {
  height: 220px;
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 10px;
}

.y-axis {
  height: 184px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-top: 6px;
  color: #8b8d86;
  font-size: 11px;
  text-align: right;
}

.chart-area {
  position: relative;
  min-width: 0;
}

.trend-body svg {
  width: 100%;
  height: 184px;
  display: block;
  overflow: visible;
}

.grid-line {
  stroke: #eee9df;
  stroke-width: 1;
}

.trend-body polyline {
  fill: none;
  stroke-width: 3;
}

.task-line { stroke: var(--green); }
.amount-line { stroke: #ef9b32; }
.trend-body polyline.muted { opacity: 0.28; }
.task-dot { fill: #fff; stroke: var(--green); stroke-width: 2; }
.amount-dot { fill: #fff; stroke: #ef9b32; stroke-width: 2; }

.axis-row {
  display: grid;
  gap: 6px;
  color: #8b8d86;
  font-size: 11px;
}

.axis-row span {
  overflow: hidden;
  text-align: center;
  white-space: nowrap;
}

.status-body {
  display: grid;
  grid-template-columns: minmax(210px, 0.95fr) minmax(0, 1fr);
  gap: 18px;
  align-items: center;
}

.donut {
  width: min(229px, 100%);
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border-radius: 50%;
}

.donut span {
  width: 108px;
  height: 108px;
  display: grid;
  place-items: center;
  align-content: center;
  border-radius: 50%;
  background: #fffefa;
  color: #7e8178;
  font-size: 12px;
}

.donut strong {
  color: #252720;
  font-size: 24px;
}

.status-body ul,
.rank-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}

.status-body ul {
  margin-left: 8px;
}

.status-body li,
.rank-row {
  min-width: 0;
  display: grid;
  align-items: center;
  gap: 10px;
}

.status-body li {
  grid-template-columns: auto max-content auto;
  justify-content: start;
  gap: 10px;
}

.status-body li i {
  width: 11px;
  height: 11px;
  border-radius: 50%;
}

.status-body strong,
.rank-row strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.status-body span,
.status-body small {
  color: #7e8178;
  font-size: 13px;
}

.rank-row small {
  color: #7e8178;
  font-size: 12px;
}

.rank-row {
  grid-template-columns: 24px minmax(0, 1fr) auto;
  padding: 9px 0;
  border-bottom: 1px solid #eee9df;
}

.rank-row span {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 5px;
  background: #fff2de;
  color: #d88b2d;
  font-weight: 900;
}

.table-card {
  min-height: 0;
}

.table-card table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 13px;
}

.table-card th,
.table-card td {
  padding: 9px 8px;
  border-bottom: 1px solid #eee9df;
  overflow: hidden;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-card th {
  color: #7e8178;
  font-weight: 800;
}

.table-card th button {
  max-width: 100%;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  font-weight: inherit;
  text-align: left;
}

.scroll-table {
  max-height: min(620px, calc(100dvh - 210px));
  overflow: auto;
}

.manage-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 14px;
}

.manage-grid .scroll-table {
  max-height: min(360px, 42dvh);
}

.work-card {
  min-height: min(680px, calc(100dvh - 132px));
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  white-space: normal;
}

.actions button {
  height: 28px;
  padding: 0 9px;
  border: 1px solid #d9dfd0;
  border-radius: 7px;
  background: #fff;
  color: #617650;
  cursor: pointer;
  font-size: 12px;
  font-weight: 850;
}

.risk-ALLOW { color: var(--green); font-weight: 900; }
.risk-REVIEW { color: #c77923; font-weight: 900; }
.risk-BLOCK { color: #c85448; font-weight: 900; }

.empty-line {
  margin: 0;
  padding: 34px 0;
  color: #90938b;
  text-align: center;
  font-size: 13px;
}

.empty-line.compact {
  padding: 22px 0;
}

.admin-modal {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(34, 35, 31, 0.24);
}

.admin-modal section {
  width: min(360px, 100%);
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fffefa;
  box-shadow: 0 24px 70px rgba(60, 52, 42, 0.18);
}

.admin-modal header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.admin-modal h3 {
  margin: 0;
}

.admin-modal button {
  width: 32px;
  height: 32px;
  border: 1px solid var(--line);
  border-radius: 50%;
  background: #fff;
  cursor: pointer;
}

.admin-modal p {
  margin: 12px 0 0;
  color: #666a61;
}

.task-modal section {
  width: min(680px, 100%);
}

.task-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.task-detail-grid > div {
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fff;
}

.task-detail-grid .wide {
  grid-column: 1 / -1;
}

.task-detail-grid small {
  display: block;
  margin-bottom: 6px;
  color: #85887f;
  font-size: 12px;
  font-weight: 800;
}

.task-detail-grid strong {
  display: block;
  min-width: 0;
  overflow-wrap: anywhere;
  color: #282b25;
  font-size: 14px;
  line-height: 1.45;
}

.task-detail-grid p {
  margin: 0;
  color: #4f534b;
  font-size: 14px;
  line-height: 1.65;
  overflow-wrap: anywhere;
}

@media (max-width: 1280px) {
  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .dashboard-grid {
    grid-template-columns: 1fr 1fr;
  }

  .trend-card {
    grid-column: 1 / -1;
  }
}

@media (max-width: 920px) {
  .admin-page {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    position: relative;
    height: auto;
  }

  .dashboard-head,
  .head-actions {
    flex-wrap: wrap;
  }

  .kpi-grid,
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .status-body {
    grid-template-columns: 1fr;
  }

  .donut {
    margin: 0 auto;
  }

  .task-detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
