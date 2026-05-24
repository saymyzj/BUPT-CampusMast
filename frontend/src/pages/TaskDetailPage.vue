<template>
  <div class="page-root">
    <section class="page-container">
      <div v-if="loading" class="state-box">加载中...</div>
      <div v-else-if="loadError" class="state-box state-error">{{ loadError }}</div>
      <div v-else-if="!task" class="state-box">任务不存在或已下架</div>

      <template v-else>
        <button class="back-link" @click="$router.push('/tasks')">← 返回任务大厅</button>
        <div class="status-bar" :class="`st-${task.status}`">
          <span class="status-label">{{ statusLabel(task.status) }}</span>
          <span v-if="task.needsAdminReview" class="review-tag">⏳ 待复审</span>
        </div>

        <div class="detail-grid">
          <div class="main-panel">
            <h1 class="task-title">{{ task.title }}</h1>
            <div class="task-tags">
              <span class="tag" :class="`tag-${task.category}`">{{ categoryLabel(task.category) }}</span>
              <span class="tag tag-reward">{{ task.reward }} 元</span>
            </div>
            <p class="task-desc">{{ task.description }}</p>
            <div class="task-info">
              <span>📍 {{ bName(task.buildingCode) }}<template v-if="task.locationDetail"> · {{ task.locationDetail }}</template></span>
              <span>⏰ 截止 {{ formatTime(task.deadline) }}</span>
              <span>🕐 创建 {{ formatTime(task.createdAt) }}</span>
            </div>

            <div v-if="task.proofNote" class="proof-box">
              <h4 class="proof-title">📋 完成说明</h4>
              <p>{{ task.proofNote }}</p>
            </div>

            <!-- 操作按钮 -->
            <div v-if="actions.length > 0" class="action-bar">
              <button v-for="a in actions" :key="a.label" class="btn" :class="`btn-${a.variant}`" @click="a.handler">
                {{ a.label }}
              </button>
            </div>

            <!-- 评价 -->
            <div v-if="showRating" class="rating-card">
              <h4 class="rating-title">⭐ 评价对方</h4>
              <div class="stars">
                <button v-for="s in 5" :key="s" class="star" :class="{ on: ratingScore >= s }" @click="ratingScore = s">
                  {{ s }}★
                </button>
              </div>
              <textarea v-model="ratingComment" class="form-input form-textarea" placeholder="写几句评价..." rows="3"></textarea>
              <button class="btn btn-primary" :disabled="ratingSubmitting" @click="submitRating">
                {{ ratingSubmitting ? '提交中...' : '提交评价' }}
              </button>
              <p v-if="ratingError" class="form-error">{{ ratingError }}</p>
            </div>

            <!-- 时间线 -->
            <div class="timeline">
              <h4 class="section-title">📋 状态时间线</h4>
              <div v-if="task.logs.length === 0" class="state-box">暂无记录</div>
              <div v-for="log in task.logs" :key="log.id" class="tl-item">
                <div class="tl-dot"></div>
                <div class="tl-body">
                  <span class="tl-trans">{{ statusLabel(log.fromStatus) }} → {{ statusLabel(log.toStatus) }}</span>
                  <span class="tl-time">{{ formatTime(log.createdAt) }}</span>
                  <span v-if="log.remark" class="tl-remark">{{ log.remark }}</span>
                </div>
              </div>
            </div>
          </div>

          <aside class="side-panel">
            <div class="side-card">
              <h4 class="side-card-title">需求方</h4>
              <div class="side-user">
                <span class="side-avatar">{{ task.requester.nickname.charAt(0) }}</span>
                <div>
                  <p class="side-name">{{ task.requester.nickname }}</p>
                  <p class="side-credit">信用 {{ task.requester.overallCreditScore }}</p>
                </div>
              </div>
            </div>
            <div v-if="task.helper" class="side-card">
              <h4 class="side-card-title">接单方</h4>
              <div class="side-user">
                <span class="side-avatar side-av-helper">{{ task.helper.nickname.charAt(0) }}</span>
                <div>
                  <p class="side-name">{{ task.helper.nickname }}</p>
                  <p class="side-credit">信用 {{ task.helper.overallCreditScore }}</p>
                </div>
              </div>
            </div>
            <div class="side-card side-card-info">
              <p class="info-row">审核 {{ task.moderationResult }}</p>
            </div>
          </aside>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { getTaskById, acceptTask, submitTaskProof, confirmTask, rejectTask, cancelTask, abandonTask, rateTaskPartner } from "@/api/modules/task";
import { useAuthStore } from "@/stores/auth";
import { useBuildingName } from "@/composables/useBuildings";
import { isTaskVisible } from "@/utils/taskVisibility";
import type { TaskDetail, TaskStatus, TaskCategory } from "@/types/api";

const route = useRoute();
const authStore = useAuthStore();
const { name: bName, ensure: ensureBuildings } = useBuildingName();

const task = ref<TaskDetail | null>(null);
const loading = ref(false);
const loadError = ref("");
const showRating = ref(false);
const ratingScore = ref(5);
const ratingComment = ref("");
const ratingSubmitting = ref(false);
const ratingError = ref("");

const S: Record<string, string> = {
  PENDING: "待接单", IN_PROGRESS: "进行中", PENDING_REVIEW: "待验收",
  COMPLETED: "已完成", DISPUTED: "争议中", CANCELLED: "已取消", EXPIRED: "已过期", CLOSED_BY_ADMIN: "管理员关闭",
};
const C: Record<string, string> = { package: "快递代取", food: "代买餐食", move: "搬运重物", other: "其他" };
function statusLabel(s: TaskStatus) { return S[s] ?? s; }
function categoryLabel(c: TaskCategory) { return C[c] ?? c; }
function formatTime(iso: string) { return new Date(iso).toLocaleString("zh-CN"); }

const userId = computed(() => authStore.userId ?? "");
const isRequester = computed(() => task.value?.requester.id === userId.value);
const isHelper = computed(() => task.value?.helper?.id === userId.value);
const s = computed(() => task.value?.status as TaskStatus);

interface Action { label: string; variant: string; handler: () => void; }
const actions = computed<Action[]>(() => {
  if (!task.value) return [];
  const a: Action[] = [];
  const st = s.value;
  if (st === "PENDING" && isRequester.value) a.push({ label: "取消任务", variant: "danger", handler: handleCancel });
  if (st === "PENDING" && !isRequester.value && !isHelper.value) a.push({ label: "接单", variant: "primary", handler: handleAccept });
  if (st === "IN_PROGRESS" && isHelper.value) {
    a.push({ label: "提交完成", variant: "primary", handler: handleSubmit });
    a.push({ label: "放弃任务", variant: "danger", handler: handleAbandon });
  }
  if (st === "IN_PROGRESS" && isRequester.value) a.push({ label: "发起争议", variant: "danger", handler: handleDispute });
  if (st === "PENDING_REVIEW" && isRequester.value) {
    a.push({ label: "确认完成", variant: "primary", handler: handleConfirm });
    a.push({ label: "拒绝验收", variant: "danger", handler: handleReject });
  }
  if (st === "COMPLETED" && (isRequester.value || isHelper.value)) a.push({ label: "评价对方", variant: "secondary", handler: () => { showRating.value = true; } });
  return a;
});

async function loadTask() {
  loading.value = true; loadError.value = "";
  try {
    const loaded = await getTaskById(route.params.id as string);
    task.value = isTaskVisible(loaded) ? loaded : null;
  } catch (err: any) { loadError.value = err?.response?.data?.error?.message || "加载失败"; } finally { loading.value = false; }
}
async function doAction(name: string, fn: () => Promise<any>) { try { await fn(); await loadTask(); } catch (err: any) { alert(`${name}失败：${err?.response?.data?.error?.message || "请重试"}`); } }
async function handleAccept() { await doAction("接单", () => acceptTask(task.value!.id)); }
async function handleSubmit() { await doAction("提交", () => submitTaskProof(task.value!.id, { proofNote: "已完成任务" })); }
async function handleConfirm() { await doAction("确认", () => confirmTask(task.value!.id)); }
async function handleCancel() { await doAction("取消", () => cancelTask(task.value!.id)); }
async function handleAbandon() { await doAction("放弃", () => abandonTask(task.value!.id)); }
async function handleReject() { const r = prompt("请输入拒绝原因："); if (r) await doAction("拒绝", () => rejectTask(task.value!.id, { reason: r })); }
async function handleDispute() { const r = prompt("请输入争议原因："); if (r) await doAction("发起争议", () => rejectTask(task.value!.id, { reason: r })); }
async function submitRating() {
  if (!task.value) return; ratingError.value = ""; ratingSubmitting.value = true;
  try { await rateTaskPartner(task.value.id, { score: ratingScore.value, comment: ratingComment.value.trim() || undefined }); showRating.value = false; await loadTask(); } catch (err: any) { ratingError.value = err?.response?.data?.error?.message || "评价失败"; } finally { ratingSubmitting.value = false; }
}
onMounted(() => { ensureBuildings(); loadTask(); });
</script>

<style scoped>
.page-root {
  --blue-500: #2556a8; --blue-600: #1f478c; --blue-50: #edf3fb;
  --red-500: #b24a3a; --orange-500: #c67f2f; --green-500: #2f7a41; --purple-500: #7c3aed;
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
.page-container { position: relative; z-index: 1; padding: 40px 20px; max-width: 960px; margin: 0 auto; }
.back-link { display: inline-block; margin-bottom: 20px; padding: 6px 0; font-size: 14px; color: var(--blue-500); background: none; border: none; cursor: pointer; font-weight: 500; transition: color 0.2s; }
.back-link:hover { color: var(--blue-600); }
.state-box { text-align: center; padding: 80px 20px; color: var(--gray-600); font-size: 15px; }
.state-error { color: var(--red-500); background: #fff5f5; border-radius: var(--radius-lg); }

.status-bar { padding: 14px 24px; border-radius: var(--radius); margin-bottom: 24px; display: flex; align-items: center; gap: 12px; }
.st-PENDING { background: #dbeafe; color: #1e40af; }
.st-IN_PROGRESS { background: #fef3c7; color: #92400e; }
.st-PENDING_REVIEW { background: #ede9fe; color: #6b21a8; }
.st-COMPLETED { background: #d1fae5; color: #065f46; }
.st-DISPUTED { background: #fee2e2; color: #991b1b; }
.st-CANCELLED, .st-EXPIRED, .st-CLOSED_BY_ADMIN { background: #f3f4f6; color: #374151; }
.status-label { font-size: 16px; font-weight: 700; }
.review-tag { font-size: 12px; padding: 2px 10px; background: rgba(255,255,255,0.7); border-radius: 99px; font-weight: 600; }

.detail-grid { display: grid; grid-template-columns: 1fr 260px; gap: 24px; }
@media (max-width: 768px) { .detail-grid { grid-template-columns: 1fr; } }

.main-panel { background: #faf7f1; border: 1px solid rgba(31,42,58,0.04); border-radius: var(--radius-lg); padding: 32px; box-shadow: var(--shadow-lg); }
.task-title { font-size: 24px; font-weight: 700; color: var(--gray-800); margin-bottom: 12px; font-family: 'Nunito','Noto Sans SC',sans-serif; }
.task-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.tag { padding: 3px 12px; border-radius: var(--radius-sm); font-size: 12px; font-weight: 600; }
.tag-package { background: #dbeafe; color: #1e40af; }
.tag-food { background: #fef3c7; color: #92400e; }
.tag-move { background: #ede9fe; color: #6b21a8; }
.tag-other { background: #f3f4f6; color: #374151; }
.tag-reward { background: #fce7f3; color: #be185d; }
.task-desc { font-size: 15px; color: var(--gray-600); line-height: 1.6; margin-bottom: 16px; white-space: pre-wrap; }
.task-info { display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: var(--gray-600); }
.proof-box { margin-top: 16px; padding: 14px 16px; background: #f0fdf4; border-radius: var(--radius); font-size: 14px; color: var(--gray-800); }
.proof-title { font-size: 13px; font-weight: 600; margin-bottom: 4px; }

.action-bar { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--gray-100); }
.btn { padding: 10px 22px; border-radius: var(--radius); font-size: 14px; font-weight: 600; border: none; cursor: pointer; transition: all 0.25s; }
.btn:hover { transform: translateY(-1px); }
.btn-primary { background: var(--blue-500); color: #fff; }
.btn-primary:hover { background: var(--blue-600); box-shadow: 0 6px 16px rgba(37,86,168,0.25); }
.btn-danger { background: #fff; color: var(--red-500); border: 1px solid var(--red-500); }
.btn-danger:hover { background: #fff5f5; box-shadow: 0 6px 16px rgba(178,74,58,0.12); }
.btn-secondary { background: #fff; color: var(--blue-500); border: 1px solid var(--blue-500); }
.btn-secondary:hover { background: var(--blue-50); box-shadow: 0 6px 16px rgba(37,86,168,0.1); }

.rating-card { margin-top: 24px; padding: 20px; background: #fff; border-radius: var(--radius); border: 1px solid var(--gray-100); }
.rating-title { font-size: 15px; font-weight: 600; color: var(--gray-800); margin-bottom: 12px; }
.stars { display: flex; gap: 6px; margin-bottom: 12px; }
.star { padding: 4px 10px; background: none; border: 1px solid var(--gray-300); border-radius: var(--radius-sm); cursor: pointer; font-size: 18px; color: var(--gray-300); transition: all 0.2s; }
.star.on { border-color: #f59e0b; color: #f59e0b; background: #fffbeb; }
.form-input, .form-textarea { width: 100%; padding: 10px 14px; font-size: 14px; border: 1px solid var(--gray-100); border-radius: var(--radius); background: #fff; color: var(--gray-800); box-sizing: border-box; font-family: inherit; }
.form-textarea { resize: vertical; }
.form-error { margin-top: 8px; padding: 10px 14px; font-size: 13px; background: #ffebee; color: var(--red-500); border-radius: var(--radius); }

.timeline { margin-top: 32px; }
.section-title { font-size: 15px; font-weight: 600; color: var(--gray-800); margin-bottom: 16px; }
.tl-item { display: flex; gap: 12px; margin-bottom: 14px; font-size: 13px; }
.tl-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--blue-500); margin-top: 4px; flex-shrink: 0; }
.tl-trans { color: var(--gray-800); font-weight: 600; display: block; }
.tl-time { color: var(--gray-600); font-size: 12px; }
.tl-remark { display: block; color: var(--gray-600); font-size: 12px; margin-top: 2px; }

.side-panel { display: flex; flex-direction: column; gap: 16px; }
.side-card { background: #faf7f1; border: 1px solid rgba(31,42,58,0.04); border-radius: var(--radius-lg); padding: 20px; box-shadow: var(--shadow-sm); }
.side-card-title { font-size: 12px; color: var(--gray-600); margin-bottom: 12px; font-weight: 500; }
.side-user { display: flex; align-items: center; gap: 12px; }
.side-avatar { width: 40px; height: 40px; border-radius: var(--radius); background: var(--blue-500); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 700; }
.side-av-helper { background: var(--green-500); }
.side-name { font-size: 15px; font-weight: 600; color: var(--gray-800); }
.side-credit { font-size: 12px; color: var(--blue-500); margin-top: 2px; }
.side-card-info { font-size: 12px; color: var(--gray-600); }
.info-row { margin-bottom: 4px; }
</style>
