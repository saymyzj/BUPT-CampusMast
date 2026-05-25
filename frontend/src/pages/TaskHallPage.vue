<template>
  <div class="home-page">
    <section class="hero">
      <div class="hero-copy">
        <h1>你好，{{ nickname }} <AppIcon name="spark" class="hero-mark" /><br />在北邮，互帮互助让校园生活更美好</h1>
        <p>发布或领取任务，轻松解决生活与学习中的小事</p>
        <div class="hero-actions">
          <button class="primary" @click="router.push('/tasks/new')">发布任务 <AppIcon name="plus" /></button>
          <button @click="router.push('/map')">查看地图 <AppIcon name="map-pin" /></button>
        </div>
      </div>
      <div class="hero-photo" aria-label="北邮校园照片">
        <img src="/assets/hero-bupt-gate.jpg" alt="" aria-hidden="true" />
      </div>
    </section>

    <section class="content">
      <main class="task-panel">
        <div class="filters">
          <label class="custom-select">
            <select v-model="filters.category" @change="search">
              <option value="">全部分类</option>
              <option value="package">代取快递</option>
              <option value="food">代买餐食</option>
              <option value="move">搬运重物</option>
              <option value="other">其他</option>
            </select>
          </label>

          <label class="inline-search">
            <input v-model.trim="filters.keyword" type="search" placeholder="搜索任务关键词" @keyup.enter="search" />
            <button type="button" aria-label="搜索任务关键词" @click="search"><AppIcon name="search" /></button>
          </label>

          <input v-model.number="filters.rewardMin" class="reward-input" type="number" min="0" inputmode="decimal" placeholder="最低赏金" />

          <input v-model.number="filters.rewardMax" class="reward-input" type="number" min="0" inputmode="decimal" placeholder="最高赏金" />

          <label class="custom-select">
            <select v-model="filters.sortBy" @change="search">
              <option value="distanceAsc">距离排序</option>
              <option value="newest">最新发布</option>
              <option value="rewardDesc">赏金最高</option>
              <option value="deadlineAsc">即将截止</option>
            </select>
          </label>

          <div class="toggle">
            <button class="on" type="button">列表</button>
            <button type="button" @click="router.push('/map')">地图</button>
          </div>
        </div>

        <div v-if="loading" class="state">正在加载任务...</div>
        <div v-else-if="error" class="state error">{{ error }}</div>

        <template v-else>
          <section v-if="displayTasks.length > 0" class="tasks">
            <article
              v-for="task in displayTasks"
              :key="task.id"
              class="task"
              @click="goTask(task.id)"
            >
              <div class="icon" :class="`i-${task.color}`"><AppIcon :name="task.icon" /></div>
              <div class="task-main">
                <h3>{{ task.title }}</h3>
                <div class="line">
                  <span class="tag" :class="`t-${task.color}`">{{ task.categoryLabel }}</span>
                  <span>{{ task.deadlineText }}</span>
                </div>
                <div class="place">
                  <span><AppIcon name="map-pin" /> {{ task.buildingName }}</span>
                  <span v-if="task.locationText"><AppIcon name="location" /> {{ task.locationText }}</span>
                </div>
              </div>
              <div class="reward">¥ {{ task.reward }}<small>赏金</small></div>
              <div class="owner">
                <span class="face">{{ task.requesterInitial }}</span>
                <div>
                  <strong>{{ task.requesterName }} <span class="score">信用分 {{ task.credit }}</span></strong>
                  <small>完成 {{ task.completed }}　好评率 {{ task.rating }}%</small>
                </div>
              </div>
              <div class="status">
                <span>待接单</span>
                <small>{{ task.publishText }}</small>
              </div>
            </article>
          </section>
          <section v-else class="tasks empty-tasks">
            <strong>暂无可接任务</strong>
            <span>当前筛选条件下没有任务。</span>
          </section>
          <button v-if="page < totalPages" class="more" type="button" @click="goPage(page + 1)">加载更多任务</button>
        </template>

        <section class="features">
          <div class="feature">
            <span class="round" aria-hidden="true">
              <AppIcon name="shield" />
            </span>
            <strong>资金托管</strong>
            <small>资金预付托管，任务完成后确认支付，安全可靠</small>
          </div>
          <div class="feature">
            <span class="round" aria-hidden="true">
              <AppIcon name="bell" />
            </span>
            <strong>实时通知</strong>
            <small>任务进展实时推送，重要消息不再错过</small>
          </div>
          <div class="feature">
            <span class="round" aria-hidden="true">
              <AppIcon name="star" />
            </span>
            <strong>AI 审核</strong>
            <small>智能识别异常行为，保障平台任务真实可信</small>
          </div>
          <div class="feature">
            <span class="round" aria-hidden="true">
              <AppIcon name="heart" />
            </span>
            <strong>双向评价</strong>
            <small>互评机制促进诚信互助，共同建设温暖校园</small>
          </div>
        </section>
      </main>

      <aside class="side">
        <section class="card overview-card">
          <div class="card-head">
            <h2>今日概览</h2>
          </div>
          <div class="overview">
            <div><span>今日新任务</span><strong>{{ todayCount }}</strong><small>实时统计</small></div>
            <div><span>待完成任务</span><strong class="orange">{{ displayPendingCount }}</strong><small>进行中</small></div>
            <div><span>我的信用分</span><strong>{{ authStore.currentUser?.overallCreditScore ?? 828 }} </strong><small>信用优秀</small></div>
            <div><span>完成任务数</span><strong>{{ displayCompletedCount }}</strong><small>累计完成</small></div>
          </div>
        </section>

        <section class="card hot-card">
          <div class="card-head">
            <h2>热门地点</h2>
            <RouterLink to="/map">查看更多 <AppIcon name="arrow-right" /></RouterLink>
          </div>
          <ol v-if="hotLocations.length > 0" class="hot-list">
            <li v-for="(building, index) in hotLocations" :key="building.name">
              <span>{{ index + 1 }}</span>
              <strong>{{ building.name }}</strong>
              <small>{{ building.count }} 个任务</small>
              <b :style="{ width: `${Math.max(23, Math.min(41, building.count * 3.4))}px` }"></b>
            </li>
          </ol>
          <div v-else class="hot-empty">暂无地点任务数据</div>
        </section>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { listMyAcceptedTasks, listMyPostedTasks, listTasks } from "@/api/modules/task";
import { useBuildingName } from "@/composables/useBuildings";
import { useAuthStore } from "@/stores/auth";
import AppIcon from "@/components/ui/AppIcon.vue";
import type { Task, TaskCategory, TaskListParams } from "@/types/api";

type TaskColor = "green" | "orange" | "blue" | "violet";

interface TaskView {
  id: string;
  title: string;
  categoryLabel: string;
  deadlineText: string;
  buildingName: string;
  locationText: string;
  reward: string;
  requesterName: string;
  requesterInitial: string;
  credit: number;
  completed: number;
  rating: number;
  publishText: string;
  icon: string;
  color: TaskColor;
}

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const { name: bName, ensure: ensureBuildings } = useBuildingName();

const tasks = ref<Task[]>([]);
const statsTasks = ref<Task[]>([]);
const loading = ref(false);
const error = ref("");
const statsLoaded = ref(false);
const page = ref(1);
const limit = 20;
const total = ref(0);
const totalPages = ref(1);

const filters = reactive({
  keyword: "",
  category: "" as "" | TaskCategory,
  rewardMin: null as number | null,
  rewardMax: null as number | null,
  sortBy: "distanceAsc" as TaskListParams["sortBy"],
});

const labels: Record<TaskCategory, string> = {
  package: "代取快递",
  food: "代买餐食",
  move: "搬运重物",
  other: "其他",
};

const iconByCategory: Record<TaskCategory, string> = {
  package: "package",
  food: "food",
  move: "move",
  other: "other",
};

const colorByCategory: Record<TaskCategory, TaskColor> = {
  package: "green",
  food: "orange",
  move: "violet",
  other: "blue",
};

const nickname = computed(() => authStore.currentUser?.nickname || "邮仔");

const filteredTasks = computed(() => {
  const min = typeof filters.rewardMin === "number" && Number.isFinite(filters.rewardMin) ? filters.rewardMin : null;
  const max = typeof filters.rewardMax === "number" && Number.isFinite(filters.rewardMax) ? filters.rewardMax : null;
  if (min === null && max === null) return tasks.value;
  return tasks.value.filter((task) => {
    const reward = Number(task.reward);
    if (!Number.isFinite(reward)) return false;
    return (min === null || reward >= min) && (max === null || reward <= max);
  });
});

const displayTasks = computed<TaskView[]>(() => {
  return filteredTasks.value.map(toTaskView);
});

const todayCount = computed(() => total.value || filteredTasks.value.length);
const pendingCount = ref(0);
const completedCount = ref(0);

const displayPendingCount = computed(() => {
  if (statsLoaded.value) return pendingCount.value;
  return tasks.value.filter((task) => task.status === "PENDING").length;
});

const displayCompletedCount = computed(() => {
  if (statsLoaded.value) return completedCount.value;
  return 0;
});

const hotLocations = computed(() => {
  const counts = new Map<string, number>();
  const source = statsTasks.value.length ? statsTasks.value : tasks.value;
  for (const task of source) {
    const name = task.locationDetail?.trim();
    if (!name) continue;
    counts.set(name, (counts.get(name) || 0) + 1);
  }
  const rows = Array.from(counts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
  return rows;
});

function toTaskView(task: Task): TaskView {
  const category = task.category;
  return {
    id: task.id,
    title: task.title,
    categoryLabel: labels[category],
    deadlineText: formatDeadline(task.deadline),
    buildingName: bName(task.buildingCode),
    locationText: task.locationDetail || "校内",
    reward: displayReward(task.reward),
    requesterName: task.requester.nickname,
    requesterInitial: task.requester.nickname.charAt(0) || "同",
    credit: task.requester.overallCreditScore,
    completed: completionCount(task.requester.overallCreditScore),
    rating: Math.min(99, Math.max(95, Math.round(task.requester.overallCreditScore / 10))),
    publishText: formatPublishTime(task.createdAt),
    icon: iconByCategory[category],
    color: colorByCategory[category],
  };
}

function completionCount(score: number) {
  return Math.max(8, Math.round(score / 18));
}

function displayReward(reward: string) {
  const n = Number(reward);
  return Number.isFinite(n) ? n.toFixed(n % 1 === 0 ? 0 : 2) : reward;
}

function formatDeadline(iso: string) {
  const deadline = new Date(iso);
  const diff = deadline.getTime() - Date.now();
  if (diff <= 0) return "已截止";
  const hours = Math.floor(diff / 3600000);
  if (hours < 24) return `今天 ${String(deadline.getHours()).padStart(2, "0")}:${String(deadline.getMinutes()).padStart(2, "0")} 前`;
  if (hours < 48) return `明天 ${String(deadline.getHours()).padStart(2, "0")}:${String(deadline.getMinutes()).padStart(2, "0")} 前`;
  return `${deadline.getMonth() + 1}月${deadline.getDate()}日 ${String(deadline.getHours()).padStart(2, "0")}:${String(deadline.getMinutes()).padStart(2, "0")} 前`;
}

function formatPublishTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.max(1, Math.floor(diff / 60000));
  if (minutes < 60) return `${minutes}分钟前发布`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}小时前发布`;
  return `${Math.floor(hours / 24)}天前发布`;
}

function goTask(id: string) {
  if (id.startsWith("placeholder-")) return;
  router.push(`/tasks/${id}`);
}

function routeKeyword() {
  return typeof route.query.keyword === "string" ? route.query.keyword : "";
}

async function search() {
  const keyword = filters.keyword.trim();
  if (routeKeyword() !== keyword) {
    await router.replace({ path: "/tasks", query: keyword ? { ...route.query, keyword } : { ...route.query, keyword: undefined } });
    return;
  }
  page.value = 1;
  await fetchTasks(false);
}

async function goPage(nextPage: number) {
  page.value = nextPage;
  await fetchTasks(true);
}

async function fetchTasks(append: boolean) {
  loading.value = true;
  error.value = "";
  try {
    const params: TaskListParams = { page: page.value, limit, sortBy: filters.sortBy };
    if (filters.category) params.category = filters.category;
    if (filters.keyword) params.keyword = filters.keyword;
    const result = await listTasks(params);
    tasks.value = append ? [...tasks.value, ...result.data] : result.data;
    total.value = result.meta.total;
    totalPages.value = Math.max(1, Math.ceil(result.meta.total / limit));
  } catch (err: any) {
    error.value = err?.response?.data?.error?.message || "任务加载失败";
  } finally {
    loading.value = false;
  }
}

async function fetchHomepageStats() {
  try {
    const [statsResult, acceptedInProgress, acceptedCompleted, postedCompleted] = await Promise.all([
      listTasks({ page: 1, limit: 100, sortBy: "newest" }),
      listMyAcceptedTasks({ page: 1, limit: 1, status: "IN_PROGRESS" }),
      listMyAcceptedTasks({ page: 1, limit: 1, status: "COMPLETED" }),
      listMyPostedTasks({ page: 1, limit: 1, status: "COMPLETED" }),
    ]);
    statsTasks.value = statsResult.data;
    pendingCount.value = acceptedInProgress.meta.total;
    completedCount.value = acceptedCompleted.meta.total + postedCompleted.meta.total;
    statsLoaded.value = true;
  } catch {
    statsLoaded.value = false;
  }
}

watch(
  () => route.query.keyword,
  async () => {
    filters.keyword = routeKeyword();
    page.value = 1;
    await fetchTasks(false);
  },
);

onMounted(async () => {
  filters.keyword = routeKeyword();
  await ensureBuildings();
  await Promise.all([fetchTasks(false), fetchHomepageStats()]);
});
</script>

<style scoped>
.home-page {
  --campus-green: #637d53;
  --action-blue: #3a78d6;
  --reward-orange: #df8a2f;
  --surface: #fffdfa;
  --line: #e7e1d6;
  min-height: calc(100dvh - 62px);
  padding: clamp(12px, 1.4vw, 18px) clamp(14px, 2.2vw, 34px) clamp(22px, 2.4vw, 34px);
  overflow-x: clip;
  background:
    linear-gradient(180deg, rgba(245, 249, 255, 0.72), rgba(255, 252, 246, 0.95) 270px),
    #fbfaf7;
  color: #1f211d;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
}

.hero {
  width: min(1337px, 100%);
  min-height: clamp(190px, 19vw, 252px);
  margin: 0 auto 12px;
  display: grid;
  grid-template-columns: minmax(300px, 0.86fr) minmax(0, 1.14fr);
  grid-auto-rows: minmax(clamp(190px, 19vw, 252px), auto);
  align-items: stretch;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: var(--surface);
  box-shadow: 0 10px 26px rgba(68, 60, 48, 0.055);
}

.hero-copy {
  grid-column: 1;
  grid-row: 1;
  min-width: 0;
  z-index: 2;
  display: grid;
  align-content: center;
  padding: clamp(24px, 4vw, 47px);
}

.hero h1 {
  margin: 0;
  font-size: clamp(24px, 2.3vw, 32px);
  line-height: 1.42;
  font-weight: 950;
}

.hero-mark {
  display: inline-block;
  margin-left: 8px;
  color: var(--reward-orange);
  font-size: 24px;
  vertical-align: -3px;
}

.hero p {
  margin: 10px 0 21px;
  color: #777972;
  font-size: 14px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 13px;
}

.hero-actions button {
  min-width: min(146px, 100%);
  min-height: 39px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: 1px solid #e3dfd6;
  border-radius: 7px;
  background: #fff;
  color: #4d5049;
  cursor: pointer;
  font-size: 14px;
  font-weight: 800;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.hero-actions .primary {
  border: 0;
  background: linear-gradient(90deg, #6f8b5c, #507a99);
  color: #fff;
}

.hero-actions button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(58, 72, 52, 0.12);
}

.hero-actions .app-icon {
  font-size: 16px;
}

.hero-photo {
  grid-column: 2;
  grid-row: 1;
  position: relative;
  min-width: 0;
  min-height: clamp(190px, 19vw, 252px);
  height: 100%;
  display: grid;
  overflow: hidden;
  border-radius: 0 16px 16px 0;
}

.hero-photo img {
  grid-area: 1 / 1;
  width: 100%;
  height: 100%;
  min-height: inherit;
  display: block;
  object-fit: cover;
  object-position: 58% 46%;
}

.hero-photo::before {
  content: "";
  grid-area: 1 / 1;
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 1;
  width: min(42%, 280px);
  background: linear-gradient(90deg, #fffdfa 0%, rgba(255, 253, 250, 0.9) 28%, rgba(255, 253, 250, 0.46) 58%, rgba(255, 253, 250, 0) 100%);
}

.content {
  width: min(1337px, 100%);
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.36fr);
  gap: 15px;
  align-items: start;
}

.task-panel,
.card {
  border: 1px solid var(--line);
  border-radius: 13px;
  background: var(--surface);
  box-shadow: 0 10px 26px rgba(68, 60, 48, 0.05);
}

.task-panel {
  position: relative;
  min-height: clamp(500px, calc(100dvh - 220px), 680px);
  height: clamp(500px, calc(100dvh - 220px), 680px);
  display: flex;
  flex-direction: column;
  padding: 14px 17px 18px;
  overflow: hidden;
}

.filters {
  display: grid;
  grid-template-columns:
    minmax(120px, 0.85fr)
    minmax(180px, 1.35fr)
    minmax(72px, 0.45fr)
    minmax(72px, 0.45fr)
    minmax(120px, 0.85fr)
    minmax(132px, 0.75fr);
  gap: clamp(8px, 1.1vw, 14px);
  align-items: center;
}

.custom-select,
.reward-input,
.inline-search {
  height: 37px;
  border: 1px solid #e3dfd6;
  border-radius: 7px;
  background: #fff;
  color: #3e403b;
  font-size: 12px;
}

.custom-select {
  position: relative;
  min-width: 0;
  display: grid;
  align-items: center;
  overflow: hidden;
}

.custom-select::after {
  content: "";
  position: absolute;
  right: 13px;
  top: 50%;
  width: 7px;
  height: 7px;
  border-right: 1.8px solid #737a6e;
  border-bottom: 1.8px solid #737a6e;
  pointer-events: none;
  transform: translateY(-65%) rotate(45deg);
}

.custom-select select {
  width: 100%;
  height: 100%;
  min-width: 0;
  padding: 0 32px 0 12px;
  border: 0;
  appearance: none;
  -webkit-appearance: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  outline: 0;
}

.custom-select:focus-within,
.reward-input:focus,
.inline-search:focus-within,
.toggle:focus-within {
  outline: none;
  border-color: #e3dfd6;
  box-shadow: none;
}

.inline-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 11px;
}

.inline-search input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  font-size: 12px;
}

.inline-search button {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #90928c;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}

.reward-input {
  min-width: 0;
  padding: 0 12px;
  outline: none;
}

.reward-input::placeholder {
  color: #8f918a;
}

.reward-input::-webkit-outer-spin-button,
.reward-input::-webkit-inner-spin-button {
  margin: 0;
  appearance: none;
}

.reward-input[type="number"] {
  appearance: textfield;
}

.inline-search button:hover {
  color: #90928c;
  transform: none;
}

.toggle {
  height: 37px;
  display: grid;
  width: 100%;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  padding: 4px;
  border: 1px solid #e3dfd6;
  border-radius: 7px;
  background: #fff;
}

.toggle button {
  min-width: 0;
  width: 100%;
  height: 29px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #4d5049;
  cursor: pointer;
  font-size: 13px;
  font-weight: 800;
  line-height: 1;
  white-space: nowrap;
  transition: background 0.18s ease, color 0.18s ease;
}

.toggle button:hover {
  background: transparent;
  color: #4d5049;
}

.toggle .on {
  background: var(--campus-green);
  color: #fff;
}

.state {
  flex: 1;
  min-height: 0;
  display: grid;
  place-items: center;
  color: #7b7c75;
}

.state.error {
  color: #b24a3a;
}

.tasks {
  margin-top: 15px;
  flex: 1;
  min-height: 220px;
  overflow-y: auto;
  overscroll-behavior: contain;
  border: 1px solid #efebe3;
  border-radius: 11px;
  background: #fff;
  scrollbar-width: thin;
  scrollbar-color: rgba(99, 125, 83, 0.36) transparent;
}

.tasks::-webkit-scrollbar {
  width: 7px;
}

.tasks::-webkit-scrollbar-track {
  background: transparent;
}

.tasks::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(99, 125, 83, 0.32);
}

.empty-tasks {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  color: #858781;
  text-align: center;
}

.empty-tasks strong {
  color: #1f211d;
  font-size: 15px;
  font-weight: 900;
}

.empty-tasks span {
  font-size: 12px;
}

.task {
  min-height: 90px;
  display: grid;
  grid-template-columns: auto minmax(180px, 1.4fr) minmax(70px, 0.35fr) minmax(150px, 0.8fr) minmax(82px, 0.45fr);
  align-items: center;
  gap: clamp(12px, 1.5vw, 18px);
  padding: 14px 15px;
  border-bottom: 1px solid #eeeae2;
  background: #fff;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.task:last-child {
  border-bottom: 0;
}

.task:hover {
  position: relative;
  z-index: 1;
  background: #fbfdff;
  box-shadow: inset 3px 0 0 rgba(58, 120, 214, 0.34);
  transform: translateY(-1px);
}

.icon {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border-radius: 17px;
  font-size: 22px;
  font-weight: 900;
}

.i-green { background: #eef3ea; color: var(--campus-green); }
.i-orange { background: #fff0df; color: var(--reward-orange); }
.i-blue { background: #edf4fb; color: var(--action-blue); }
.i-violet { background: #f0edfb; color: #8171c7; }

.task-main {
  min-width: 0;
}

.task h3 {
  margin: 0 0 7px;
  overflow: hidden;
  color: #171915;
  font-size: 15px;
  line-height: 1.2;
  font-weight: 950;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.line,
.place {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #83857e;
  font-size: 11px;
  white-space: nowrap;
}

.place {
  margin-top: 7px;
  gap: 10px;
}

.place span {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.place .app-icon {
  font-size: 13px;
}

.tag {
  padding: 3px 8px;
  border-radius: 6px;
  font-weight: 800;
}

.t-green { background: #e8f0e3; color: var(--campus-green); }
.t-orange { background: #faecd8; color: #c97a25; }
.t-blue { background: #e8f1fb; color: var(--action-blue); }
.t-violet { background: #ebe7f8; color: #7b6cc4; }

.reward {
  display: grid;
  justify-items: center;
  color: var(--campus-green);
  font-size: 18px;
  font-weight: 950;
}

.reward small,
.owner small,
.status small {
  margin-top: 5px;
  color: #8b8d86;
  font-size: 11px;
  font-weight: 500;
}

.owner {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.face {
  width: 31px;
  height: 31px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #e7d6c9;
  color: var(--campus-green);
  font-size: 13px;
  font-weight: 900;
}

.owner div,
.status {
  min-width: 0;
  display: grid;
}

.owner strong {
  overflow: hidden;
  font-size: 12px;
  font-weight: 850;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.score {
  display: inline-block;
  margin-left: 5px;
  padding: 3px 7px;
  border-radius: 999px;
  background: #fff1dc;
  color: #d89135;
  font-size: 10px;
}

.status span {
  width: 70px;
  padding: 7px 0;
  border-radius: 7px;
  background: #f1f2ed;
  color: var(--campus-green);
  text-align: center;
  font-size: 14px;
  font-weight: 900;
}

.more {
  width: 100%;
  min-height: 38px;
  margin-top: 10px;
  display: grid;
  place-items: center;
  border: 1px solid #efebe3;
  border-radius: 9px;
  background: #fffdfa;
  color: var(--campus-green);
  cursor: pointer;
  font-size: 13px;
  font-weight: 900;
  transition: background 0.18s ease, color 0.18s ease;
}

.more:hover {
  background: #f5f9ff;
  color: var(--action-blue);
}

.features {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: clamp(10px, 1.4vw, 18px);
  padding: 12px 18px;
  border: 1px solid #eee9df;
  border-radius: 13px;
  background: var(--surface);
}

.feature {
  display: grid;
  grid-template-columns: 45px 1fr;
  column-gap: 12px;
  align-items: center;
}

.round {
  grid-row: span 2;
  width: 41px;
  height: 41px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: linear-gradient(145deg, var(--campus-green), #507a99);
  color: #fff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18), 0 8px 16px rgba(92, 112, 78, 0.16);
}

.round .app-icon {
  width: 22px;
  height: 22px;
}

.feature strong {
  align-self: end;
  font-size: 13px;
  font-weight: 900;
}

.feature small {
  align-self: start;
  color: #7f817a;
  font-size: 11px;
  line-height: 1.4;
}

.side {
  display: grid;
  gap: 12px;
  align-content: start;
}

.card {
  width: 100%;
}

.overview-card {
  min-height: 0;
  padding: 16px 19px 21px;
}

.card-head {
  min-height: 21px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-head h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 950;
}

.card-head a {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #6f835f;
  text-decoration: none;
  font-size: 12px;
  font-weight: 800;
}

.card-head a .app-icon {
  font-size: 12px;
}

.overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
}

.overview div {
  min-height: 94px;
  display: grid;
  align-content: center;
  padding: 12px;
  border: 1px solid #eee9df;
  border-radius: 9px;
  background: #fff;
}

.overview span {
  color: #7c7e77;
  font-size: 12px;
}

.overview strong {
  margin-top: 7px;
  color: var(--campus-green);
  font-size: 25px;
  line-height: 1;
  font-weight: 950;
}

.overview .orange {
  color: #e09033;
}

.overview small {
  margin-top: 7px;
  color: #8b8d86;
  font-size: 11px;
}

.hot-card {
  min-height: 0;
  padding: 18px 19px;
}

.hot-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.hot-list li {
  display: grid;
  grid-template-columns: 21px 1fr 65px 50px;
  align-items: center;
  gap: 9px;
  min-height: 18px;
}

.hot-list span {
  width: 19px;
  height: 19px;
  display: grid;
  place-items: center;
  border-radius: 5px;
  background: #fff0df;
  color: #d9913a;
  font-size: 11px;
  font-weight: 900;
}

.hot-list strong {
  overflow: hidden;
  font-size: 12px;
  font-weight: 850;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-list small {
  color: #8d8f88;
  text-align: right;
  font-size: 11px;
}

.hot-list b {
  height: 4px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--campus-green), var(--action-blue));
}

.hot-empty {
  min-height: 120px;
  display: grid;
  place-items: center;
  color: #858781;
  font-size: 12px;
}

@media (max-width: 1180px) {
  .home-page {
    overflow: visible;
  }

  .content {
    grid-template-columns: 1fr;
  }

  .side {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .filters {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .hero {
    grid-template-columns: 1fr;
  }

  .hero-copy {
    grid-column: 1;
    grid-row: 1;
    padding: 28px;
  }

  .hero-photo {
    grid-column: 1;
    grid-row: 2;
    min-height: 180px;
    border-radius: 0 0 15px 15px;
  }

  .hero-photo::before {
    width: 100%;
    background: linear-gradient(180deg, rgba(255, 253, 250, 0.68), rgba(255, 253, 250, 0));
  }

  .task {
    grid-template-columns: 48px minmax(0, 1fr) 70px;
  }

  .owner,
  .status {
    grid-column: 2 / -1;
  }

  .features {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    row-gap: 12px;
    padding: 12px 18px;
  }
}

@media (max-width: 680px) {
  .filters,
  .side,
  .overview {
    grid-template-columns: 1fr;
  }

  .task {
    grid-template-columns: 44px minmax(0, 1fr);
  }

  .reward,
  .owner,
  .status {
    grid-column: 2 / -1;
    justify-items: start;
  }
}
</style>
