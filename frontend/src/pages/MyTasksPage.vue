<template>
  <div class="page-root">
    <section class="page-container">
      <div class="page-header">
        <h1 class="page-title">我的任务</h1>
        <p class="page-subtitle">管理你发布和接取的任务</p>
      </div>

      <div class="tabs">
        <button class="tab" :class="{ active: tab === 'posted' }" @click="switchTab('posted')">我发布的</button>
        <button class="tab" :class="{ active: tab === 'accepted' }" @click="switchTab('accepted')">我接取的</button>
      </div>

      <div class="filter-bar">
        <select v-model="statusFilter" class="filter-select" @change="fetchTasks">
          <option value="">全部状态</option>
          <option value="PENDING">待接单</option>
          <option value="IN_PROGRESS">进行中</option>
          <option value="PENDING_REVIEW">待验收</option>
          <option value="COMPLETED">已完成</option>
          <option value="DISPUTED">争议中</option>
        </select>
      </div>

      <div v-if="loading" class="state-box">加载中...</div>
      <div v-else-if="error" class="state-box state-error">{{ error }}</div>
      <div v-else-if="tasks.length === 0" class="state-box">暂无任务</div>

      <div v-else class="task-list">
        <div v-for="t in tasks" :key="t.id" class="task-card" @click="$router.push(`/tasks/${t.id}`)">
          <div class="card-top">
            <span class="status-badge" :class="`st-${t.status}`">{{ statusLabel(t.status) }}</span>
            <span class="tag" :class="`tag-${t.category}`">{{ categoryLabel(t.category) }}</span>
            <span class="tag tag-reward">{{ t.reward }} 元</span>
          </div>
          <h3 class="card-title">{{ t.title }}</h3>
          <p class="card-desc">{{ t.description }}</p>
          <div class="card-meta">
            <span>📍 {{ bName(t.buildingCode) }}</span>
            <span>⏰ {{ formatTime(t.deadline) }}</span>
          </div>
        </div>
      </div>

      <div v-if="total > 0" class="pagination">
        <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <span class="page-info">{{ page }} / {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { listMyPostedTasks, listMyAcceptedTasks } from "@/api/modules/task";
import { useBuildingName } from "@/composables/useBuildings";
import type { Task, TaskStatus, TaskCategory } from "@/types/api";

const router = useRouter();
const { name: bName, ensure: ensureBuildings } = useBuildingName();
const tab = ref<"posted" | "accepted">("posted");
const tasks = ref<Task[]>([]);
const loading = ref(false);
const error = ref("");
const page = ref(1);
const limit = 12;
const total = ref(0);
const totalPages = ref(1);
const statusFilter = ref("");

const S: Record<string, string> = {
  PENDING: "待接单", IN_PROGRESS: "进行中", PENDING_REVIEW: "待验收",
  COMPLETED: "已完成", DISPUTED: "争议中", CANCELLED: "已取消", EXPIRED: "已过期", CLOSED_BY_ADMIN: "管理员关闭",
};
const C: Record<string, string> = { package: "快递代取", food: "代买餐食", move: "搬运重物", other: "其他" };
function statusLabel(s: TaskStatus) { return S[s] ?? s; }
function categoryLabel(c: TaskCategory) { return C[c] ?? c; }
function formatTime(iso: string) {
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

async function fetchTasks() {
  loading.value = true; error.value = "";
  try {
    const params: Record<string, unknown> = { page: page.value, limit };
    if (statusFilter.value) params.status = statusFilter.value;
    const r = await (tab.value === "posted" ? listMyPostedTasks : listMyAcceptedTasks)(params as any);
    tasks.value = r.data; total.value = r.meta.total; totalPages.value = Math.max(1, Math.ceil(r.meta.total / limit));
  } catch (err: any) { error.value = err?.response?.data?.error?.message || "加载失败"; } finally { loading.value = false; }
}
function switchTab(t: "posted" | "accepted") { tab.value = t; page.value = 1; fetchTasks(); }
function goPage(p: number) { page.value = p; fetchTasks(); }
onMounted(() => { ensureBuildings(); fetchTasks(); });
</script>

<style scoped>
.page-root {
  --blue-500: #2556a8; --blue-600: #1f478c; --blue-50: #edf3fb;
  --red-500: #b24a3a; --green-500: #2f7a41; --purple-500: #7c3aed;
  --gray-50: #f6f1e6; --gray-100: #ece3d2; --gray-300: #b9ad95; --gray-600: #50493f; --gray-800: #202735;
  --bg-start: #fbf7ef; --bg-end: #efe6d6;
  --shadow-sm: 0 2px 6px rgba(23,29,40,0.04); --shadow-md: 0 8px 20px rgba(23,29,40,0.07);
  --shadow-lg: 0 14px 32px rgba(23,29,40,0.10);
  --radius-sm: 6px; --radius: 10px; --radius-lg: 16px;
  min-height: 100vh;
  background: linear-gradient(175deg, var(--bg-start) 0%, #f4efe0 50%, var(--bg-end) 100%);
  background-attachment: fixed; position: relative;
}
.page-root::before {
  content: ''; position: fixed; inset: 0; z-index: 0;
  background-image: linear-gradient(rgba(37,86,168,0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37,86,168,0.06) 1px, transparent 1px);
  background-size: 32px 32px; opacity: 0.4; pointer-events: none;
}
.page-container { position: relative; z-index: 1; padding: 40px 20px; max-width: 860px; margin: 0 auto; }
.page-header { margin-bottom: 28px; }
.page-title { font-size: 32px; font-weight: 700; color: var(--gray-800); font-family: 'Nunito','Noto Sans SC',sans-serif; }
.page-subtitle { font-size: 15px; color: var(--gray-600); margin-top: 6px; }

.tabs { display: flex; margin-bottom: 20px; align-items: center; }
.tab { display: inline-flex; align-items: center; justify-content: center; height: 44px; padding: 0 28px; font-size: 14px; font-weight: 600; background: #fff; border: 1px solid var(--gray-100); cursor: pointer; color: var(--gray-600); transition: all 0.25s; line-height: 1; }
.tab:first-child { border-radius: var(--radius) 0 0 var(--radius); }
.tab:last-child { border-radius: 0 var(--radius) var(--radius) 0; }
.tab:hover { background: var(--blue-50); color: var(--blue-500); }
.tab.active { background: var(--blue-500); color: #fff; border-color: var(--blue-500); }

.filter-bar { margin-bottom: 20px; }
.filter-select { appearance: none; -webkit-appearance: none; padding: 10px 36px 10px 14px; font-size: 13px; border: 1px solid var(--gray-100); border-radius: var(--radius); background: #fff; color: var(--gray-800); cursor: pointer; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2350493f' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; transition: border 0.2s; }
.filter-select:focus { outline: none; border-color: var(--blue-500); }

.state-box { text-align: center; padding: 80px 20px; color: var(--gray-600); font-size: 15px; }
.state-error { color: var(--red-500); background: #fff5f5; border-radius: var(--radius-lg); }

.task-list { display: flex; flex-direction: column; gap: 16px; }
.task-card {
  background: #faf7f1; border: 1px solid rgba(31,42,58,0.04); border-radius: var(--radius-lg);
  padding: 20px 24px; box-shadow: var(--shadow-sm); cursor: pointer;
  transition: all 0.35s cubic-bezier(0.3, 0, 0.2, 1);
}
.task-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); border-color: rgba(37,86,168,0.2); }
.card-top { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 10px; }
.status-badge { padding: 3px 10px; border-radius: var(--radius-sm); font-size: 12px; font-weight: 700; }
.st-PENDING { background: #dbeafe; color: #1e40af; }
.st-IN_PROGRESS { background: #fef3c7; color: #92400e; }
.st-PENDING_REVIEW { background: #ede9fe; color: #6b21a8; }
.st-COMPLETED { background: #d1fae5; color: #065f46; }
.st-DISPUTED { background: #fee2e2; color: #991b1b; }
.st-CANCELLED, .st-EXPIRED, .st-CLOSED_BY_ADMIN { background: #f3f4f6; color: #374151; }
.tag { padding: 3px 10px; border-radius: var(--radius-sm); font-size: 12px; font-weight: 600; }
.tag-package { background: #dbeafe; color: #1e40af; }
.tag-food { background: #fef3c7; color: #92400e; }
.tag-move { background: #ede9fe; color: #6b21a8; }
.tag-other { background: #f3f4f6; color: #374151; }
.tag-reward { background: #fce7f3; color: #be185d; }
.card-title { font-size: 16px; font-weight: 700; color: var(--gray-800); margin-bottom: 6px; }
.card-desc { font-size: 13px; color: var(--gray-600); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-meta { display: flex; gap: 16px; font-size: 12px; color: var(--gray-600); margin-top: 8px; }

.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 32px; font-size: 14px; color: var(--gray-600); }
.pagination button { padding: 8px 18px; border: 1px solid var(--gray-100); border-radius: var(--radius); background: #fff; cursor: pointer; color: var(--gray-800); font-weight: 500; transition: all 0.25s; }
.pagination button:hover:not(:disabled) { border-color: var(--blue-500); color: var(--blue-500); transform: translateY(-1px); box-shadow: var(--shadow-sm); }
.pagination button:disabled { opacity: 0.35; cursor: not-allowed; }
.page-info { font-weight: 600; }
</style>
