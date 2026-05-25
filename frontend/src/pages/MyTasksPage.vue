<template>
  <div class="my-tasks-page">
    <section class="my-tasks-shell">
      <header class="overview-card">
        <div class="overview-copy">
          <span class="eyebrow">我的任务</span>
          <h1>管理发布与接取任务</h1>
          <p>查看任务进度、处理验收与沟通，让每个任务的状态保持清晰。</p>
        </div>
        <button class="publish-button" type="button" @click="router.push('/tasks/new')">
          <AppIcon name="plus" />
          发布任务
        </button>
      </header>

      <div class="content-grid">
        <main class="task-panel">
          <div class="panel-toolbar">
            <div class="segmented" role="tablist" aria-label="任务范围">
              <button
                type="button"
                :class="{ active: tab === 'posted' }"
                role="tab"
                :aria-selected="tab === 'posted'"
                @click="switchTab('posted')"
              >
                我发布的
              </button>
              <button
                type="button"
                :class="{ active: tab === 'accepted' }"
                role="tab"
                :aria-selected="tab === 'accepted'"
                @click="switchTab('accepted')"
              >
                我接取的
              </button>
            </div>

            <label class="status-select">
              <span>状态</span>
              <select v-model="statusFilter" @change="handleStatusChange">
                <option value="">全部状态</option>
                <option value="PENDING">待接单</option>
                <option value="IN_PROGRESS">进行中</option>
                <option value="PENDING_REVIEW">待验收</option>
                <option value="COMPLETED">已完成</option>
                <option value="DISPUTED">争议中</option>
              </select>
            </label>
          </div>

          <div v-if="loading" class="state-card">
            <AppIcon name="spark" />
            <span>正在加载任务</span>
          </div>
          <div v-else-if="error" class="state-card state-error">
            <AppIcon name="alert" />
            <span>{{ error }}</span>
          </div>
          <div v-else-if="tasks.length === 0" class="state-card">
            <AppIcon name="package" />
            <span>暂无任务</span>
          </div>

          <section v-else class="task-list" aria-label="我的任务列表">
            <article
              v-for="task in tasks"
              :key="task.id"
              class="task-card"
              tabindex="0"
              @click="openTask(task.id)"
              @keydown.enter="openTask(task.id)"
            >
              <span class="task-icon" :class="`category-${task.category}`">
                <AppIcon :name="categoryIcon(task.category)" />
              </span>

              <div class="task-main">
                <div class="title-row">
                  <h2>{{ task.title }}</h2>
                  <strong>¥ {{ task.reward }}</strong>
                </div>
                <div class="tag-row">
                  <span class="category-pill" :class="`category-${task.category}`">{{ categoryLabel(task.category) }}</span>
                  <span class="status-pill" :class="`status-${task.status}`">{{ statusLabel(task.status) }}</span>
                </div>
                <p class="task-desc">{{ task.description }}</p>
                <div class="meta-row">
                  <span>
                    <AppIcon name="map-pin" />
                    {{ displayLocation(task) }}
                  </span>
                  <span>
                    <AppIcon name="calendar" />
                    {{ formatTime(task.deadline) }}
                  </span>
                  <span>
                    <AppIcon name="message" />
                    {{ counterpartLabel(task) }}
                  </span>
                </div>
              </div>

              <AppIcon class="card-arrow" name="arrow-right" />
            </article>
          </section>

          <footer v-if="total > 0" class="pagination">
            <button type="button" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
            <span>{{ page }} / {{ totalPages }}</span>
            <button type="button" :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
          </footer>
        </main>

        <aside class="side-column">
          <section class="summary-card">
            <div class="card-heading">
              <h2>{{ scopeTitle }}</h2>
              <span>{{ total }} 个任务</span>
            </div>
            <div class="summary-grid">
              <div>
                <strong>{{ activeCount }}</strong>
                <span>处理中</span>
              </div>
              <div>
                <strong>{{ reviewCount }}</strong>
                <span>待验收</span>
              </div>
              <div>
                <strong>{{ completedCount }}</strong>
                <span>已完成</span>
              </div>
              <div>
                <strong>{{ disputedCount }}</strong>
                <span>争议中</span>
              </div>
            </div>
          </section>

          <section class="guide-card">
            <div class="card-heading">
              <h2>处理建议</h2>
            </div>
            <ul>
              <li>
                <AppIcon name="message" />
                <span>任务沟通尽量保留在站内聊天中。</span>
              </li>
              <li>
                <AppIcon name="check-circle" />
                <span>完成后及时提交或确认验收，避免状态长期停留。</span>
              </li>
              <li>
                <AppIcon name="shield" />
                <span>遇到异常先查看任务详情，再按流程处理。</span>
              </li>
            </ul>
          </section>
        </aside>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { listMyAcceptedTasks, listMyPostedTasks } from "@/api/modules/task";
import AppIcon from "@/components/ui/AppIcon.vue";
import { useBuildingName } from "@/composables/useBuildings";
import type { Task, TaskCategory, TaskStatus } from "@/types/api";

const router = useRouter();
const { name: buildingName, ensure: ensureBuildings } = useBuildingName();

const tab = ref<"posted" | "accepted">("posted");
const tasks = ref<Task[]>([]);
const loading = ref(false);
const error = ref("");
const page = ref(1);
const limit = 12;
const total = ref(0);
const totalPages = ref(1);
const statusFilter = ref("");

const statusLabels: Record<TaskStatus, string> = {
  PENDING: "待接单",
  IN_PROGRESS: "进行中",
  PENDING_REVIEW: "待验收",
  COMPLETED: "已完成",
  DISPUTED: "争议中",
  CANCELLED: "已取消",
  EXPIRED: "已过期",
  CLOSED_BY_ADMIN: "已关闭",
};

const categoryLabels: Record<TaskCategory, string> = {
  package: "代取快递",
  food: "代取餐食",
  move: "跑腿代办",
  other: "其他",
};

const categoryIcons: Record<TaskCategory, string> = {
  package: "package",
  food: "food",
  move: "move",
  other: "other",
};

const scopeTitle = computed(() => (tab.value === "posted" ? "我发布的任务" : "我接取的任务"));
const activeCount = computed(() => tasks.value.filter((task) => task.status === "IN_PROGRESS").length);
const reviewCount = computed(() => tasks.value.filter((task) => task.status === "PENDING_REVIEW").length);
const completedCount = computed(() => tasks.value.filter((task) => task.status === "COMPLETED").length);
const disputedCount = computed(() => tasks.value.filter((task) => task.status === "DISPUTED").length);

function statusLabel(status: TaskStatus) {
  return statusLabels[status] ?? status;
}

function categoryLabel(category: TaskCategory) {
  return categoryLabels[category] ?? category;
}

function categoryIcon(category: TaskCategory) {
  return categoryIcons[category] ?? "other";
}

function displayLocation(task: Task) {
  return task.locationDetail || buildingName(task.buildingCode) || "未填写地点";
}

function counterpartLabel(task: Task) {
  if (tab.value === "posted") return task.helper?.nickname ? `接单人：${task.helper.nickname}` : "暂无接单人";
  return `发布者：${task.requester?.nickname || "未知用户"}`;
}

function formatTime(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "时间未知";
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${month}/${day} ${hours}:${minutes}`;
}

async function fetchTasks() {
  loading.value = true;
  error.value = "";
  try {
    const params: { page: number; limit: number; status?: string } = { page: page.value, limit };
    if (statusFilter.value) params.status = statusFilter.value;

    const response = await (tab.value === "posted" ? listMyPostedTasks : listMyAcceptedTasks)(params);
    tasks.value = response.data;
    total.value = response.meta?.total ?? response.data.length;
    totalPages.value = Math.max(1, Math.ceil(total.value / limit));
  } catch (err: any) {
    error.value = err?.response?.data?.error?.message || "加载失败";
  } finally {
    loading.value = false;
  }
}

function switchTab(nextTab: "posted" | "accepted") {
  if (tab.value === nextTab) return;
  tab.value = nextTab;
  page.value = 1;
  void fetchTasks();
}

function handleStatusChange() {
  page.value = 1;
  void fetchTasks();
}

function goPage(nextPage: number) {
  if (nextPage < 1 || nextPage > totalPages.value || nextPage === page.value) return;
  page.value = nextPage;
  void fetchTasks();
}

function openTask(id: string) {
  void router.push(`/tasks/${id}`);
}

onMounted(() => {
  void ensureBuildings();
  void fetchTasks();
});
</script>

<style scoped>
.my-tasks-page {
  min-height: calc(100dvh - 62px);
  padding: clamp(14px, 2vw, 26px);
  background: #fbfaf7;
  color: #23251f;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
}

.my-tasks-shell {
  width: min(1440px, 100%);
  margin: 0 auto;
  display: grid;
  gap: clamp(12px, 1.6vw, 18px);
}

.overview-card,
.task-panel,
.summary-card,
.guide-card {
  border: 1px solid #ece8df;
  border-radius: 16px;
  background: rgba(255, 254, 251, 0.96);
  box-shadow: 0 14px 38px rgba(54, 48, 38, 0.06);
}

.overview-card {
  min-height: clamp(76px, 9vh, 100px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: clamp(12px, 1.6vw, 18px);
}

.overview-copy {
  min-width: 0;
}

.eyebrow {
  color: #6f835f;
  font-size: 13px;
  font-weight: 900;
}

.overview-copy h1 {
  margin: 4px 0;
  font-size: clamp(20px, 2.1vw, 27px);
  line-height: 1.18;
  letter-spacing: 0;
}

.overview-copy p {
  max-width: 56ch;
  margin: 0;
  color: #777970;
  font-size: 13px;
  line-height: 1.35;
}

.publish-button {
  flex: 0 0 auto;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 18px;
  border: 0;
  border-radius: 9px;
  background: linear-gradient(135deg, #789069, #5f744f);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 900;
  box-shadow: 0 12px 24px rgba(95, 116, 79, 0.22);
}

.publish-button:hover {
  transform: translateY(-1px);
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 0.32fr);
  gap: clamp(12px, 1.6vw, 18px);
  align-items: start;
}

.task-panel {
  min-width: 0;
  height: clamp(560px, calc(100dvh - 180px), 820px);
  min-height: 560px;
  display: flex;
  flex-direction: column;
  padding: clamp(12px, 1.4vw, 16px);
  overflow: hidden;
}

.panel-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.segmented {
  min-width: min(100%, 270px);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  padding: 4px;
  border: 1px solid #ece8df;
  border-radius: 12px;
  background: #f5f3ee;
}

.segmented button {
  min-width: 0;
  height: 36px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: #676961;
  cursor: pointer;
  font-size: 13px;
  font-weight: 900;
  white-space: nowrap;
}

.segmented button.active {
  background: #fff;
  color: #6f835f;
  box-shadow: 0 8px 18px rgba(52, 46, 36, 0.08);
}

.status-select {
  position: relative;
  min-width: 168px;
  height: 42px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 34px 0 13px;
  border: 1px solid #ece8df;
  border-radius: 11px;
  background: #fff;
  color: #787a72;
  font-size: 12px;
  font-weight: 800;
}

.status-select::after {
  content: "";
  position: absolute;
  right: 14px;
  top: 50%;
  width: 7px;
  height: 7px;
  border-right: 1.8px solid #7e8279;
  border-bottom: 1.8px solid #7e8279;
  pointer-events: none;
  transform: translateY(-65%) rotate(45deg);
}

.status-select select {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  appearance: none;
  background: transparent;
  color: #242520;
  cursor: pointer;
  font: inherit;
  font-weight: 900;
}

.state-card {
  flex: 1;
  min-height: 260px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 12px;
  border: 1px dashed #ddd7cc;
  border-radius: 14px;
  background: #fffdfa;
  color: #777970;
  font-size: 14px;
}

.state-card .app-icon {
  width: 32px;
  height: 32px;
  color: #789069;
}

.state-error {
  border-color: rgba(178, 74, 58, 0.25);
  color: #b24a3a;
  background: #fff8f6;
}

.task-list {
  flex: 1;
  min-height: 0;
  display: grid;
  align-content: start;
  gap: 10px;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding-right: 5px;
  scrollbar-width: thin;
  scrollbar-color: rgba(111, 131, 95, 0.36) transparent;
}

.task-list::-webkit-scrollbar {
  width: 7px;
}

.task-list::-webkit-scrollbar-track {
  background: transparent;
}

.task-list::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(111, 131, 95, 0.32);
}

.task-card {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid #eee9df;
  border-radius: 14px;
  background: #fffdfa;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.task-card:hover,
.task-card:focus-visible {
  outline: 0;
  border-color: rgba(111, 131, 95, 0.34);
  box-shadow: 0 14px 28px rgba(54, 48, 38, 0.08);
  transform: translateY(-1px);
}

.task-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  font-size: 20px;
}

.task-icon.category-package,
.category-pill.category-package {
  background: #edf4ff;
  color: #4f82c2;
}

.task-icon.category-food,
.category-pill.category-food {
  background: #fff4e3;
  color: #bc7926;
}

.task-icon.category-move,
.category-pill.category-move {
  background: #f1f8ed;
  color: #628551;
}

.task-icon.category-other,
.category-pill.category-other {
  background: #f2eefc;
  color: #8164bd;
}

.task-main {
  min-width: 0;
  display: grid;
  gap: 5px;
}

.title-row {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.title-row h2 {
  overflow: hidden;
  margin: 0;
  color: #20221d;
  font-size: 15px;
  font-weight: 900;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.title-row strong {
  color: #6f835f;
  font-size: 17px;
  font-weight: 900;
  white-space: nowrap;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.category-pill,
.status-pill {
  max-width: 100%;
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 3px 9px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 900;
}

.status-PENDING {
  background: #f2f3ed;
  color: #6f835f;
}

.status-IN_PROGRESS {
  background: #fff4e3;
  color: #bc7926;
}

.status-PENDING_REVIEW {
  background: #edf4ff;
  color: #4f82c2;
}

.status-COMPLETED {
  background: #edf7f0;
  color: #4d8359;
}

.status-DISPUTED {
  background: #fff0ef;
  color: #b24a3a;
}

.status-CANCELLED,
.status-EXPIRED,
.status-CLOSED_BY_ADMIN {
  background: #f1f1ee;
  color: #777970;
}

.task-desc {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: #686a62;
  font-size: 13px;
  line-height: 1.42;
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
}

.meta-row {
  min-width: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  color: #8a8d86;
  font-size: 12px;
}

.meta-row span {
  min-width: 0;
  max-width: min(100%, 260px);
  display: inline-flex;
  align-items: center;
  gap: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-row .app-icon {
  flex: 0 0 auto;
  color: #9aa092;
}

.card-arrow {
  width: 18px;
  height: 18px;
  color: #9ba094;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  color: #74766e;
  font-size: 13px;
  font-weight: 800;
}

.pagination button {
  height: 34px;
  padding: 0 14px;
  border: 1px solid #e8e4da;
  border-radius: 9px;
  background: #fff;
  color: #4f5948;
  cursor: pointer;
  font: inherit;
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.42;
}

.side-column {
  min-width: 0;
  display: grid;
  gap: 12px;
}

.summary-card,
.guide-card {
  padding: 18px;
}

.card-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.card-heading h2 {
  margin: 0;
  color: #20221d;
  font-size: 16px;
  font-weight: 900;
}

.card-heading span {
  color: #6f835f;
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.summary-grid div {
  min-width: 0;
  padding: 13px;
  border: 1px solid #eee9df;
  border-radius: 12px;
  background: #fffdfa;
}

.summary-grid strong {
  display: block;
  color: #6f835f;
  font-size: 24px;
  line-height: 1;
  font-weight: 900;
}

.summary-grid span {
  display: block;
  margin-top: 7px;
  color: #81847b;
  font-size: 12px;
}

.guide-card ul {
  display: grid;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.guide-card li {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 9px;
  align-items: start;
  color: #656860;
  font-size: 13px;
  line-height: 1.55;
}

.guide-card .app-icon {
  margin-top: 2px;
  color: #6f835f;
}

@media (max-width: 1080px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .side-column {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .my-tasks-page {
    padding: 12px;
  }

  .overview-card,
  .panel-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .publish-button,
  .status-select,
  .segmented {
    width: 100%;
  }

  .task-card {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .card-arrow {
    display: none;
  }

  .title-row {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .title-row h2 {
    white-space: normal;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
  }

  .side-column {
    grid-template-columns: 1fr;
  }
}
</style>
