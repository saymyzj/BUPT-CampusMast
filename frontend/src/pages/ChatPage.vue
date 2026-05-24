<template>
  <div class="chat-page">
    <section class="chat-shell">
      <aside class="conversation-panel">
        <header class="panel-title-block">
          <h1>消息中心</h1>
          <p>{{ visibleConversations.length }} 个任务会话</p>
        </header>

        <div class="tabs" role="tablist">
          <button
            type="button"
            :class="{ active: activeTab === 'all' }"
            @click="activeTab = 'all'"
          >
            聊天消息
            <span v-if="chatUnreadCount">{{ formatBadge(chatUnreadCount) }}</span>
          </button>
          <button
            type="button"
            :class="{ active: activeTab === 'unread' }"
            @click="activeTab = 'unread'"
          >
            未读提醒
            <span v-if="chatUnreadCount">{{ formatBadge(chatUnreadCount) }}</span>
          </button>
        </div>

        <label class="search-field">
          <AppIcon name="search" />
          <input v-model.trim="keyword" type="search" placeholder="搜索会话或联系人" />
        </label>

        <div class="conversation-scroll">
          <div v-if="loading" class="empty-state">会话加载中...</div>
          <div v-else-if="error" class="empty-state error">{{ error }}</div>
          <div v-else-if="filteredConversations.length === 0" class="empty-state">
            <strong>暂无聊天会话</strong>
            <span>接单或任务被接取后，会在这里显示真实会话。</span>
          </div>

          <template v-else>
            <button
              v-for="conversation in filteredConversations"
              :key="conversation.id"
              type="button"
              class="conversation-card"
              :class="{ active: activeConv?.id === conversation.id }"
              @click="openConv(conversation)"
            >
              <span class="avatar-wrap">
                <span class="avatar" :style="{ background: avatarGradient(conversation) }">
                  {{ partnerInitial(conversation) }}
                </span>
                <span v-if="conversation.unreadCount > 0" class="online-dot"></span>
              </span>

              <span class="conversation-main">
                <span class="conversation-row">
                  <strong>{{ partnerName(conversation) }}</strong>
                  <small>{{ lastMessageTime(conversation) }}</small>
                </span>
                <span class="conversation-task">任务：{{ taskTitle(conversation) }}</span>
                <span class="conversation-preview">{{ conversationPreview(conversation) }}</span>
              </span>

              <span v-if="conversation.unreadCount > 0" class="unread-dot">
                {{ formatBadge(conversation.unreadCount) }}
              </span>
            </button>
          </template>
        </div>

        <footer class="conversation-footer">
          <AppIcon name="bell" />
          <span>暂无更多会话</span>
          <RouterLink to="/tasks">去任务大厅</RouterLink>
        </footer>
      </aside>

      <main class="message-panel">
        <div v-if="!activeConv" class="message-empty">
          <strong>选择一个会话</strong>
          <span>在这里和对方确认任务细节、交付时间和地点。</span>
        </div>

        <template v-else>
          <header class="message-header">
            <div class="participant">
              <span class="large-avatar" :style="{ background: activeAvatarGradient }">
                {{ activePartnerInitial }}
              </span>
              <div class="participant-copy">
                <div class="participant-line">
                  <strong>{{ activePartnerName }}</strong>
                  <span class="presence"><i></i>在线</span>
                </div>
                <p>{{ activePartnerMeta }}</p>
              </div>
            </div>

            <div class="task-context">
              <span>{{ activeTaskStatusText }}</span>
              <strong>{{ activeTask?.title || "任务会话" }}</strong>
            </div>

            <div class="header-actions">
              <button type="button" class="task-button" @click="goTaskDetail">查看任务</button>
              <button type="button" class="icon-button" aria-label="更多操作">
                <AppIcon name="more" />
              </button>
            </div>
          </header>

          <section ref="messageBodyRef" class="message-scroll">
            <div class="day-divider"><span>{{ activeDateLabel }}</span></div>

            <div v-if="messageLoading" class="empty-state">消息加载中...</div>
            <div v-else-if="messageError" class="empty-state error">{{ messageError }}</div>
            <div v-else-if="messages.length === 0" class="empty-state">
              <strong>暂无消息</strong>
              <span>发送第一条消息，和对方确认任务细节。</span>
            </div>

            <article
              v-for="message in messages"
              :key="message.id"
              class="message-row"
              :class="{ mine: message.senderId === userId }"
            >
              <span v-if="message.senderId !== userId" class="mini-avatar" :style="{ background: activeAvatarGradient }">
                {{ activePartnerInitial }}
              </span>
              <div class="bubble-group">
                <div class="bubble">{{ message.content }}</div>
                <time>{{ formatClock(message.createdAt) }}</time>
              </div>
              <span v-if="message.senderId === userId" class="mini-avatar mine-avatar">
                {{ currentInitial }}
              </span>
            </article>
          </section>

          <form class="composer" @submit.prevent="sendMessage">
            <div class="composer-tools" aria-hidden="true">
              <AppIcon name="smile" />
            </div>
            <textarea
              v-model="newMessage"
              rows="1"
              maxlength="500"
              placeholder="输入消息..."
              @keydown.enter.exact.prevent="sendMessage"
            ></textarea>
            <button type="submit" :disabled="sending || !newMessage.trim()">
              {{ sending ? "发送中" : "发送" }}
            </button>
          </form>
        </template>
      </main>

      <aside class="notification-panel">
        <header class="notice-head">
          <h2>最新通知</h2>
          <button
            v-if="notificationUnreadCount > 0"
            type="button"
            :disabled="markingAll"
            @click="handleMarkAllNotifications"
          >
            {{ markingAll ? "处理中" : "全部已读" }}
          </button>
        </header>

        <div class="notice-scroll">
          <div v-if="notificationLoading" class="empty-state">通知加载中...</div>
          <div v-else-if="notificationError" class="empty-state error">{{ notificationError }}</div>
          <div v-else-if="notifications.length === 0" class="empty-state">
            <strong>暂无通知</strong>
            <span>新的任务、聊天和系统通知会显示在这里。</span>
          </div>

          <template v-else>
            <button
              v-for="notice in notifications"
              :key="notice.id"
              type="button"
              class="notice-card"
              :class="{ unread: !notice.isRead }"
              @click="openNotification(notice)"
            >
              <span class="notice-icon" :class="notificationClass(notice.type)">
                <AppIcon :name="notificationIcon(notice.type)" />
              </span>
              <span class="notice-copy">
                <span class="notice-title-row">
                  <strong>{{ notice.title }}</strong>
                  <time>{{ formatNoticeTime(notice.createdAt) }}</time>
                </span>
                <span class="notice-body">{{ notice.body }}</span>
                <span class="notice-action">{{ notice.relatedTaskId ? "查看任务" : "查看详情" }}</span>
              </span>
              <i v-if="!notice.isRead" class="notice-dot"></i>
            </button>
          </template>
        </div>

        <footer class="tip-card">
          <span class="notice-icon tip">
            <AppIcon name="bell" />
          </span>
          <div>
            <strong>小贴士</strong>
            <p>及时查看消息和通知，不错过任务进度和重要信息。</p>
          </div>
        </footer>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import {
  createTaskChatMessage,
  listChatConversations,
  listTaskChatMessages,
  markConversationRead,
} from "@/api/modules/chat";
import { listNotifications, markAllNotificationsRead, markNotificationRead } from "@/api/modules/notification";
import { getTaskById } from "@/api/modules/task";
import AppIcon from "@/components/ui/AppIcon.vue";
import { useAuthStore } from "@/stores/auth";
import { useNotificationStore } from "@/stores/notification";
import { CATEGORY_COLORS } from "@/types/map";
import { isTaskVisible } from "@/utils/taskVisibility";
import type {
  ChatConversation,
  ChatMessage,
  Notification,
  NotificationType,
  TaskCategory,
  TaskDetail,
  UserSummary,
} from "@/types/api";

type ConversationTab = "all" | "unread";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();

const conversations = ref<ChatConversation[]>([]);
const taskById = ref<Record<string, TaskDetail>>({});
const messages = ref<ChatMessage[]>([]);
const notifications = ref<Notification[]>([]);

const activeConv = ref<ChatConversation | null>(null);
const activeTab = ref<ConversationTab>("all");
const keyword = ref("");
const newMessage = ref("");
const loading = ref(false);
const messageLoading = ref(false);
const notificationLoading = ref(false);
const sending = ref(false);
const markingAll = ref(false);
const error = ref("");
const messageError = ref("");
const notificationError = ref("");
const notificationUnreadCount = ref(0);
const messageBodyRef = ref<HTMLElement | null>(null);

const hiddenConversationStatuses = new Set(["CANCELLED", "EXPIRED", "CLOSED_BY_ADMIN"]);
const userId = computed(() => authStore.userId ?? "");
const currentInitial = computed(() => initialOf(authStore.currentUser?.nickname || "我"));

const visibleConversations = computed(() =>
  conversations.value.filter((conversation) => {
    if (conversation.taskStatus && hiddenConversationStatuses.has(conversation.taskStatus)) return false;
    const task = taskById.value[conversation.taskId];
    return task ? isTaskVisible(task) : true;
  }),
);

const filteredConversations = computed(() => {
  const q = keyword.value.trim().toLowerCase();
  return visibleConversations.value.filter((conversation) => {
    if (activeTab.value === "unread" && conversation.unreadCount <= 0) return false;
    if (!q) return true;
    const task = taskById.value[conversation.taskId];
    return [
      partnerName(conversation),
      task?.title,
      task?.description,
      task?.locationDetail,
      conversation.latestMessage?.content,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(q));
  });
});

const chatUnreadCount = computed(() =>
  visibleConversations.value.reduce((sum, conversation) => sum + conversation.unreadCount, 0),
);

const activeTask = computed(() => (activeConv.value ? taskById.value[activeConv.value.taskId] ?? null : null));
const activePartner = computed(() => (activeTask.value ? getPartner(activeTask.value) : null));
const activePartnerName = computed(() => activePartner.value?.nickname || "任务会话");
const activePartnerInitial = computed(() => initialOf(activePartnerName.value));
const activePartnerMeta = computed(() => {
  const credit = activePartner.value?.overallCreditScore;
  return credit ? `信用分 ${credit} · 好评率待统计` : "任务参与方";
});
const activeAvatarGradient = computed(() => avatarGradient(activeConv.value));
const activeTaskStatusText = computed(() => {
  if (!activeTask.value) return "进行中";
  return taskStatusText(activeTask.value.status);
});
const activeDateLabel = computed(() => {
  const first = messages.value[0]?.createdAt;
  return first ? formatDayLabel(first) : "今天";
});

watch(chatUnreadCount, (count) => notificationStore.setChatUnreadCount(count), { immediate: true });
watch(notificationUnreadCount, (count) => notificationStore.setNotificationUnreadCount(count), { immediate: true });

function initialOf(value?: string | null) {
  return value?.trim().charAt(0) || "?";
}

function formatBadge(count: number) {
  return count > 99 ? "99+" : String(count);
}

function taskTitle(conversation: ChatConversation) {
  return taskById.value[conversation.taskId]?.title || "任务会话";
}

function categoryColor(category?: TaskCategory) {
  return category ? CATEGORY_COLORS[category] ?? "#6f835f" : "#6f835f";
}

function getPartner(task: TaskDetail): UserSummary | null {
  if (task.requester.id === userId.value) return task.helper ?? null;
  return task.requester;
}

function partnerName(conversation: ChatConversation) {
  const task = taskById.value[conversation.taskId];
  if (!task) return "任务会话";
  return getPartner(task)?.nickname || "等待接单";
}

function partnerInitial(conversation: ChatConversation) {
  return initialOf(partnerName(conversation));
}

function conversationPreview(conversation: ChatConversation) {
  return conversation.latestMessage?.content || taskById.value[conversation.taskId]?.description || "暂无消息";
}

function avatarGradient(conversation: ChatConversation | null) {
  const task = conversation ? taskById.value[conversation.taskId] : activeTask.value;
  const base = categoryColor(task?.category);
  return `linear-gradient(135deg, ${base}, #d8c4a5)`;
}

function lastMessageTime(conversation: ChatConversation) {
  return conversation.latestMessage ? formatNoticeTime(conversation.latestMessage.createdAt) : "";
}

function formatClock(iso: string) {
  const d = new Date(iso);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function formatNoticeTime(iso: string) {
  const d = new Date(iso);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) return formatClock(iso);
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (d.toDateString() === yesterday.toDateString()) return "昨天";
  return `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}`;
}

function formatDayLabel(iso: string) {
  const d = new Date(iso);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) return `今天 ${formatClock(iso)}`;
  return `${d.getMonth() + 1}月${d.getDate()}日 ${formatClock(iso)}`;
}

function taskStatusText(status?: string) {
  const statusMap: Record<string, string> = {
    PENDING: "待接单",
    IN_PROGRESS: "进行中",
    PENDING_REVIEW: "待验收",
    COMPLETED: "已完成",
    DISPUTED: "争议中",
  };
  return status ? statusMap[status] ?? "进行中" : "进行中";
}

function notificationIcon(type: NotificationType) {
  const iconMap: Partial<Record<NotificationType, string>> = {
    TASK_ACCEPTED: "check-circle",
    TASK_SUBMITTED: "upload",
    CHAT_MESSAGE: "message",
    SYSTEM_NOTICE: "shield",
    TASK_CONFIRMED: "star",
    MODERATION_REVIEW: "shield",
  };
  return iconMap[type] || "bell";
}

function notificationClass(type: NotificationType) {
  if (type === "TASK_ACCEPTED" || type === "TASK_CONFIRMED") return "green";
  if (type === "TASK_SUBMITTED" || type === "CHAT_MESSAGE") return "blue";
  if (type === "TASK_REJECTED" || type === "TASK_CANCELLED" || type === "TASK_DISPUTED") return "orange";
  if (type === "MODERATION_REVIEW") return "purple";
  return "green";
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
    const notClosed = all.filter((conversation) => !conversation.taskStatus || !hiddenConversationStatuses.has(conversation.taskStatus));
    conversations.value = notClosed;

    const taskIds = Array.from(new Set(notClosed.map((conversation) => conversation.taskId)));
    const results = await Promise.allSettled(taskIds.map((taskId) => getTaskById(taskId)));
    const nextTasks: Record<string, TaskDetail> = {};
    results.forEach((result) => {
      if (result.status === "fulfilled" && isTaskVisible(result.value)) {
        nextTasks[result.value.id] = result.value;
      }
    });
    taskById.value = { ...taskById.value, ...nextTasks };
    const visibleTaskIds = new Set(Object.keys(nextTasks));
    conversations.value = notClosed.filter((conversation) => visibleTaskIds.has(conversation.taskId));

    await openInitialConversation();
  } catch {
    error.value = "会话加载失败";
  } finally {
    loading.value = false;
  }
}

async function openInitialConversation() {
  const queryTaskId = typeof route.query.taskId === "string" ? route.query.taskId : "";
  const target =
    visibleConversations.value.find((conversation) => queryTaskId && conversation.taskId === queryTaskId) ||
    visibleConversations.value[0];
  if (target && activeConv.value?.id !== target.id) {
    await openConv(target);
  }
}

async function openConv(conversation: ChatConversation) {
  activeConv.value = conversation;
  messages.value = [];
  messageError.value = "";
  messageLoading.value = true;
  try {
    const [, result] = await Promise.all([
      ensureTaskDetail(conversation.taskId),
      listTaskChatMessages(conversation.taskId, { page: 1, limit: 80 }),
    ]);
    messages.value = result.data;
    const lastMessageId = messages.value[messages.value.length - 1]?.id;
    if (lastMessageId && conversation.unreadCount > 0) {
      await markConversationRead(conversation.id, { lastReadMessageId: lastMessageId });
    }
    conversation.unreadCount = 0;
  } catch {
    messageError.value = "消息加载失败";
  } finally {
    messageLoading.value = false;
  }
  await nextTick();
  scrollToBottom();
}

async function loadNotifications() {
  notificationLoading.value = true;
  notificationError.value = "";
  try {
    const result = await listNotifications({ page: 1, limit: 6 });
    notifications.value = result.data;
    notificationUnreadCount.value = result.meta.unreadCount ?? result.data.filter((notice) => !notice.isRead).length;
  } catch {
    notificationError.value = "通知加载失败";
  } finally {
    notificationLoading.value = false;
  }
}

async function sendMessage() {
  if (!activeConv.value || !newMessage.value.trim() || sending.value) return;
  const content = newMessage.value.trim();
  sending.value = true;
  try {
    const message = await createTaskChatMessage(activeConv.value.taskId, { content });
    messages.value.push(message);
    activeConv.value.latestMessage = message;
    newMessage.value = "";
    await nextTick();
    scrollToBottom();
  } finally {
    sending.value = false;
  }
}

function scrollToBottom() {
  const body = messageBodyRef.value;
  if (body) body.scrollTop = body.scrollHeight;
}

async function handleMarkAllNotifications() {
  markingAll.value = true;
  try {
    await markAllNotificationsRead();
    notifications.value.forEach((notice) => {
      notice.isRead = true;
    });
    notificationUnreadCount.value = 0;
  } finally {
    markingAll.value = false;
  }
}

async function openNotification(notice: Notification) {
  if (!notice.isRead) {
    try {
      await markNotificationRead(notice.id);
      notice.isRead = true;
      notificationUnreadCount.value = Math.max(0, notificationUnreadCount.value - 1);
    } catch {
      // Ignore read-sync failure; navigation should still work.
    }
  }
  if (notice.relatedTaskId) await router.push(`/tasks/${notice.relatedTaskId}`);
}

function goTaskDetail() {
  if (activeConv.value) router.push(`/tasks/${activeConv.value.taskId}`);
}

onMounted(async () => {
  await Promise.all([loadConversations(), loadNotifications()]);
});
</script>

<style scoped>
.chat-page {
  min-height: calc(100vh - 62px);
  padding: 18px 32px 26px;
  background: #fbfaf7;
  color: #22241f;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
}

button,
input,
textarea {
  font: inherit;
}

button {
  cursor: pointer;
}

.chat-shell {
  width: min(1440px, 100%);
  height: calc(100vh - 106px);
  min-height: 620px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 370px minmax(520px, 1fr) 340px;
  gap: 14px;
}

.conversation-panel,
.message-panel,
.notification-panel {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid #ece9e2;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 14px 36px rgba(55, 49, 40, 0.06);
  overflow: hidden;
}

.panel-title-block {
  padding: 24px 22px 12px;
}

.panel-title-block h1,
.notice-head h2 {
  margin: 0;
  color: #151713;
  font-size: 20px;
  font-weight: 900;
}

.panel-title-block p {
  margin: 6px 0 0;
  color: #85877f;
  font-size: 12px;
  font-weight: 700;
}

.tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  margin: 8px 20px 14px;
  padding: 4px;
  border: 1px solid #ece9e2;
  border-radius: 7px;
  background: #f4f3ef;
}

.tabs button {
  position: relative;
  min-width: 0;
  height: 36px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #777a72;
  font-size: 13px;
  font-weight: 800;
}

.tabs button.active {
  color: #60754e;
  background: #fff;
  box-shadow: 0 5px 14px rgba(56, 50, 40, 0.06);
}

.tabs span {
  position: absolute;
  top: -6px;
  right: 14px;
  min-width: 17px;
  height: 17px;
  display: grid;
  place-items: center;
  padding: 0 5px;
  border-radius: 999px;
  color: #fff;
  background: #ef4e5b;
  font-size: 10px;
  font-weight: 900;
}

.search-field {
  height: 38px;
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0 20px 12px;
  padding: 0 13px;
  border: 1px solid #ece9e2;
  border-radius: 7px;
  background: #fff;
  color: #9da098;
}

.search-field input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  color: #2a2b27;
  font-size: 13px;
}

.conversation-scroll,
.notice-scroll,
.message-scroll {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
}

.conversation-scroll {
  padding: 0 18px 14px;
}

.conversation-card {
  position: relative;
  width: 100%;
  min-width: 0;
  display: grid;
  grid-template-columns: 45px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 12px 11px;
  border: 0;
  border-bottom: 1px solid #efede7;
  border-radius: 7px;
  background: transparent;
  color: inherit;
  text-align: left;
  transition: background 0.18s ease, box-shadow 0.18s ease;
}

.conversation-card:hover,
.conversation-card.active {
  background: #f4f5ee;
  box-shadow: inset 3px 0 0 #6f835f;
}

.avatar-wrap {
  position: relative;
  width: 45px;
  height: 45px;
}

.avatar,
.large-avatar,
.mini-avatar {
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  font-weight: 900;
  overflow: hidden;
}

.avatar {
  width: 45px;
  height: 45px;
  font-size: 15px;
}

.online-dot {
  position: absolute;
  right: 2px;
  bottom: 2px;
  width: 9px;
  height: 9px;
  border: 2px solid #fff;
  border-radius: 50%;
  background: #58b45f;
}

.conversation-main {
  min-width: 0;
  display: grid;
  gap: 5px;
}

.conversation-row,
.notice-title-row,
.participant-line {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.conversation-row strong,
.conversation-task,
.conversation-preview,
.notice-title-row strong,
.notice-body,
.task-context strong,
.participant-copy p,
.participant-line strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation-row strong {
  flex: 1;
  color: #23241f;
  font-size: 14px;
  font-weight: 900;
}

.conversation-row small {
  flex: 0 0 auto;
  color: #aaa79f;
  font-size: 12px;
}

.conversation-task,
.conversation-preview {
  display: block;
  color: #85877f;
  font-size: 12px;
  line-height: 1.35;
}

.conversation-preview {
  color: #73766f;
}

.unread-dot {
  position: absolute;
  right: 10px;
  bottom: 16px;
  min-width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  padding: 0 5px;
  border-radius: 999px;
  background: #ef4e5b;
  color: #fff;
  font-size: 10px;
  font-weight: 900;
}

.conversation-footer {
  margin: 10px 20px 20px;
  min-height: 92px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  border: 1px dashed #dedbd3;
  border-radius: 7px;
  color: #8b8d86;
  font-size: 13px;
}

.conversation-footer .app-icon {
  color: #a3a69f;
}

.conversation-footer a {
  color: #617650;
  text-decoration: none;
  font-weight: 800;
}

.message-panel {
  background: rgba(255, 255, 255, 0.9);
}

.message-empty,
.empty-state {
  min-height: 150px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  padding: 24px;
  color: #8a8d86;
  text-align: center;
  font-size: 13px;
  line-height: 1.5;
}

.message-empty {
  flex: 1;
}

.empty-state strong,
.message-empty strong {
  color: #242620;
  font-size: 15px;
  font-weight: 900;
}

.empty-state.error {
  color: #b25747;
}

.message-header {
  height: 82px;
  min-height: 82px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(190px, 300px) auto;
  gap: 16px;
  align-items: center;
  padding: 0 22px 0 24px;
  border-bottom: 1px solid #ece9e2;
  background: rgba(255, 255, 255, 0.92);
}

.participant {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 13px;
}

.large-avatar {
  width: 49px;
  height: 49px;
  flex: 0 0 auto;
  font-size: 17px;
}

.participant-copy {
  min-width: 0;
}

.participant-line strong {
  color: #151713;
  font-size: 16px;
  font-weight: 900;
}

.presence {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #5b9d59;
  font-size: 12px;
  font-weight: 800;
}

.presence i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #58b45f;
}

.participant-copy p {
  margin: 5px 0 0;
  color: #85877f;
  font-size: 12px;
}

.task-context {
  min-width: 0;
  padding-left: 16px;
  border-left: 1px solid #ece9e2;
}

.task-context span {
  display: block;
  color: #6f835f;
  font-size: 12px;
  font-weight: 900;
}

.task-context strong {
  display: block;
  margin-top: 5px;
  color: #2d2f29;
  font-size: 13px;
  font-weight: 900;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-button,
.icon-button {
  height: 38px;
  border: 1px solid #ece9e2;
  border-radius: 7px;
  background: #f4f5ee;
  color: #60754e;
  font-weight: 900;
}

.task-button {
  padding: 0 18px;
  white-space: nowrap;
}

.icon-button {
  width: 38px;
  display: grid;
  place-items: center;
  background: #fff;
  color: #6f706a;
}

.message-scroll {
  padding: 18px 24px 10px;
  background:
    linear-gradient(rgba(251, 250, 247, 0.82), rgba(251, 250, 247, 0.82)),
    radial-gradient(circle at 18% 0, rgba(111, 131, 95, 0.08), transparent 34%);
}

.day-divider {
  display: flex;
  justify-content: center;
  margin-bottom: 18px;
}

.day-divider span {
  padding: 5px 12px;
  border-radius: 7px;
  background: #f1f0eb;
  color: #85877f;
  font-size: 12px;
  font-weight: 800;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 15px;
}

.message-row.mine {
  justify-content: flex-end;
}

.mini-avatar {
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  background: linear-gradient(135deg, #d8c4a5, #8aa078);
  font-size: 11px;
}

.mine-avatar {
  background: linear-gradient(135deg, #e5c5a7, #8aa078);
}

.bubble-group {
  max-width: min(520px, 68%);
}

.bubble {
  padding: 11px 14px;
  border: 1px solid #e9e6df;
  border-radius: 7px;
  background: #fff;
  color: #2c2d29;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: 0 8px 20px rgba(55, 49, 40, 0.05);
}

.message-row.mine .bubble {
  border-color: #e7eddf;
  background: #eef3e7;
  color: #3a4532;
}

.bubble-group time {
  display: block;
  margin-top: 5px;
  padding: 0 3px;
  color: #999b94;
  font-size: 11px;
}

.message-row.mine .bubble-group time {
  text-align: right;
}

.composer {
  min-height: 58px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
  border-top: 1px solid #ece9e2;
  background: #fff;
}

.composer-tools {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  color: #7f8279;
}

.composer textarea {
  min-height: 37px;
  max-height: 86px;
  resize: none;
  padding: 9px 12px;
  border: 1px solid #ece9e2;
  border-radius: 7px;
  outline: 0;
  background: #fff;
  color: #2a2b27;
  font-size: 13px;
  line-height: 1.45;
}

.composer textarea:focus {
  border-color: rgba(111, 131, 95, 0.45);
  box-shadow: 0 0 0 4px rgba(111, 131, 95, 0.08);
}

.composer button {
  height: 37px;
  min-width: 58px;
  border: 0;
  border-radius: 7px;
  background: #6f835f;
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  box-shadow: 0 8px 18px rgba(111, 131, 95, 0.18);
}

.composer button:disabled {
  cursor: not-allowed;
  background: #c8c9c2;
  box-shadow: none;
}

.notification-panel {
  padding: 0 14px 14px;
}

.notice-head {
  min-height: 62px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 4px;
}

.notice-head h2 {
  font-size: 17px;
}

.notice-head button {
  border: 0;
  background: transparent;
  color: #60754e;
  font-size: 12px;
  font-weight: 900;
}

.notice-scroll {
  display: grid;
  align-content: start;
  gap: 9px;
  padding-right: 2px;
}

.notice-card {
  position: relative;
  width: 100%;
  min-width: 0;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 12px;
  padding: 14px 12px;
  border: 1px solid #ece9e2;
  border-radius: 7px;
  background: #fff;
  color: inherit;
  text-align: left;
  box-shadow: 0 8px 18px rgba(55, 49, 40, 0.04);
}

.notice-card:hover {
  background: #fdfcf8;
}

.notice-card.unread {
  border-color: #e6eddd;
}

.notice-icon {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: #6f835f;
  font-size: 17px;
}

.notice-icon.green,
.notice-icon.tip {
  background: #718861;
}

.notice-icon.blue {
  background: #4e86dc;
}

.notice-icon.orange {
  background: #f08a3f;
}

.notice-icon.purple {
  background: #9272d2;
}

.notice-copy {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.notice-title-row strong {
  flex: 1;
  color: #252722;
  font-size: 14px;
  font-weight: 900;
}

.notice-title-row time {
  flex: 0 0 auto;
  color: #aaa79f;
  font-size: 11px;
}

.notice-body {
  display: -webkit-box;
  white-space: normal;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  color: #74766f;
  font-size: 12px;
  line-height: 1.55;
}

.notice-action {
  color: #617650;
  font-size: 12px;
  font-weight: 900;
}

.notice-dot {
  position: absolute;
  right: 10px;
  top: 50%;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #ef4e5b;
  transform: translateY(-50%);
}

.tip-card {
  min-height: 78px;
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  margin-top: 10px;
  padding: 12px;
  border: 1px solid #e2e8d9;
  border-radius: 7px;
  background: #f0f4ea;
}

.tip-card strong {
  color: #3c4a33;
  font-size: 13px;
}

.tip-card p {
  margin: 4px 0 0;
  color: #65735c;
  font-size: 12px;
  line-height: 1.45;
}

@media (max-width: 1220px) {
  .chat-shell {
    grid-template-columns: 330px minmax(460px, 1fr);
  }

  .notification-panel {
    display: none;
  }
}

@media (max-width: 860px) {
  .chat-page {
    padding: 14px;
  }

  .chat-shell {
    height: auto;
    min-height: calc(100vh - 90px);
    grid-template-columns: 1fr;
  }

  .message-header {
    grid-template-columns: minmax(0, 1fr);
    height: auto;
    padding: 14px;
  }

  .task-context {
    padding: 0;
    border-left: 0;
  }

  .conversation-panel {
    min-height: 420px;
  }
}
</style>
