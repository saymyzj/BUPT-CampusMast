<template>
  <div class="profile-page">
    <div v-if="!authStore.currentUser" class="profile-state">请先登录</div>

    <div v-else class="profile-layout">
      <aside class="profile-sidebar">
        <section class="side-card">
          <h1>个人中心</h1>
          <RouterLink v-for="item in menuItems" :key="item.label" :to="item.to" class="side-link" :class="{ active: item.active }">
            <AppIcon :name="item.icon" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </section>

        <section class="help-card">
          <AppIcon name="help" />
          <strong>需要帮助？</strong>
          <p>联系客服处理账号、钱包与任务问题。</p>
        </section>
      </aside>

      <main class="profile-main">
        <section class="hero-card">
          <div class="avatar-wrap">
            <img v-if="user.avatarUrl" :src="user.avatarUrl" alt="" />
            <span v-else>{{ initial }}</span>
          </div>
          <div class="hero-copy">
            <div class="name-row">
              <h2>{{ user.nickname }}</h2>
              <button class="edit-button name-edit-button" type="button" @click="editing = !editing">
                <AppIcon name="edit" />
                {{ editing ? "收起" : "修改昵称" }}
              </button>
            </div>
            <p>北京邮电大学 · 校园互助用户</p>
            <div class="contact-row">
              <span><AppIcon name="message" />{{ user.studentEmail }}</span>
              <span><AppIcon name="phone" />{{ phoneText }}</span>
            </div>
            <p class="locations" :title="commonLocationText">常用地点：{{ commonLocationText }}</p>
          </div>
        </section>

        <section v-if="editing" class="edit-card">
          <form @submit.prevent="handleSave">
            <label>
              <span>昵称</span>
              <input v-model.trim="edit.nickname" maxlength="50" type="text" />
            </label>
            <p v-if="saveError" class="form-message error">{{ saveError }}</p>
            <p v-if="saveOk" class="form-message success">{{ saveOk }}</p>
            <button type="submit" :disabled="saving">{{ saving ? "保存中..." : "保存昵称" }}</button>
          </form>
        </section>

        <section class="metric-grid">
          <article class="metric-card">
            <span>请求者信用分</span>
            <strong>{{ user.requesterCreditScore }}</strong>
            <small>发布任务侧信用</small>
            <i><AppIcon name="trend" /></i>
          </article>
          <article class="metric-card">
            <span>助人者信用分</span>
            <strong>{{ user.helperCreditScore }}</strong>
            <small>接取任务侧信用</small>
            <i><AppIcon name="trend" /></i>
          </article>
          <article class="metric-card wide">
            <span>综合信用分</span>
            <strong>{{ user.overallCreditScore }} <em>{{ creditLabel }}</em></strong>
            <small>由平台信用模型计算</small>
            <i><AppIcon name="shield" /></i>
          </article>
          <article class="metric-card">
            <span>完成任务数</span>
            <strong>{{ completedCount }}</strong>
            <small>累计完成</small>
            <i><AppIcon name="clipboard" /></i>
          </article>
          <article class="metric-card">
            <span>平均评分</span>
            <strong>{{ ratingText }}</strong>
            <small>{{ ratingHint }}</small>
            <i><AppIcon name="star" /></i>
          </article>
        </section>

        <section class="content-grid">
          <article class="panel-card location-panel">
            <header>
              <h3>常用地点</h3>
            </header>
            <div v-if="commonLocations.length" class="location-list">
              <div v-for="location in commonLocations" :key="location.name" class="location-item">
                <span><AppIcon name="building" /></span>
                <div>
                  <strong :title="location.name">{{ location.name }}</strong>
                  <small>{{ location.count }} 次任务记录</small>
                </div>
              </div>
            </div>
            <p v-else class="empty-line">暂无常用地点记录</p>
          </article>

          <article class="panel-card task-panel">
            <header>
              <h3>最近任务</h3>
              <RouterLink to="/my-tasks">查看全部</RouterLink>
            </header>
            <div v-if="recentTasks.length" class="task-list">
              <div v-for="task in recentTasks" :key="task.id" class="task-row">
                <span :class="`dot ${task.category}`"><AppIcon :name="categoryIcon(task.category)" /></span>
                <div>
                  <strong>{{ task.title }}</strong>
                  <small>{{ statusLabel(task.status) }} · {{ formatDate(task.createdAt) }}</small>
                </div>
                <em>¥{{ task.reward }}</em>
              </div>
            </div>
            <p v-else class="empty-line">暂无任务记录</p>
          </article>

          <article class="panel-card settings-panel">
            <header>
              <h3>账户与设置</h3>
            </header>
            <template v-for="item in settingItems" :key="item.label">
              <button v-if="item.action === 'security'" type="button" class="setting-item" @click="openSecurityDialog">
                <span><AppIcon :name="item.icon" /></span>
                <div>
                  <strong>{{ item.label }}</strong>
                  <small>{{ item.caption }}</small>
                </div>
              </button>
              <RouterLink v-else :to="item.to || '/profile'" class="setting-item">
                <span><AppIcon :name="item.icon" /></span>
                <div>
                  <strong>{{ item.label }}</strong>
                  <small>{{ item.caption }}</small>
                </div>
              </RouterLink>
            </template>
          </article>
        </section>
      </main>
    </div>

    <div v-if="securityOpen" class="profile-modal-mask" @click.self="securityOpen = false">
      <section class="security-dialog">
        <header>
          <div>
            <h3>账号安全</h3>
            <p>绑定手机或修改当前账号密码。</p>
          </div>
          <button type="button" aria-label="关闭" @click="securityOpen = false">×</button>
        </header>
        <div class="security-list">
          <div>
            <span><AppIcon name="message" /></span>
            <strong>学校邮箱</strong>
            <small>{{ user.studentEmail }}</small>
          </div>
        </div>

        <form class="security-form" @submit.prevent="handleSecuritySave">
          <label>
            <span>绑定手机</span>
            <div class="security-control">
              <AppIcon name="phone" />
              <input v-model.trim="securityForm.phone" type="tel" placeholder="请输入手机号" />
            </div>
          </label>
          <label>
            <span>当前密码</span>
            <div class="security-control">
              <AppIcon name="lock" />
              <input v-model="securityForm.currentPassword" type="password" placeholder="修改密码时填写" />
            </div>
          </label>
          <label>
            <span>新密码</span>
            <div class="security-control">
              <AppIcon name="lock" />
              <input v-model="securityForm.password" type="password" minlength="6" placeholder="不修改请留空" />
            </div>
          </label>
          <label>
            <span>确认新密码</span>
            <div class="security-control">
              <AppIcon name="lock" />
              <input v-model="securityForm.confirmPassword" type="password" minlength="6" placeholder="再次输入新密码" />
            </div>
          </label>
          <p v-if="securityError" class="form-message error">{{ securityError }}</p>
          <p v-if="securityOk" class="form-message success">{{ securityOk }}</p>
          <button type="submit" :disabled="securitySaving">{{ securitySaving ? "保存中..." : "保存安全设置" }}</button>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";
import AppIcon from "@/components/ui/AppIcon.vue";
import { changePassword } from "@/api/modules/auth";
import { getMyCreditProfile } from "@/api/modules/credit";
import { listMyAcceptedTasks, listMyPostedTasks } from "@/api/modules/task";
import { useAuthStore } from "@/stores/auth";
import type { CreditProfile, Task, TaskCategory, TaskStatus } from "@/types/api";

const authStore = useAuthStore();
const editing = ref(false);
const saving = ref(false);
const saveError = ref("");
const saveOk = ref("");
const securityOpen = ref(false);
const securitySaving = ref(false);
const securityError = ref("");
const securityOk = ref("");
const postedTasks = ref<Task[]>([]);
const acceptedTasks = ref<Task[]>([]);
const creditProfile = ref<CreditProfile | null>(null);
const edit = reactive({ nickname: "" });
const securityForm = reactive({
  phone: "",
  currentPassword: "",
  password: "",
  confirmPassword: "",
});

const user = computed(() => authStore.currentUser!);
const initial = computed(() => user.value.nickname?.slice(0, 1) || "用");
const phoneText = computed(() => {
  const phone = (user.value as unknown as { phone?: string | null }).phone;
  if (!phone) return "未绑定手机";
  return phone;
});

const allTasks = computed(() => {
  const map = new Map<string, Task>();
  [...postedTasks.value, ...acceptedTasks.value].forEach((task) => map.set(task.id, task));
  return [...map.values()].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
});
const recentTasks = computed(() => allTasks.value.slice(0, 4));
const completedCount = computed(() => allTasks.value.filter((task) => task.status === "COMPLETED").length);
const creditLabel = computed(() => (user.value.overallCreditScore >= 90 ? "优秀" : user.value.overallCreditScore >= 75 ? "良好" : "正常"));
const ratingText = computed(() => {
  if (!creditProfile.value?.ratingCount) return "--";
  return creditProfile.value.averageRating.toFixed(1);
});
const ratingHint = computed(() => (creditProfile.value?.ratingCount ? `${creditProfile.value.ratingCount} 条收到的评价` : "暂无收到的评价"));

const commonLocations = computed(() => {
  const counts = new Map<string, number>();
  allTasks.value.forEach((task) => {
    const name = task.locationDetail?.trim();
    if (name) counts.set(name, (counts.get(name) || 0) + 1);
  });
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 3);
});
const commonLocationText = computed(() => commonLocations.value.map((item) => item.name).join(" / ") || "暂无常用地点");

const menuItems = [
  { label: "个人资料", icon: "user", to: "/profile", active: true },
  { label: "我的任务", icon: "clipboard", to: "/my-tasks", active: false },
  { label: "我的钱包", icon: "wallet", to: "/wallet", active: false },
  { label: "消息通知", icon: "bell", to: "/chat", active: false },
];

const settingItems = [
  { label: "账号安全", caption: "查看登录与联系方式", icon: "shield", action: "security" },
  { label: "通知设置", caption: "管理消息提醒", icon: "bell", to: "/chat" },
  { label: "收支钱包", caption: "余额与资金流水", icon: "wallet", to: "/wallet" },
  { label: "我的任务", caption: "发布与接取记录", icon: "clipboard", to: "/my-tasks" },
];

const categoryIcons: Record<TaskCategory, string> = {
  package: "package",
  food: "food",
  move: "move",
  other: "other",
};

const statusLabels: Record<TaskStatus, string> = {
  PENDING: "待领取",
  IN_PROGRESS: "进行中",
  PENDING_REVIEW: "待验收",
  COMPLETED: "已完成",
  DISPUTED: "争议中",
  CANCELLED: "已取消",
  EXPIRED: "已过期",
  CLOSED_BY_ADMIN: "后台关闭",
};

function categoryIcon(category: TaskCategory) {
  return categoryIcons[category] || "other";
}

function statusLabel(status: TaskStatus) {
  return statusLabels[status] || status;
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" });
}

function openSecurityDialog() {
  securityError.value = "";
  securityOk.value = "";
  securityForm.phone = (authStore.currentUser as unknown as { phone?: string | null })?.phone || "";
  securityForm.currentPassword = "";
  securityForm.password = "";
  securityForm.confirmPassword = "";
  securityOpen.value = true;
}

async function handleSecuritySave() {
  securityError.value = "";
  securityOk.value = "";
  if (securityForm.password && securityForm.password !== securityForm.confirmPassword) {
    securityError.value = "两次输入的新密码不一致";
    return;
  }
  if (securityForm.password && !securityForm.currentPassword) {
    securityError.value = "请输入当前密码";
    return;
  }

  securitySaving.value = true;
  try {
    await authStore.updateCurrentUserProfile({
      phone: securityForm.phone.trim() || null,
    } as any);
    if (securityForm.password) {
      await changePassword({
        currentPassword: securityForm.currentPassword,
        newPassword: securityForm.password,
      });
    }
    securityOk.value = "账号安全设置已保存";
    securityForm.currentPassword = "";
    securityForm.password = "";
    securityForm.confirmPassword = "";
  } catch (err: any) {
    securityError.value = err?.response?.data?.error?.message || "保存失败";
  } finally {
    securitySaving.value = false;
  }
}

async function loadProfileData() {
  if (!authStore.currentUser) return;
  edit.nickname = authStore.currentUser.nickname || "";
  try {
    const [posted, accepted, credit] = await Promise.all([
      listMyPostedTasks({ page: 1, limit: 50 }),
      listMyAcceptedTasks({ page: 1, limit: 50 }),
      getMyCreditProfile(),
    ]);
    postedTasks.value = posted.data;
    acceptedTasks.value = accepted.data;
    creditProfile.value = credit;
  } catch {
    postedTasks.value = [];
    acceptedTasks.value = [];
    creditProfile.value = null;
  }
}

async function handleSave() {
  saveError.value = "";
  saveOk.value = "";
  saving.value = true;
  try {
    await authStore.updateCurrentUserProfile({
      nickname: edit.nickname.trim() || undefined,
    } as any);
    saveOk.value = "保存成功";
    editing.value = false;
  } catch (err: any) {
    saveError.value = err?.response?.data?.error?.message || "保存失败";
  } finally {
    saving.value = false;
  }
}

onMounted(loadProfileData);
</script>

<style scoped>
.profile-page {
  min-height: calc(100dvh - 86px);
  padding: clamp(18px, 2.4vw, 30px);
  background: #f7f5ef;
  color: #252720;
}

.profile-layout {
  width: min(100%, 1540px);
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(190px, 220px) minmax(0, 1fr);
  gap: clamp(18px, 2vw, 26px);
}

.profile-state {
  padding: 80px 20px;
  color: #7e8178;
  text-align: center;
}

.profile-sidebar {
  min-width: 0;
  display: grid;
  align-content: space-between;
  gap: 18px;
}

.side-card,
.help-card,
.hero-card,
.edit-card,
.metric-card,
.panel-card {
  border: 1px solid #ebe7df;
  border-radius: 12px;
  background: rgba(255, 254, 251, 0.92);
  box-shadow: 0 16px 38px rgba(60, 52, 42, 0.06);
}

.side-card {
  padding: 18px 14px;
}

.side-card h1 {
  margin: 0 0 18px 8px;
  font-size: 18px;
  font-weight: 950;
}

.side-link {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 8px;
  color: #555950;
  text-decoration: none;
  font-size: 14px;
  font-weight: 750;
}

.side-link.active {
  background: #eef1e8;
  color: #62784f;
}

.side-link .app-icon {
  flex: 0 0 auto;
}

.help-card {
  padding: 18px;
  color: #6f746a;
}

.help-card > .app-icon {
  color: #6f835f;
  font-size: 22px;
}

.help-card strong {
  display: block;
  margin-top: 8px;
  color: #2a2d26;
}

.help-card p {
  margin: 8px 0 14px;
  font-size: 12px;
  line-height: 1.6;
}

.edit-card button,
.edit-button {
  border: 1px solid #cfd9c7;
  border-radius: 7px;
  background: #fffefa;
  color: #617650;
  cursor: pointer;
  font-weight: 850;
}

.profile-main {
  min-width: 0;
  display: grid;
  gap: 16px;
}

.hero-card {
  position: relative;
  min-height: clamp(180px, 19vw, 230px);
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: clamp(20px, 3vw, 40px);
  padding: clamp(22px, 3vw, 34px);
  overflow: hidden;
}

.hero-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(255, 254, 251, 0.98) 0%, rgba(255, 254, 251, 0.92) 38%, rgba(255, 254, 251, 0.22) 68%), url("/assets/hero-bupt-gate.jpg") right center / auto 118% no-repeat;
}

.hero-card > * {
  position: relative;
  z-index: 1;
}

.avatar-wrap {
  position: relative;
  width: clamp(92px, 9vw, 122px);
  aspect-ratio: 1;
  border: 4px solid #fff;
  border-radius: 50%;
  box-shadow: 0 14px 30px rgba(60, 52, 42, 0.14);
  background: #e7ecdf;
  display: grid;
  place-items: center;
  color: #647953;
  font-size: 38px;
  font-weight: 950;
  overflow: visible;
}

.avatar-wrap img {
  width: 100%;
  height: 100%;
  border-radius: inherit;
  object-fit: cover;
}

.avatar-wrap i {
  position: absolute;
  right: -2px;
  bottom: 4px;
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border: 3px solid #fff;
  border-radius: 50%;
  background: #788b66;
  color: #fff;
}

.hero-copy {
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.name-row h2 {
  margin: 0;
  flex: 0 1 auto;
  max-width: min(100%, 520px);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: clamp(28px, 3vw, 38px);
  font-weight: 950;
}

.name-row span,
.metric-card em {
  padding: 4px 10px;
  border-radius: 999px;
  background: #748964;
  color: #fff;
  font-size: 13px;
  font-style: normal;
  font-weight: 900;
}

.hero-copy p {
  margin: 10px 0 0;
  color: #5d6158;
  line-height: 1.6;
}

.contact-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 12px;
  color: #777a72;
  font-size: 13px;
}

.contact-row span,
.locations {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contact-row span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.edit-button {
  align-self: start;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  white-space: nowrap;
}

.name-edit-button {
  align-self: center;
  flex: 0 0 auto;
  padding: 8px 12px;
  font-size: 13px;
}

.edit-card {
  padding: 18px;
}

.edit-card form {
  display: grid;
  grid-template-columns: minmax(220px, 420px) auto;
  gap: 14px;
  align-items: end;
}

.edit-card label {
  display: grid;
  gap: 6px;
  color: #51554d;
  font-size: 13px;
  font-weight: 800;
}

.edit-card input {
  min-width: 0;
  height: 40px;
  padding: 0 12px;
  border: 1px solid #e5e0d6;
  border-radius: 7px;
  background: #fff;
}

.edit-card button {
  height: 40px;
  padding: 0 18px;
}

.form-message {
  grid-column: 1 / -1;
  margin: 0;
  font-size: 13px;
}

.form-message.error { color: #b8544a; }
.form-message.success { color: #668052; }

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
}

.metric-card {
  position: relative;
  min-width: 0;
  min-height: 128px;
  padding: 20px;
  overflow: hidden;
}

.metric-card span,
.metric-card small {
  display: block;
  color: #697066;
}

.metric-card strong {
  display: block;
  margin: 8px 0 8px;
  color: #6f835f;
  font-size: clamp(24px, 2.2vw, 32px);
  font-weight: 950;
}

.metric-card > i {
  position: absolute;
  right: 18px;
  bottom: 18px;
  width: 54px;
  height: 54px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #eef1e8;
  color: #6f835f;
  font-size: 26px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(250px, 0.85fr) minmax(340px, 1.35fr) minmax(320px, 1.1fr);
  gap: 16px;
}

.panel-card {
  min-width: 0;
  padding: 20px;
}

.panel-card header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-card h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 950;
}

.panel-card a,
.panel-card button {
  border: 0;
  background: transparent;
  color: #6f835f;
  text-decoration: none;
  font-size: 13px;
  font-weight: 850;
}

.location-list,
.task-list {
  display: grid;
}

.location-item,
.task-row,
.setting-item {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 13px 0;
  border-bottom: 1px solid #eee9df;
  text-decoration: none;
}

.location-item:last-child,
.task-row:last-child,
.setting-item:last-child {
  border-bottom: 0;
}

.location-item > span,
.dot,
.setting-item > span {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: #eef1e8;
  color: #6f835f;
  font-size: 20px;
}

.location-item strong,
.task-row strong,
.setting-item strong {
  display: block;
  min-width: 0;
  overflow: hidden;
  color: #252720;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.location-item > div,
.task-row > div,
.setting-item > div {
  min-width: 0;
}

.location-item small,
.task-row small,
.setting-item small {
  display: block;
  margin-top: 4px;
  color: #85887f;
  font-size: 12px;
}

.task-row em {
  color: #6f835f;
  font-style: normal;
  font-weight: 950;
}

.dot.package { background: #e8f1fb; color: #4778b4; }
.dot.food { background: #faecd8; color: #c97a25; }
.dot.move { background: #e8f0e3; color: #6d835f; }
.dot.other { background: #ebe7f8; color: #7b6cc4; }

.settings-panel {
  grid-column: span 1;
}

.setting-item {
  color: inherit;
  width: 100%;
  border: 0;
  background: transparent;
  cursor: pointer;
  font: inherit;
  text-align: left;
}

.profile-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(33, 35, 30, 0.24);
  backdrop-filter: blur(8px);
}

.security-dialog {
  width: min(460px, 100%);
  padding: 22px;
  border: 1px solid #ebe7df;
  border-radius: 14px;
  background: rgba(255, 254, 251, 0.98);
  box-shadow: 0 24px 70px rgba(60, 52, 42, 0.18);
}

.security-dialog header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.security-dialog h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 950;
}

.security-dialog p {
  margin: 6px 0 0;
  color: #777a72;
  font-size: 13px;
}

.security-dialog header button {
  width: 34px;
  height: 34px;
  border: 1px solid #e5e0d6;
  border-radius: 50%;
  background: #fff;
  color: #5e6259;
  cursor: pointer;
  font-size: 20px;
}

.security-list {
  display: grid;
  gap: 10px;
  margin-bottom: 14px;
}

.security-list div {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(90px, 0.42fr) minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid #eee9df;
  border-radius: 10px;
  background: #fffdfa;
}

.security-list span {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: #eef1e8;
  color: #6f835f;
}

.security-list strong {
  color: #252720;
  font-size: 13px;
}

.security-list small {
  min-width: 0;
  overflow-wrap: anywhere;
  color: #73776e;
  font-size: 13px;
}

.security-form {
  display: grid;
  gap: 12px;
}

.security-form label {
  display: grid;
  gap: 7px;
  color: #51554d;
  font-size: 13px;
  font-weight: 850;
}

.security-control {
  height: 42px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  border: 1px solid #e5e0d6;
  border-radius: 8px;
  background: #fff;
  color: #8a8d86;
}

.security-control input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  color: #252720;
  font: inherit;
}

.security-form > button {
  height: 42px;
  border: 0;
  border-radius: 8px;
  background: #6f835f;
  color: #fff;
  cursor: pointer;
  font-weight: 900;
}

.security-form > button:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.empty-line {
  margin: 0;
  padding: 26px 0;
  color: #90938b;
  text-align: center;
  font-size: 13px;
}

@media (max-width: 1180px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }

  .profile-sidebar {
    display: none;
  }

  .metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .content-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 760px) {
  .hero-card,
  .edit-card form,
  .content-grid,
  .metric-grid {
    grid-template-columns: 1fr;
  }

  .hero-card::before {
    background: linear-gradient(90deg, rgba(255, 254, 251, 0.98), rgba(255, 254, 251, 0.76)), url("/assets/hero-bupt-gate.jpg") center / cover no-repeat;
  }
}
</style>
