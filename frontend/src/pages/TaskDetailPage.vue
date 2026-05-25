<template>
  <div class="detail-page">
    <section class="detail-shell">
      <div v-if="loading" class="state-box">任务加载中...</div>
      <div v-else-if="loadError" class="state-box error">{{ loadError }}</div>
      <div v-else-if="!task" class="state-box">任务不存在或已下架</div>

      <template v-else>
        <button class="back-link" type="button" @click="router.push('/tasks')">
          <AppIcon name="arrow-right" />
          返回任务大厅
        </button>

        <section class="detail-hero">
          <div class="hero-main">
            <div class="hero-topline">
              <span class="category-pill" :class="`category-${task.category}`">
                <AppIcon :name="categoryIcon(task.category)" />
                {{ categoryLabel(task.category) }}
              </span>
              <span class="status-pill" :class="`status-${task.status}`">{{ statusLabel(task.status) }}</span>
            </div>

            <div class="title-row">
              <h1>{{ task.title }}</h1>
              <strong>¥ {{ task.reward }}</strong>
            </div>

            <p class="task-description">{{ task.description }}</p>

            <div class="info-grid">
              <article>
                <AppIcon name="location" />
                <span>详细地点</span>
                <strong>{{ locationText }}</strong>
              </article>
              <article>
                <AppIcon name="calendar" />
                <span>截止时间</span>
                <strong>{{ formatTime(task.deadline) }}</strong>
              </article>
              <article>
                <AppIcon name="clock" />
                <span>发布时间</span>
                <strong>{{ formatTime(task.createdAt) }}</strong>
              </article>
            </div>
          </div>

          <aside class="hero-side">
            <span>剩余时间</span>
            <strong>{{ deadlineText }}</strong>
            <small>任务编号 {{ shortId(task.id) }}</small>
          </aside>
        </section>

        <section class="detail-layout">
          <main class="main-column">
            <section v-if="task.imageUrls.length" class="content-card">
              <header>
                <h2>任务图片</h2>
              </header>
              <div class="image-grid">
                <img v-for="url in task.imageUrls" :key="url" :src="url" alt="" />
              </div>
            </section>

            <section v-if="task.proofNote || task.proofImageUrls.length" class="content-card proof-card">
              <header>
                <h2>完成说明</h2>
                <span>{{ task.proofImageUrls.length }} 张凭证</span>
              </header>
              <p v-if="task.proofNote">{{ task.proofNote }}</p>
              <div v-if="task.proofImageUrls.length" class="image-grid">
                <img v-for="url in task.proofImageUrls" :key="url" :src="url" alt="" />
              </div>
            </section>

            <section v-if="actions.length" class="content-card action-card">
              <header>
                <h2>任务操作</h2>
                <span>{{ actionHint }}</span>
              </header>
              <div class="action-list">
                <button
                  v-for="action in actions"
                  :key="action.label"
                  type="button"
                  class="action-button"
                  :class="`action-${action.variant}`"
                  @click="action.handler"
                >
                  {{ action.label }}
                </button>
              </div>
            </section>

            <section v-if="showRating" class="content-card rating-card">
              <header>
                <h2>评价对方</h2>
                <button type="button" @click="showRating = false">收起</button>
              </header>
              <div class="stars">
                <button
                  v-for="score in 5"
                  :key="score"
                  type="button"
                  :class="{ active: ratingScore >= score }"
                  @click="ratingScore = score"
                >
                  <AppIcon name="star" />
                </button>
              </div>
              <textarea v-model.trim="ratingComment" maxlength="300" placeholder="写几句评价..." />
              <p v-if="ratingError" class="form-error">{{ ratingError }}</p>
              <button class="submit-rating" type="button" :disabled="ratingSubmitting" @click="submitRating">
                {{ ratingSubmitting ? "提交中..." : "提交评价" }}
              </button>
            </section>

            <section class="content-card timeline-card">
              <header>
                <h2>状态时间线</h2>
                <span>{{ task.logs.length }} 条记录</span>
              </header>
              <p v-if="task.logs.length === 0" class="empty-line">暂无状态记录</p>
              <div v-else class="timeline-list" aria-label="任务状态时间轴">
                <article v-for="log in task.logs" :key="log.id" class="timeline-item">
                  <i></i>
                  <div>
                    <strong>{{ statusLabel(log.fromStatus) }} → {{ statusLabel(log.toStatus) }}</strong>
                    <span>{{ formatTime(log.createdAt) }}</span>
                    <p v-if="log.remark">{{ remarkLabel(log.remark) }}</p>
                  </div>
                </article>
              </div>
            </section>
          </main>

          <aside class="side-column">
            <section class="side-card">
              <header>
                <h2>需求方</h2>
              </header>
              <div class="user-mini">
                <span class="user-avatar avatar-requester">{{ task.requester.nickname.slice(0, 1) }}</span>
                <div>
                  <strong>{{ task.requester.nickname }}</strong>
                  <small>信用分 {{ task.requester.overallCreditScore }}</small>
                </div>
              </div>
            </section>

            <section class="side-card">
              <header>
                <h2>接单方</h2>
              </header>
              <div v-if="task.helper" class="user-mini">
                <span class="user-avatar avatar-helper">{{ task.helper.nickname.slice(0, 1) }}</span>
                <div>
                  <strong>{{ task.helper.nickname }}</strong>
                  <small>信用分 {{ task.helper.overallCreditScore }}</small>
                </div>
              </div>
              <p v-else class="empty-line">当前任务尚未被接取</p>
            </section>
          </aside>
        </section>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppIcon from "@/components/ui/AppIcon.vue";
import {
  abandonTask,
  acceptTask,
  cancelTask,
  confirmTask,
  getTaskById,
  rateTaskPartner,
  rejectTask,
  submitTaskProof,
} from "@/api/modules/task";
import { useBuildingName } from "@/composables/useBuildings";
import { useAuthStore } from "@/stores/auth";
import { isTaskVisible } from "@/utils/taskVisibility";
import type { TaskCategory, TaskDetail, TaskStatus } from "@/types/api";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const { name: buildingName, ensure: ensureBuildings } = useBuildingName();

const task = ref<TaskDetail | null>(null);
const loading = ref(false);
const loadError = ref("");
const showRating = ref(false);
const ratingScore = ref(5);
const ratingComment = ref("");
const ratingSubmitting = ref(false);
const ratingError = ref("");

const statusLabels: Record<TaskStatus, string> = {
  PENDING: "待接单",
  IN_PROGRESS: "进行中",
  PENDING_REVIEW: "待验收",
  COMPLETED: "已完成",
  DISPUTED: "争议中",
  CANCELLED: "已取消",
  EXPIRED: "已过期",
  CLOSED_BY_ADMIN: "后台关闭",
};

const categoryLabels: Record<TaskCategory, string> = {
  package: "代取快递",
  food: "代买餐食",
  move: "搬运重物",
  other: "其他",
};

const categoryIcons: Record<TaskCategory, string> = {
  package: "package",
  food: "food",
  move: "move",
  other: "other",
};

const userId = computed(() => authStore.userId ?? "");
const isRequester = computed(() => task.value?.requester.id === userId.value);
const isHelper = computed(() => task.value?.helper?.id === userId.value);
const currentStatus = computed(() => task.value?.status as TaskStatus | undefined);
const locationText = computed(() => {
  if (!task.value) return "校内地点";
  const detail = task.value.locationDetail?.trim();
  const building = task.value.buildingCode ? buildingName(task.value.buildingCode) : "";
  if (detail && building && detail !== building) return `${building} · ${detail}`;
  return detail || building || "校内地点";
});
const deadlineText = computed(() => {
  if (!task.value) return "--";
  const diff = new Date(task.value.deadline).getTime() - Date.now();
  if (diff <= 0) return "已截止";
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes} 分钟`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} 小时`;
  return `${Math.floor(hours / 24)} 天`;
});
const actionHint = computed(() => {
  if (!task.value) return "";
  if (isRequester.value) return "你是该任务发布者";
  if (isHelper.value) return "你是该任务接单者";
  return "确认信息后可接取任务";
});

interface Action {
  label: string;
  variant: "primary" | "danger" | "secondary";
  handler: () => void;
}

const actions = computed<Action[]>(() => {
  if (!task.value || !currentStatus.value) return [];
  const list: Action[] = [];
  const status = currentStatus.value;
  if (status === "PENDING" && isRequester.value) list.push({ label: "取消任务", variant: "danger", handler: handleCancel });
  if (status === "PENDING" && !isRequester.value && !isHelper.value) list.push({ label: "接取任务", variant: "primary", handler: handleAccept });
  if (status === "IN_PROGRESS" && isHelper.value) {
    list.push({ label: "提交完成", variant: "primary", handler: handleSubmit });
    list.push({ label: "放弃任务", variant: "danger", handler: handleAbandon });
  }
  if (status === "IN_PROGRESS" && isRequester.value) list.push({ label: "发起争议", variant: "danger", handler: handleDispute });
  if (status === "PENDING_REVIEW" && isRequester.value) {
    list.push({ label: "确认完成", variant: "primary", handler: handleConfirm });
    list.push({ label: "拒绝验收", variant: "danger", handler: handleReject });
  }
  if (status === "COMPLETED" && (isRequester.value || isHelper.value)) {
    list.push({ label: "评价对方", variant: "secondary", handler: () => { showRating.value = true; } });
  }
  return list;
});

function statusLabel(status: TaskStatus) {
  return statusLabels[status] ?? status;
}

function categoryLabel(category: TaskCategory) {
  return categoryLabels[category] ?? category;
}

function categoryIcon(category: TaskCategory) {
  return categoryIcons[category] ?? "other";
}

function shortId(id: string) {
  return id.slice(0, 8);
}

const remarkLabels: Record<string, string> = {
  "Task created and reward frozen": "任务已创建，赏金已冻结",
  "Task accepted by helper": "任务已被接取",
  "Task cancelled by requester": "发布者已取消任务",
  "Task expired by system": "任务已超时关闭",
  "Task abandoned by helper": "接单者已放弃任务",
  "Task disputed by requester": "发布者已发起争议",
  "Task confirmed by requester": "发布者已确认完成",
  "Task confirmed": "发布者已确认完成",
  "Task cancelled": "任务已取消",
  "Helper abandoned task": "接单者已放弃任务",
  "Proof submitted": "接单者已提交完成说明",
  "Dispute resolved in favor of helper": "争议已处理，任务完成",
  "Dispute resolved in favor of requester": "争议已处理，任务取消",
  "Dispute closed by admin": "争议已关闭",
};

function remarkLabel(remark: string) {
  const normalized = remark.trim();
  if (remarkLabels[normalized]) return remarkLabels[normalized];
  if (/[A-Za-z]/.test(normalized)) return "任务状态已更新";
  return normalized;
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function loadTask() {
  loading.value = true;
  loadError.value = "";
  try {
    const loaded = await getTaskById(route.params.id as string);
    task.value = isTaskVisible(loaded) ? loaded : null;
  } catch (err: any) {
    loadError.value = err?.response?.data?.error?.message || "加载失败";
  } finally {
    loading.value = false;
  }
}

async function doAction(name: string, fn: () => Promise<unknown>) {
  try {
    await fn();
    await loadTask();
  } catch (err: any) {
    alert(`${name}失败：${err?.response?.data?.error?.message || "请重试"}`);
  }
}

async function handleAccept() {
  await doAction("接单", () => acceptTask(task.value!.id));
}

async function handleSubmit() {
  const note = prompt("请输入完成说明：") || "已完成任务";
  await doAction("提交", () => submitTaskProof(task.value!.id, { proofNote: note }));
}

async function handleConfirm() {
  await doAction("确认", () => confirmTask(task.value!.id));
}

async function handleCancel() {
  await doAction("取消", () => cancelTask(task.value!.id));
}

async function handleAbandon() {
  await doAction("放弃", () => abandonTask(task.value!.id));
}

async function handleReject() {
  const reason = prompt("请输入拒绝原因：");
  if (reason) await doAction("拒绝", () => rejectTask(task.value!.id, { reason }));
}

async function handleDispute() {
  const reason = prompt("请输入争议原因：");
  if (reason) await doAction("发起争议", () => rejectTask(task.value!.id, { reason }));
}

async function submitRating() {
  if (!task.value) return;
  ratingError.value = "";
  ratingSubmitting.value = true;
  try {
    await rateTaskPartner(task.value.id, {
      score: ratingScore.value,
      comment: ratingComment.value.trim() || undefined,
    });
    showRating.value = false;
    await loadTask();
  } catch (err: any) {
    ratingError.value = err?.response?.data?.error?.message || "评价失败";
  } finally {
    ratingSubmitting.value = false;
  }
}

onMounted(() => {
  ensureBuildings();
  loadTask();
});
</script>

<style scoped>
.detail-page {
  min-height: calc(100dvh - 86px);
  padding: clamp(18px, 2.4vw, 30px);
  background: #f7f5ef;
  color: #252720;
}

.detail-shell {
  width: min(100%, 1480px);
  margin: 0 auto;
}

.state-box {
  display: grid;
  place-items: center;
  min-height: 260px;
  border: 1px solid #ebe7df;
  border-radius: 12px;
  background: rgba(255, 254, 251, 0.92);
  color: #7e8178;
}

.state-box.error {
  color: #b8544a;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  border: 0;
  background: transparent;
  color: #6f835f;
  cursor: pointer;
  font-size: 14px;
  font-weight: 850;
}

.back-link .app-icon {
  transform: rotate(180deg);
}

.detail-hero,
.content-card,
.side-card {
  border: 1px solid #ebe7df;
  border-radius: 12px;
  background: rgba(255, 254, 251, 0.94);
  box-shadow: 0 16px 38px rgba(60, 52, 42, 0.06);
}

.detail-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(180px, 220px);
  gap: 18px;
  padding: clamp(22px, 2.6vw, 34px);
  overflow: hidden;
}

.hero-main {
  min-width: 0;
}

.hero-topline,
.title-row,
.action-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.category-pill,
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
}

.category-package { background: #e8f1fb; color: #4778b4; }
.category-food { background: #faecd8; color: #c97a25; }
.category-move { background: #e8f0e3; color: #6d835f; }
.category-other { background: #ebe7f8; color: #7b6cc4; }

.status-PENDING { background: #eef1e8; color: #6f835f; }
.status-IN_PROGRESS { background: #fff2de; color: #c77923; }
.status-PENDING_REVIEW { background: #ebe7f8; color: #7b6cc4; }
.status-COMPLETED { background: #e8f0e3; color: #5d794e; }
.status-DISPUTED { background: #fae7e3; color: #c85448; }
.status-CANCELLED,
.status-EXPIRED,
.status-CLOSED_BY_ADMIN { background: #efede7; color: #777a72; }

.title-row {
  justify-content: space-between;
  margin-top: 16px;
}

.title-row h1 {
  min-width: 0;
  margin: 0;
  overflow-wrap: anywhere;
  color: #191b17;
  font-size: clamp(26px, 3vw, 40px);
  font-weight: 950;
  line-height: 1.2;
}

.title-row strong {
  flex: 0 0 auto;
  color: #6f835f;
  font-size: clamp(26px, 2.4vw, 36px);
  font-weight: 950;
}

.task-description {
  max-width: 880px;
  margin: 16px 0 0;
  color: #5f635a;
  font-size: 15px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 22px;
}

.info-grid article {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 3px 8px;
  padding: 13px;
  border: 1px solid #eee9df;
  border-radius: 9px;
  background: #fffdfa;
}

.info-grid .app-icon {
  grid-row: span 2;
  margin-top: 3px;
  color: #6f835f;
}

.info-grid span {
  color: #85887f;
  font-size: 12px;
}

.info-grid strong {
  min-width: 0;
  overflow: hidden;
  color: #2c3029;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.hero-side {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  border-radius: 12px;
  background: linear-gradient(145deg, #eef1e8, #fffaf1);
  color: #64745a;
  text-align: center;
}

.hero-side span,
.hero-side small {
  color: #7e8178;
  font-size: 12px;
}

.hero-side strong {
  color: #6f835f;
  font-size: clamp(26px, 3vw, 38px);
  font-weight: 950;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 310px);
  gap: 18px;
  margin-top: 18px;
}

.main-column,
.side-column {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 16px;
}

.content-card,
.side-card {
  min-width: 0;
  padding: 20px;
}

.content-card header,
.side-card header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.content-card h2,
.side-card h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 950;
}

.content-card header span,
.content-card header button {
  border: 0;
  background: transparent;
  color: #7e8178;
  font-size: 12px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}

.image-grid img {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 9px;
  object-fit: cover;
}

.proof-card p {
  margin: 0 0 14px;
  color: #5f635a;
  line-height: 1.7;
}

.action-card header span {
  color: #6f835f;
  font-weight: 800;
}

.action-button,
.submit-rating {
  min-height: 40px;
  padding: 0 18px;
  border-radius: 7px;
  cursor: pointer;
  font-weight: 900;
}

.action-primary,
.submit-rating {
  border: 1px solid #6f835f;
  background: #6f835f;
  color: #fff;
}

.action-danger {
  border: 1px solid #d7b3ad;
  background: #fff7f5;
  color: #b8544a;
}

.action-secondary {
  border: 1px solid #d7cba9;
  background: #fff8e8;
  color: #b8781d;
}

.rating-card textarea {
  width: 100%;
  min-height: 92px;
  margin: 12px 0;
  padding: 12px;
  border: 1px solid #e5e0d6;
  border-radius: 8px;
  resize: vertical;
}

.stars {
  display: flex;
  gap: 8px;
}

.stars button {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1px solid #e5e0d6;
  border-radius: 8px;
  background: #fffefa;
  color: #c7c2b8;
  cursor: pointer;
}

.stars button.active {
  border-color: #f1bf65;
  background: #fff5df;
  color: #e39a22;
}

.form-error {
  margin: 0 0 10px;
  color: #b8544a;
  font-size: 13px;
}

.timeline-list {
  position: relative;
  display: grid;
  grid-auto-columns: minmax(180px, 1fr);
  grid-auto-flow: column;
  gap: 0;
  overflow-x: auto;
  padding: 6px 8px 4px 18px;
  scrollbar-width: thin;
}

.timeline-item {
  position: relative;
  display: grid;
  grid-template-rows: 28px auto;
  gap: 8px;
  min-width: 0;
  padding-right: 18px;
}

.timeline-item::before {
  content: "";
  position: absolute;
  top: 10px;
  left: 10px;
  right: -10px;
  height: 2px;
  background: #e4eadf;
}

.timeline-item:last-child::before {
  right: calc(100% - 10px);
}

.timeline-item i {
  position: relative;
  z-index: 1;
  width: 10px;
  height: 10px;
  margin-top: 6px;
  border-radius: 50%;
  background: #6f835f;
  box-shadow: 0 0 0 5px #eef1e8;
}

.timeline-item strong,
.timeline-item span,
.timeline-item p {
  display: block;
}

.timeline-item strong {
  min-width: 0;
  overflow: hidden;
  color: #2c3029;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.timeline-item span,
.timeline-item p {
  margin: 4px 0 0;
  color: #85887f;
  font-size: 12px;
  line-height: 1.5;
}

.timeline-item p {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.user-mini {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  font-weight: 950;
}

.avatar-requester { background: #6f835f; }
.avatar-helper { background: #c77923; }

.user-mini div {
  min-width: 0;
}

.user-mini strong,
.user-mini small {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-mini small {
  margin-top: 3px;
  color: #df8a2f;
  font-size: 12px;
}

.empty-line {
  margin: 0;
  padding: 18px 0;
  color: #90938b;
  text-align: center;
  font-size: 13px;
}

@media (max-width: 980px) {
  .detail-hero,
  .detail-layout {
    grid-template-columns: 1fr;
  }

  .hero-side {
    min-height: 120px;
  }
}

@media (max-width: 720px) {
  .info-grid {
    grid-template-columns: 1fr;
  }

  .title-row {
    align-items: flex-start;
  }
}
</style>
