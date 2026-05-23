<template>
  <div class="home-page">
    <section class="hero">
      <div class="hero-copy">
        <h1>你好，{{ nickname }} <span>👋</span><br />在北邮，互帮互助让校园生活更美好</h1>
        <p>发布或领取任务，轻松解决生活与学习中的小事</p>
        <div class="hero-actions">
          <button class="primary" @click="router.push('/tasks/new')">发布任务 <b>＋</b></button>
          <button @click="router.push('/map')">查看地图 <b>⌖</b></button>
        </div>
      </div>
      <div class="hero-photo" aria-label="北邮校园照片"></div>
    </section>

    <section class="content">
      <main class="task-panel">
        <div class="filters">
          <select v-model="filters.category" @change="search">
            <option value="">全部分类</option>
            <option value="package">代取快递</option>
            <option value="food">代买餐食</option>
            <option value="move">搬运重物</option>
            <option value="other">其他</option>
          </select>

          <label class="inline-search">
            <input v-model.trim="filters.keyword" type="search" placeholder="搜索任务关键词" @keyup.enter="search" />
            <button type="button" aria-label="搜索任务关键词" @click="search">⌕</button>
          </label>

          <select v-model="filters.rewardRange">
            <option value="">赏金范围</option>
            <option value="0-10">¥0 - ¥10</option>
            <option value="10-30">¥10 - ¥30</option>
            <option value="30-9999">¥30 以上</option>
          </select>

          <select v-model="filters.building" @change="search">
            <option value="">全部楼宇</option>
            <option v-for="building in buildingOptions" :key="building.code" :value="building.code">
              {{ building.name }}
            </option>
          </select>

          <select v-model="filters.sortBy" @change="search">
            <option value="distanceAsc">距离排序</option>
            <option value="newest">最新发布</option>
            <option value="rewardDesc">赏金最高</option>
            <option value="deadlineAsc">即将截止</option>
          </select>

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
              <div class="icon" :class="`i-${task.color}`">{{ task.icon }}</div>
              <div class="task-main">
                <h3>{{ task.title }}</h3>
                <div class="line">
                  <span class="tag" :class="`t-${task.color}`">{{ task.categoryLabel }}</span>
                  <span>{{ task.deadlineText }}</span>
                </div>
                <div class="place">
                  <span>⌖ {{ task.buildingName }}</span>
                  <span v-if="task.locationText">⌁ {{ task.locationText }}</span>
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
          <div v-else class="more">暂无更多任务</div>
        </template>

        <section class="features">
          <div class="feature">
            <span class="round" aria-hidden="true">
              <svg viewBox="0 0 24 24" role="img">
                <path d="M12 3.5 18.5 6v5.2c0 4.1-2.6 7.8-6.5 9.3-3.9-1.5-6.5-5.2-6.5-9.3V6L12 3.5Z" />
                <path d="m9.2 12 1.8 1.8 3.9-4.1" />
              </svg>
            </span>
            <strong>资金托管</strong>
            <small>资金预付托管，任务完成后确认支付，安全可靠</small>
          </div>
          <div class="feature">
            <span class="round" aria-hidden="true">
              <svg viewBox="0 0 24 24" role="img">
                <path d="M18 10.8c0-3.3-2.1-5.8-5.1-6.4V3a.9.9 0 0 0-1.8 0v1.4C8.1 5 6 7.5 6 10.8v3.4l-1.5 2.4h15l-1.5-2.4v-3.4Z" />
                <path d="M9.7 18.4a2.4 2.4 0 0 0 4.6 0" />
              </svg>
            </span>
            <strong>实时通知</strong>
            <small>任务进展实时推送，重要消息不再错过</small>
          </div>
          <div class="feature">
            <span class="round" aria-hidden="true">
              <svg viewBox="0 0 24 24" role="img">
                <path d="m12 4.2 2.2 4.5 5 .7-3.6 3.5.8 5-4.4-2.4-4.4 2.4.8-5-3.6-3.5 5-.7L12 4.2Z" />
              </svg>
            </span>
            <strong>AI 审核</strong>
            <small>智能识别异常行为，保障平台任务真实可信</small>
          </div>
          <div class="feature">
            <span class="round" aria-hidden="true">
              <svg viewBox="0 0 24 24" role="img">
                <path d="M12 19.2s-6.7-4-7.9-8.3C3.4 8.2 5 6 7.5 6c1.5 0 2.8.8 3.5 2 .7-1.2 2-2 3.5-2C17 6 18.6 8.2 17.9 10.9 16.7 15.2 12 19.2 12 19.2Z" />
              </svg>
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
            <h2>热门楼宇</h2>
            <RouterLink to="/map">查看更多 ›</RouterLink>
          </div>
          <ol v-if="hotBuildings.length > 0" class="hot-list">
            <li v-for="(building, index) in hotBuildings" :key="building.name">
              <span>{{ index + 1 }}</span>
              <strong>{{ building.name }}</strong>
              <small>{{ building.count }} 个任务</small>
              <b :style="{ width: `${Math.max(23, Math.min(41, building.count * 3.4))}px` }"></b>
            </li>
          </ol>
          <div v-else class="hot-empty">暂无楼宇任务数据</div>
        </section>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { listMyAcceptedTasks, listMyPostedTasks, listTasks } from "@/api/modules/task";
import { listCampusBuildings } from "@/api/modules/map";
import { useBuildingName } from "@/composables/useBuildings";
import { useAuthStore } from "@/stores/auth";
import type { CampusBuilding, Task, TaskCategory, TaskListParams } from "@/types/api";

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
const buildings = ref<CampusBuilding[]>([]);
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
  building: "",
  rewardRange: "",
  sortBy: "distanceAsc" as TaskListParams["sortBy"],
});

const labels: Record<TaskCategory, string> = {
  package: "代取快递",
  food: "代买餐食",
  move: "搬运重物",
  other: "其他",
};

const iconByCategory: Record<TaskCategory, string> = {
  package: "▣",
  food: "▤",
  move: "⇄",
  other: "✦",
};

const colorByCategory: Record<TaskCategory, TaskColor> = {
  package: "green",
  food: "orange",
  move: "violet",
  other: "blue",
};

const nickname = computed(() => authStore.currentUser?.nickname || "邮仔");
const buildingOptions = computed(() => buildings.value.map((building) => ({ code: building.code, name: building.name })));

const filteredTasks = computed(() => {
  if (!filters.rewardRange) return tasks.value;
  const [min, max] = filters.rewardRange.split("-").map(Number);
  return tasks.value.filter((task) => {
    const reward = Number(task.reward);
    return reward >= min && reward <= max;
  });
});

const displayTasks = computed<TaskView[]>(() => {
  return filteredTasks.value.slice(0, 3).map(toTaskView);
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

const hotBuildings = computed(() => {
  const counts = new Map<string, number>();
  const source = statsTasks.value.length ? statsTasks.value : tasks.value;
  for (const task of source) counts.set(task.buildingCode, (counts.get(task.buildingCode) || 0) + 1);
  const rows = Array.from(counts.entries())
    .map(([code, count]) => ({ name: bName(code), count }))
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
    if (filters.building) params.buildingCode = filters.building;
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
  try {
    buildings.value = await listCampusBuildings();
  } catch {
    buildings.value = [];
  }
  await Promise.all([fetchTasks(false), fetchHomepageStats()]);
});
</script>

<style scoped>
.home-page {
  min-height: calc(100vh - 86px);
  padding-bottom: 16px;
  overflow: hidden;
  background: #fbfaf7;
  color: #1f211d;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
}

.hero {
  position: relative;
  width: min(1337px, calc(100vw - 34px));
  height: 223px;
  margin: 0 auto 12px;
  overflow: hidden;
  border: 1px solid #e7e4dc;
  border-radius: 16px;
  background: #fffdfa;
  box-shadow: 0 10px 26px rgba(68, 60, 48, 0.055);
}

.hero-copy {
  position: absolute;
  left: 47px;
  top: 33px;
  z-index: 3;
}

.hero h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.42;
  font-weight: 950;
}

.hero p {
  margin: 10px 0 21px;
  color: #777972;
  font-size: 14px;
}

.hero-actions {
  display: flex;
  gap: 13px;
}

.hero-actions button {
  width: 146px;
  height: 39px;
  border: 1px solid #e3dfd6;
  border-radius: 7px;
  background: #fff;
  color: #4d5049;
  cursor: pointer;
  font-size: 14px;
  font-weight: 800;
}

.hero-actions .primary {
  border: 0;
  background: linear-gradient(90deg, #708760, #5f754f);
  color: #fff;
}

.hero-actions b {
  margin-left: 15px;
  font-size: 16px;
}

.hero-photo {
  position: absolute;
  left: 492px;
  top: 16px;
  width: 643px;
  height: 192px;
  overflow: hidden;
  border-radius: 15px;
  background-image: url("/assets/home-reference.png");
  background-repeat: no-repeat;
  background-size: 1440px 802px;
  background-position: -209px -101px;
}

.hero-photo::before {
  content: "";
  position: absolute;
  left: -2px;
  top: 0;
  bottom: 0;
  width: 210px;
  background: linear-gradient(90deg, #fffdfa 0%, rgba(255, 253, 250, 0.82) 18%, rgba(255, 253, 250, 0) 100%);
}

.hero::after {
  content: "";
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 258px;
  background: linear-gradient(90deg, rgba(255, 253, 250, 0), #fffdfa 72%);
  z-index: 2;
}

.content {
  width: min(1337px, calc(100vw - 34px));
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 966px) 357px;
  gap: 15px;
}

.task-panel,
.card {
  border: 1px solid #e8e4dc;
  border-radius: 13px;
  background: #fffdfa;
  box-shadow: 0 10px 26px rgba(68, 60, 48, 0.05);
}

.task-panel {
  position: relative;
  height: 470px;
  padding: 14px 17px 0;
}

.filters {
  height: 38px;
  display: grid;
  grid-template-columns: 132px 171px 116px 116px 116px 210px;
  gap: 14px;
  align-items: center;
}

.filters select,
.inline-search {
  height: 37px;
  border: 1px solid #e3dfd6;
  border-radius: 7px;
  background: #fff;
  color: #3e403b;
  font-size: 12px;
}

.filters select {
  min-width: 0;
  padding: 0 12px;
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
  font-size: 17px;
  line-height: 1;
}

.inline-search button:hover {
  color: #6f835f;
}

.toggle {
  height: 37px;
  display: grid;
  width: 45%;
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
}

.toggle .on {
  background: #6f835f;
  color: #fff;
}

.state {
  height: 309px;
  display: grid;
  place-items: center;
  color: #7b7c75;
}

.state.error {
  color: #b24a3a;
}

.tasks {
  margin-top: 15px;
  height: 271px;
  overflow: hidden;
  border: 1px solid #efebe3;
  border-radius: 11px 11px 0 0;
  background: #fff;
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
  height: 90px;
  display: grid;
  grid-template-columns: 64px minmax(240px, 300px) 77px 230px 103px;
  align-items: center;
  gap: 15px;
  padding: 0 15px;
  border-bottom: 1px solid #eeeae2;
  background: #fff;
  cursor: pointer;
}

.task:nth-child(3) {
  border-bottom: 0;
}

.task:hover {
  background: #fbfbf7;
}

.icon {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border-radius: 17px;
  font-size: 23px;
  font-weight: 900;
}

.i-green { background: #eef3ea; color: #6e825e; }
.i-orange { background: #fbefdd; color: #c97a25; }
.i-blue { background: #edf4fb; color: #4d7db9; }
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

.tag {
  padding: 3px 8px;
  border-radius: 6px;
  font-weight: 800;
}

.t-green { background: #e8f0e3; color: #6f835f; }
.t-orange { background: #faecd8; color: #c97a25; }
.t-blue { background: #e8f1fb; color: #4778b4; }
.t-violet { background: #ebe7f8; color: #7b6cc4; }

.reward {
  display: grid;
  justify-items: center;
  color: #6f835f;
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
  color: #6f835f;
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
  color: #6f835f;
  text-align: center;
  font-size: 14px;
  font-weight: 900;
}

.more {
  width: 100%;
  height: 38px;
  display: grid;
  place-items: center;
  border: 1px solid #efebe3;
  border-top: 0;
  border-radius: 0 0 11px 11px;
  background: #fffdfa;
  color: #6f835f;
  cursor: pointer;
  font-size: 13px;
  font-weight: 900;
}

.features {
  position: absolute;
  left: 17px;
  right: 17px;
  bottom: 19px;
  height: 64px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  padding: 0 18px;
  border: 1px solid #eee9df;
  border-radius: 13px;
  background: #fffdfa;
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
  background: #6f835f;
  color: #fff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18), 0 8px 16px rgba(92, 112, 78, 0.16);
}

.round svg {
  width: 22px;
  height: 22px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.round svg path:first-child:last-child {
  fill: currentColor;
  stroke: none;
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
  width: 357px;
}

.overview-card {
  height: 269px;
  padding: 21px 19px;
}

.card-head {
  height: 21px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.card-head h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 950;
}

.card-head a {
  color: #6f835f;
  text-decoration: none;
  font-size: 12px;
  font-weight: 800;
}

.overview {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.overview div {
  width: 151px;
  height: 94px;
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
  color: #6f835f;
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
  height: 193px;
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
  background: #6f835f;
}

.hot-empty {
  height: 120px;
  display: grid;
  place-items: center;
  color: #858781;
  font-size: 12px;
}

@media (max-width: 1180px) {
  .home-page {
    overflow: visible;
  }

  .hero,
  .content {
    width: calc(100vw - 32px);
  }

  .content {
    grid-template-columns: 1fr;
  }

  .task-panel {
    overflow-x: auto;
  }

  .side {
    grid-template-columns: repeat(2, 357px);
  }
}
</style>
