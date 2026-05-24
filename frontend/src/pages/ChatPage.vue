<template>
  <div class="chat-page">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">CM</div>
        <div class="brand-copy">
          <strong>CampusMast</strong>
          <span>校园互助 · 让帮助更简单</span>
        </div>
      </div>

      <nav class="nav">
        <button
          v-for="item in navItems"
          :key="item.id"
          class="nav-item"
          :class="{ active: activeNav === item.id }"
          @click="router.push(item.route)"
        >
          <span class="nav-label">{{ item.label }}</span>
        </button>
      </nav>

      <section class="sidebar-section">
        <div class="section-title">聊天概览</div>
        <div class="quick-list">
          <div class="quick-row">
            <span class="quick-dot" style="background:#6c5ce7">{{ visibleConversations.length }}</span>
            <span>进行中会话</span>
          </div>
          <div class="quick-row">
            <span class="quick-dot" style="background:#ff4757">{{ unreadTotal }}</span>
            <span>未读消息</span>
          </div>
          <div class="quick-row">
            <span class="quick-dot" style="background:#32c483">{{ repliedTodayCount }}</span>
            <span>今日已回复</span>
          </div>
        </div>
      </section>

      <button class="publish-btn" @click="router.push('/tasks/new')">+ 发布任务</button>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div class="topbar-left">
          <button class="collapse-btn" title="返回任务大厅" @click="router.push('/tasks')">‹</button>
          <span class="topbar-title">任务聊天</span>
          <span class="status-pill"><span class="status-dot"></span>实时在线</span>
        </div>
        <div class="topbar-actions">
          <button class="view-btn" @click="router.push('/tasks')">查看任务大厅</button>
          <button class="round-btn" title="消息中心" @click="router.push('/notifications')">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M18 10.8c0-3.3-2.1-5.8-5.1-6.4V3a.9.9 0 0 0-1.8 0v1.4C8.1 5 6 7.5 6 10.8v3.4l-1.5 2.4h15l-1.5-2.4v-3.4Z" />
              <path d="M9.7 18.4a2.4 2.4 0 0 0 4.6 0" />
            </svg>
            <span v-if="unreadTotal" class="badge"></span>
          </button>
          <button class="avatar" title="个人资料" @click="router.push('/profile')">
            {{ currentInitial }}
          </button>
        </div>
      </header>

      <section class="chat-stage">
        <aside class="conversation-list" :class="{ hidden: activeConv }">
          <div class="panel-head">
            <span class="panel-title">会话列表</span>
            <span class="panel-count">{{ visibleConversations.length }} 个任务</span>
          </div>
          <label class="search-box">
            <span>⌕</span>
            <input v-model="keyword" type="search" placeholder="搜索任务或联系人" />
          </label>

          <div class="conversation-scroll">
            <div v-if="loading" class="state-box">加载中...</div>
            <div v-else-if="error" class="state-box state-error">{{ error }}</div>
            <div v-else-if="filteredConversations.length === 0" class="state-box">
              <strong>暂无聊天会话</strong>
              <span>接单后会自动创建任务聊天</span>
            </div>

            <button
              v-for="conversation in filteredConversations"
              v-else
              :key="conversation.id"
              class="conv-item"
              :class="{ active: activeConv?.id === conversation.id }"
              @click="openConv(conversation)"
            >
              <span class="conv-avatar" :style="{ background: conversationColor(conversation) }">
                {{ partnerInitial(conversation) }}
              </span>
              <span class="conv-main">
                <span class="conv-title-row">
                  <span class="conv-title">{{ partnerName(conversation) }}</span>
                  <span class="task-tag" :style="categoryStyle(conversation)">{{ categoryLabel(conversation) }}</span>
                </span>
                <span class="conv-preview">{{ conversationPreview(conversation) }}</span>
              </span>
              <span class="conv-meta">
                <span class="conv-time">{{ conversation.latestMessage ? formatShort(conversation.latestMessage.createdAt) : "" }}</span>
                <span v-if="conversation.unreadCount > 0" class="unread">{{ conversation.unreadCount }}</span>
              </span>
            </button>
          </div>
        </aside>

        <section class="chat-main" :class="{ expanded: activeConv }">
          <div v-if="!activeConv" class="empty-chat">
            <strong>选择一个任务会话</strong>
            <span>在这里和对方确认任务细节、交付时间和地点</span>
          </div>

          <template v-else>
            <div class="chat-header">
              <div class="chat-user">
                <button class="mobile-back" @click="activeConv = null">‹</button>
                <span class="chat-avatar">{{ activePartnerInitial }}</span>
                <div class="chat-title-copy">
                  <div class="chat-name">{{ activePartnerName }}</div>
                  <div class="chat-sub">{{ activeTaskSubtitle }}</div>
                </div>
              </div>
              <div class="chat-actions">
                <button class="icon-btn" title="任务详情" @click="goTaskDetail">详</button>
                <button class="icon-btn" title="刷新消息" @click="refreshActiveConversation">刷</button>
                <button class="icon-btn" title="更多">···</button>
              </div>
            </div>

            <div ref="msgBodyRef" class="message-scroll">
              <div class="day-divider"><span>{{ activeDateLabel }}</span></div>
              <div class="system-note">任务聊天已建立，请在聊天中确认具体交付信息。</div>

              <div v-if="msgLoading" class="state-box">加载中...</div>
              <div v-else-if="messages.length === 0" class="state-box">
                <strong>暂无消息</strong>
                <span>发送第一条消息，和对方确认任务细节</span>
              </div>

              <div
                v-for="message in messages"
                :key="message.id"
                class="msg-row"
                :class="{ mine: message.senderId === userId }"
              >
                <span v-if="message.senderId !== userId" class="msg-mini">{{ activePartnerInitial }}</span>
                <div class="bubble-wrap">
                  <div class="bubble">{{ message.content }}</div>
                  <div class="bubble-time">{{ formatShort(message.createdAt) }}</div>
                </div>
              </div>
            </div>

            <form class="composer" @submit.prevent="sendMsg">
              <button class="attach-btn" type="button" title="添加附件">+</button>
              <textarea
                v-model="newMsg"
                class="composer-input"
                rows="1"
                maxlength="500"
                placeholder="输入消息，和对方确认任务细节"
                @keydown.enter.exact.prevent="sendMsg"
              ></textarea>
              <button class="icon-btn emoji-btn" type="button" title="表情">表</button>
              <button class="send-btn" type="submit" :disabled="!newMsg.trim() || sending">
                {{ sending ? "发送中" : "发送" }}
              </button>
            </form>
          </template>
        </section>

        <aside class="task-panel">
          <div class="panel-head">
            <span class="panel-title">任务信息</span>
            <span class="panel-count">{{ activeTaskStatusText }}</span>
          </div>
          <div v-if="!activeTask" class="task-empty">
            <strong>暂无任务信息</strong>
            <span>选择会话后显示任务摘要</span>
          </div>
          <div v-else class="task-content">
            <div class="task-summary-card">
              <div class="task-type-row">
                <span class="type-chip" :style="activeCategoryStyle">{{ activeCategoryLabel }}</span>
                <span class="remain">{{ activeTimeLeft }}</span>
              </div>
              <h2 class="task-title">{{ activeTask.title }}</h2>
              <div class="reward">{{ formatReward(activeTask.reward) }}</div>
              <p class="task-desc">{{ activeTask.description }}</p>
            </div>

            <div class="info-list">
              <div class="info-row">
                <span class="info-label">接单者</span>
                <span class="info-value">{{ activeHelperText }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">地点</span>
                <span class="info-value">{{ activeTask.locationDetail || "校内地点" }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">截止时间</span>
                <span class="info-value">{{ formatDeadline(activeTask.deadline) }}</span>
              </div>
            </div>

            <div class="side-actions">
              <button class="side-btn primary" @click="goTaskDetail">查看任务详情</button>
              <button class="side-btn secondary" @click="router.push('/my-tasks')">进入我的任务</button>
            </div>
          </div>
        </aside>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  createTaskChatMessage,
  listChatConversations,
  listTaskChatMessages,
  markConversationRead,
} from "@/api/modules/chat";
import { getTaskById } from "@/api/modules/task";
import { useAuthStore } from "@/stores/auth";
import { CATEGORY_COLORS, CATEGORY_LABELS } from "@/types/map";
import { isTaskVisible } from "@/utils/taskVisibility";
import type { ChatConversation, ChatMessage, TaskCategory, TaskDetail, UserSummary } from "@/types/api";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const userId = computed(() => authStore.userId ?? "");

const conversations = ref<ChatConversation[]>([]);
const taskById = ref<Record<string, TaskDetail>>({});
const loading = ref(false);
const error = ref("");
const keyword = ref("");

const activeConv = ref<ChatConversation | null>(null);
const messages = ref<ChatMessage[]>([]);
const msgLoading = ref(false);
const newMsg = ref("");
const sending = ref(false);
const msgBodyRef = ref<HTMLElement | null>(null);

const navItems = [
  { id: "map", label: "地图", route: "/map" },
  { id: "tasks", label: "任务大厅", route: "/tasks" },
  { id: "my-tasks", label: "我的任务", route: "/my-tasks" },
  { id: "chat", label: "任务聊天", route: "/chat" },
  { id: "wallet", label: "积分钱包", route: "/wallet" },
];

const hiddenConversationStatuses = new Set(["CANCELLED", "EXPIRED", "CLOSED_BY_ADMIN"]);

const activeNav = computed(() => {
  const path = route.path;
  const matched = navItems.find((item) => path === item.route || (item.route !== "/tasks" && path.startsWith(item.route)));
  return matched?.id ?? "chat";
});

const visibleConversations = computed(() =>
  conversations.value.filter((conversation) => {
    if (conversation.taskStatus && hiddenConversationStatuses.has(conversation.taskStatus)) return false;
    const task = taskById.value[conversation.taskId];
    return task ? isTaskVisible(task) : true;
  }),
);

const filteredConversations = computed(() => {
  const q = keyword.value.trim().toLowerCase();
  if (!q) return visibleConversations.value;
  return visibleConversations.value.filter((conversation) => {
    const task = taskById.value[conversation.taskId];
    return [
      partnerName(conversation),
      task?.title,
      task?.description,
      task?.locationDetail,
      categoryLabel(conversation),
      conversation.latestMessage?.content,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(q));
  });
});

const unreadTotal = computed(() =>
  visibleConversations.value.reduce((sum, conversation) => sum + conversation.unreadCount, 0),
);

const repliedTodayCount = computed(() => {
  const today = new Date().toDateString();
  return visibleConversations.value.filter((conversation) => {
    const latest = conversation.latestMessage;
    return latest?.senderId === userId.value && new Date(latest.createdAt).toDateString() === today;
  }).length;
});

const currentInitial = computed(() => initialOf(authStore.currentUser?.nickname));
const activeTask = computed(() => (activeConv.value ? taskById.value[activeConv.value.taskId] ?? null : null));
const activePartner = computed(() => (activeTask.value ? getPartner(activeTask.value) : null));
const activePartnerName = computed(() => activePartner.value?.nickname ?? "任务聊天");
const activePartnerInitial = computed(() => initialOf(activePartnerName.value));
const activeCategoryLabel = computed(() => (activeTask.value ? categoryName(activeTask.value.category) : "任务"));
const activeCategoryColor = computed(() => (activeTask.value ? categoryColor(activeTask.value.category) : "#6c5ce7"));
const activeCategoryStyle = computed(() => ({
  color: activeCategoryColor.value,
  background: `${activeCategoryColor.value}18`,
}));
const activeTaskSubtitle = computed(() => {
  if (!activeTask.value) return "任务聊天";
  const credit = activePartner.value ? ` · 信用 ${activePartner.value.overallCreditScore}` : "";
  return `任务：${activeTask.value.title}${credit}`;
});
const activeTimeLeft = computed(() => (activeTask.value ? `剩余 ${computeTimeLeft(activeTask.value.deadline)}` : ""));
const activeHelperText = computed(() => {
  const helper = activeTask.value?.helper;
  if (!helper) return "暂未接单";
  return `${helper.nickname} · 信用 ${helper.overallCreditScore}`;
});
const activeTaskStatusText = computed(() => {
  if (!activeTask.value) return "未选择";
  const statusMap: Record<string, string> = {
    PENDING: "待接单",
    IN_PROGRESS: "进行中",
    SUBMITTED: "待确认",
    COMPLETED: "已完成",
  };
  return statusMap[activeTask.value.status] ?? "进行中";
});
const activeDateLabel = computed(() => {
  const first = messages.value[0]?.createdAt;
  return first ? formatDateLabel(first) : "今天";
});

function initialOf(value?: string | null) {
  return value?.trim().charAt(0) || "?";
}

function categoryName(category?: TaskCategory) {
  return category ? CATEGORY_LABELS[category] ?? "其他" : "任务";
}

function categoryColor(category?: TaskCategory) {
  return category ? CATEGORY_COLORS[category] ?? "#6c5ce7" : "#6c5ce7";
}

function categoryStyle(conversation: ChatConversation) {
  const task = taskById.value[conversation.taskId];
  const color = categoryColor(task?.category);
  return { color, background: `${color}18` };
}

function categoryLabel(conversation: ChatConversation) {
  return categoryName(taskById.value[conversation.taskId]?.category);
}

function getPartner(task: TaskDetail): UserSummary | null {
  if (task.requester.id === userId.value) return task.helper ?? null;
  return task.requester;
}

function partnerName(conversation: ChatConversation) {
  const task = taskById.value[conversation.taskId];
  if (!task) return "任务聊天";
  return getPartner(task)?.nickname ?? "等待接单";
}

function partnerInitial(conversation: ChatConversation) {
  return initialOf(partnerName(conversation));
}

function conversationColor(conversation: ChatConversation) {
  const task = taskById.value[conversation.taskId];
  return categoryColor(task?.category);
}

function conversationPreview(conversation: ChatConversation) {
  return conversation.latestMessage?.content?.slice(0, 34) || taskById.value[conversation.taskId]?.title || "暂无消息";
}

function formatShort(iso: string) {
  const d = new Date(iso);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function formatDateLabel(iso: string) {
  const d = new Date(iso);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) return `今天 ${formatShort(iso)}`;
  return `${d.getMonth() + 1}/${d.getDate()} ${formatShort(iso)}`;
}

function formatDeadline(iso: string) {
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function formatReward(value: string) {
  const amount = Number.parseFloat(value);
  return Number.isFinite(amount) ? `¥${amount.toFixed(2)}` : value;
}

function computeTimeLeft(deadline: string) {
  const diff = new Date(deadline).getTime() - Date.now();
  if (diff <= 0) return "已截止";
  const hours = Math.floor(diff / 3600000);
  const minutes = Math.floor((diff % 3600000) / 60000);
  if (hours >= 24) return formatDeadline(deadline);
  if (hours > 0) return `${hours} 小时`;
  if (minutes > 0) return `${minutes} 分钟`;
  return "马上截止";
}

async function ensureTaskDetail(taskId: string) {
  if (taskById.value[taskId]) return taskById.value[taskId];
  const task = await getTaskById(taskId);
  taskById.value = { ...taskById.value, [taskId]: task };
  return task;
}

async function loadConversations() {
  loading.value = true;
  error.value = "";
  try {
    const all = await listChatConversations();
    const visibleByStatus = all.filter((conversation) => !conversation.taskStatus || !hiddenConversationStatuses.has(conversation.taskStatus));
    conversations.value = visibleByStatus;

    const taskIds = Array.from(new Set(visibleByStatus.map((conversation) => conversation.taskId)));
    const results = await Promise.allSettled(taskIds.map((taskId) => getTaskById(taskId)));
    const nextTasks: Record<string, TaskDetail> = {};
    results.forEach((result) => {
      if (result.status === "fulfilled" && isTaskVisible(result.value)) {
        nextTasks[result.value.id] = result.value;
      }
    });
    taskById.value = { ...taskById.value, ...nextTasks };
    conversations.value = visibleByStatus.filter((conversation) => {
      const task = nextTasks[conversation.taskId];
      return task ? isTaskVisible(task) : true;
    });
  } catch {
    error.value = "加载会话失败";
  } finally {
    loading.value = false;
  }
}

async function openConv(conversation: ChatConversation) {
  activeConv.value = conversation;
  messages.value = [];
  msgLoading.value = true;
  try {
    const [_, messageResult] = await Promise.all([
      ensureTaskDetail(conversation.taskId),
      listTaskChatMessages(conversation.taskId, { page: 1, limit: 50 }),
    ]);
    messages.value = messageResult.data.slice().reverse();
    const lastMessageId = messages.value[messages.value.length - 1]?.id;
    if (lastMessageId) await markConversationRead(conversation.id, { lastReadMessageId: lastMessageId });
    conversation.unreadCount = 0;
  } catch {
    error.value = "加载消息失败";
  } finally {
    msgLoading.value = false;
  }
  await nextTick();
  scrollBottom();
}

async function refreshActiveConversation() {
  if (activeConv.value) await openConv(activeConv.value);
}

function scrollBottom() {
  const el = msgBodyRef.value;
  if (el) el.scrollTop = el.scrollHeight;
}

async function sendMsg() {
  if (!newMsg.value.trim() || !activeConv.value || sending.value) return;
  const content = newMsg.value.trim();
  sending.value = true;
  try {
    const msg = await createTaskChatMessage(activeConv.value.taskId, { content });
    messages.value.push(msg);
    activeConv.value.latestMessage = msg;
    newMsg.value = "";
    await nextTick();
    scrollBottom();
  } finally {
    sending.value = false;
  }
}

function goTaskDetail() {
  if (!activeConv.value) return;
  router.push(`/tasks/${activeConv.value.taskId}`);
}

onMounted(loadConversations);
</script>

<style scoped>
.chat-page {
  position: fixed;
  inset: 0;
  display: flex;
  overflow: hidden;
  color: #202633;
  background: #f7f8fb;
  font-family: "Noto Sans SC", "Microsoft YaHei", Arial, sans-serif;
}

button,
input,
textarea {
  font: inherit;
}

.sidebar {
  width: 263px;
  min-width: 263px;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-right: 1px solid #eef0f5;
  box-shadow: 10px 0 34px rgba(31, 36, 48, 0.04);
  z-index: 4;
}

.brand {
  height: 76px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
}

.brand-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 13px;
  color: #fff;
  background: #111827;
  font-weight: 900;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.16);
}

.brand-copy strong {
  display: block;
  color: #171b27;
  font-size: 20px;
  line-height: 1.1;
  font-weight: 900;
}

.brand-copy span {
  display: block;
  margin-top: 4px;
  color: #9ca3af;
  font-size: 12px;
  white-space: nowrap;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px 14px 8px;
}

.nav-item {
  height: 48px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 14px;
  border: none;
  border-radius: 0;
  background: transparent;
  color: #686f7e;
  cursor: pointer;
  font-size: 15px;
  font-weight: 700;
  text-align: left;
}

.nav-item:hover,
.nav-item.active {
  color: #6c5ce7;
  background: linear-gradient(90deg, rgba(108, 92, 231, 0.14), rgba(108, 92, 231, 0.04));
}

.nav-item.active {
  box-shadow: inset 3px 0 0 #6c5ce7;
}

.sidebar-section {
  margin: 18px;
  padding-top: 18px;
  border-top: 1px solid #eef0f5;
}

.section-title {
  margin-bottom: 12px;
  color: #232937;
  font-size: 13px;
  font-weight: 900;
}

.quick-list {
  display: grid;
  gap: 10px;
}

.quick-row {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #5c6474;
  font-size: 12px;
  font-weight: 700;
}

.quick-dot {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 8px;
  color: #fff;
  font-size: 11px;
  font-weight: 900;
}

.publish-btn {
  height: 72px;
  margin: auto 18px 24px;
  border: none;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, #8657ff, #596cff);
  box-shadow: 0 18px 34px rgba(108, 92, 231, 0.28);
  cursor: pointer;
  font-weight: 900;
}

.workspace {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.topbar {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 1px 0 rgba(31, 36, 48, 0.06);
  z-index: 3;
}

.topbar-left,
.topbar-actions {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-left {
  flex: 1;
}

.collapse-btn {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: none;
  border-radius: 10px;
  color: #6d7280;
  background: transparent;
  cursor: pointer;
  font-size: 22px;
}

.topbar-title {
  overflow: hidden;
  color: #202633;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 18px;
  font-weight: 900;
}

.status-pill,
.view-btn {
  height: 40px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #eceef3;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 8px 22px rgba(31, 36, 48, 0.05);
  color: #3a4050;
  padding: 0 14px;
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
}

.view-btn,
.round-btn,
.avatar {
  cursor: pointer;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #32c483;
  box-shadow: 0 0 0 4px rgba(50, 196, 131, 0.14);
}

.round-btn,
.avatar {
  position: relative;
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border: 1px solid #eceef3;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 8px 22px rgba(31, 36, 48, 0.05);
  color: #202633;
  font-weight: 900;
}

.round-btn svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.avatar {
  border: none;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(145deg, #4a4650, #c8b2a6);
}

.badge {
  position: absolute;
  top: 6px;
  right: 7px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff4757;
}

.chat-stage {
  min-height: 0;
  flex: 1;
  display: grid;
  grid-template-columns: 320px minmax(420px, 1fr) 292px;
  border-top: 1px solid rgba(31, 36, 48, 0.06);
  overflow: hidden;
}

.conversation-list,
.task-panel {
  background: #fff;
}

.conversation-list {
  min-width: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #eef0f5;
}

.panel-head {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 18px;
  border-bottom: 1px solid #eef0f5;
}

.panel-title {
  color: #202633;
  font-size: 15px;
  font-weight: 900;
}

.panel-count {
  flex-shrink: 0;
  padding: 3px 8px;
  border-radius: 999px;
  color: #6c5ce7;
  background: #f3f0ff;
  font-size: 11px;
  font-weight: 900;
}

.search-box {
  height: 40px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 14px;
  padding: 0 12px;
  border: 1px solid #eceef3;
  border-radius: 12px;
  background: #fbfcfe;
  color: #9aa1ae;
  font-size: 13px;
  font-weight: 700;
}

.search-box input {
  min-width: 0;
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: #202633;
}

.conversation-scroll {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  padding: 0 10px 14px;
}

.conv-item {
  width: 100%;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 12px 10px;
  border: none;
  border-radius: 12px;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.conv-item + .conv-item {
  margin-top: 6px;
}

.conv-item:hover,
.conv-item.active {
  background: linear-gradient(90deg, rgba(108, 92, 231, 0.13), rgba(108, 92, 231, 0.04));
}

.conv-item.active {
  box-shadow: inset 3px 0 0 #6c5ce7;
}

.conv-avatar {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  color: #fff;
  font-size: 15px;
  font-weight: 900;
}

.conv-main {
  min-width: 0;
}

.conv-title-row {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.conv-title,
.conv-preview {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-title {
  color: #202633;
  font-size: 13px;
  font-weight: 900;
}

.task-tag {
  flex-shrink: 0;
  padding: 2px 6px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 900;
}

.conv-preview {
  display: block;
  margin-top: 5px;
  color: #8b93a2;
  font-size: 12px;
  font-weight: 700;
}

.conv-meta {
  display: grid;
  justify-items: end;
  gap: 6px;
}

.conv-time {
  color: #a2a8b4;
  font-size: 11px;
  font-weight: 700;
}

.unread {
  min-width: 19px;
  height: 19px;
  display: grid;
  place-items: center;
  padding: 0 6px;
  border-radius: 10px;
  color: #fff;
  background: #ff4757;
  font-size: 10px;
  font-weight: 900;
}

.chat-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(rgba(247, 248, 251, 0.94), rgba(247, 248, 251, 0.94)),
    radial-gradient(circle at top left, rgba(108, 92, 231, 0.14), transparent 36%),
    radial-gradient(circle at bottom right, rgba(255, 138, 52, 0.12), transparent 32%);
}

.empty-chat,
.state-box,
.task-empty {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  min-height: 180px;
  padding: 28px;
  color: #8b93a2;
  text-align: center;
  font-size: 13px;
  font-weight: 700;
}

.empty-chat {
  flex: 1;
}

.state-box strong,
.empty-chat strong,
.task-empty strong {
  color: #202633;
  font-size: 15px;
  font-weight: 900;
}

.state-error {
  color: #ff4757;
}

.chat-header {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 22px;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid #eef0f5;
}

.chat-user {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.mobile-back {
  display: none;
}

.chat-avatar {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(145deg, #6c5ce7, #596cff);
  font-weight: 900;
  box-shadow: 0 10px 24px rgba(108, 92, 231, 0.2);
}

.chat-title-copy {
  min-width: 0;
}

.chat-name,
.chat-sub {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-name {
  color: #202633;
  font-size: 15px;
  font-weight: 900;
}

.chat-sub {
  margin-top: 3px;
  color: #8b93a2;
  font-size: 12px;
  font-weight: 700;
}

.chat-actions {
  display: flex;
  gap: 10px;
}

.icon-btn {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border: 1px solid #eceef3;
  border-radius: 12px;
  background: #fff;
  color: #555e70;
  cursor: pointer;
  font-size: 13px;
  font-weight: 900;
  box-shadow: 0 8px 20px rgba(31, 36, 48, 0.05);
}

.message-scroll {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  padding: 22px;
}

.day-divider {
  display: flex;
  justify-content: center;
  margin-bottom: 18px;
}

.day-divider span {
  padding: 5px 10px;
  border: 1px solid rgba(236, 238, 243, 0.9);
  border-radius: 999px;
  color: #8b93a2;
  background: rgba(255, 255, 255, 0.86);
  font-size: 11px;
  font-weight: 800;
}

.msg-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-bottom: 14px;
}

.msg-row.mine {
  justify-content: flex-end;
}

.msg-mini {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 50%;
  color: #fff;
  background: #111827;
  font-size: 11px;
  font-weight: 900;
}

.bubble-wrap {
  max-width: min(520px, 72%);
}

.bubble {
  padding: 11px 14px;
  border: 1px solid rgba(31, 36, 48, 0.06);
  border-radius: 16px 16px 16px 6px;
  background: #fff;
  color: #343b4c;
  box-shadow: 0 8px 22px rgba(31, 36, 48, 0.06);
  font-size: 14px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg-row.mine .bubble {
  border: none;
  border-radius: 16px 16px 6px 16px;
  color: #fff;
  background: linear-gradient(135deg, #8657ff, #596cff);
  box-shadow: 0 14px 26px rgba(108, 92, 231, 0.22);
}

.bubble-time {
  margin-top: 5px;
  padding: 0 4px;
  color: #9aa1ae;
  font-size: 10px;
  font-weight: 700;
}

.msg-row.mine .bubble-time {
  text-align: right;
}

.system-note {
  max-width: 520px;
  margin: 18px auto;
  padding: 10px 14px;
  border: 1px solid #ffe1bd;
  border-radius: 12px;
  color: #9a5b1f;
  background: #fff7ed;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
}

.composer {
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  gap: 10px;
  align-items: end;
  padding: 14px 18px 18px;
  background: rgba(255, 255, 255, 0.96);
  border-top: 1px solid #eef0f5;
}

.attach-btn,
.send-btn {
  border: none;
  cursor: pointer;
  font-weight: 900;
}

.attach-btn {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 13px;
  color: #6c5ce7;
  background: #f3f0ff;
  font-size: 18px;
}

.composer-input {
  min-height: 42px;
  max-height: 96px;
  resize: none;
  border: 1px solid #eceef3;
  border-radius: 14px;
  outline: none;
  padding: 11px 14px;
  color: #202633;
  background: #fbfcfe;
  font-size: 14px;
  line-height: 1.45;
}

.composer-input:focus {
  border-color: #7c4dff;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(124, 77, 255, 0.08);
}

.send-btn {
  height: 42px;
  min-width: 86px;
  border-radius: 13px;
  color: #fff;
  background: linear-gradient(135deg, #8657ff, #596cff);
  box-shadow: 0 12px 22px rgba(108, 92, 231, 0.25);
  font-size: 14px;
}

.send-btn:disabled {
  cursor: not-allowed;
  background: #c8cbd3;
  box-shadow: none;
}

.task-panel {
  min-width: 0;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #eef0f5;
}

.task-content {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.task-summary-card {
  padding: 16px;
  border: 1px solid #eceef3;
  border-radius: 12px;
  background: #fbfcfe;
}

.task-type-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.type-chip {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
}

.remain {
  flex-shrink: 0;
  color: #8b93a2;
  font-size: 11px;
  font-weight: 800;
}

.task-title {
  margin: 0 0 10px;
  color: #111827;
  font-size: 17px;
  line-height: 1.35;
  font-weight: 900;
}

.reward {
  margin-bottom: 12px;
  color: #f17b2f;
  font-size: 24px;
  font-weight: 900;
}

.task-desc {
  margin: 0;
  color: #747d8f;
  font-size: 12px;
  line-height: 1.6;
  font-weight: 700;
}

.info-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.info-row {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 10px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eef0f5;
  font-size: 12px;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: #9aa1ae;
  font-weight: 800;
}

.info-value {
  min-width: 0;
  color: #343b4c;
  font-weight: 800;
}

.side-actions {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.side-btn {
  height: 40px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 900;
}

.side-btn.primary {
  color: #fff;
  background: #111827;
}

.side-btn.secondary {
  color: #3a4050;
  background: #f3f4f7;
}

@media (max-width: 1180px) {
  .chat-stage {
    grid-template-columns: 300px minmax(360px, 1fr);
  }

  .task-panel {
    display: none;
  }
}

@media (max-width: 860px) {
  .sidebar {
    width: 68px;
    min-width: 68px;
  }

  .brand-copy,
  .nav-label,
  .sidebar-section,
  .publish-btn {
    display: none;
  }

  .brand {
    justify-content: center;
    padding: 0;
  }

  .nav {
    padding: 14px 10px;
  }

  .nav-item {
    justify-content: center;
    padding: 0;
  }

  .nav-item::before {
    content: "•";
    color: currentColor;
    font-size: 20px;
  }

  .chat-stage {
    grid-template-columns: 280px minmax(0, 1fr);
  }
}

@media (max-width: 680px) {
  .chat-page {
    position: static;
    min-height: 100vh;
  }

  .sidebar {
    display: none;
  }

  .topbar {
    height: auto;
    align-items: stretch;
    flex-direction: column;
    padding: 12px;
  }

  .topbar-actions {
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .chat-stage {
    min-height: calc(100vh - 118px);
    grid-template-columns: 1fr;
  }

  .conversation-list.hidden {
    display: none;
  }

  .chat-main:not(.expanded) {
    display: none;
  }

  .mobile-back {
    width: 32px;
    height: 32px;
    display: grid;
    place-items: center;
    flex-shrink: 0;
    border: none;
    border-radius: 10px;
    color: #6d7280;
    background: #f3f4f7;
    cursor: pointer;
    font-size: 22px;
  }

  .chat-actions {
    display: none;
  }

  .bubble-wrap {
    max-width: 82%;
  }

  .composer {
    grid-template-columns: auto 1fr auto;
  }

  .emoji-btn {
    display: none;
  }
}
</style>
