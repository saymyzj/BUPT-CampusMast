<template>
  <div class="page-root">
    <section class="page-container">
      <div class="page-header">
        <div>
          <h1 class="page-title">通知中心</h1>
          <p class="page-subtitle">查看系统通知和任务事件</p>
        </div>
        <button v-if="hasUnread" class="btn btn-secondary" :disabled="markingAll" @click="handleMarkAll">
          {{ markingAll ? '处理中...' : '全部已读' }}
        </button>
      </div>

      <div v-if="loading" class="state-box">加载中...</div>
      <div v-else-if="error" class="state-box state-error">{{ error }}</div>
      <div v-else-if="notifications.length === 0" class="state-box">暂无通知</div>

      <div v-else class="notif-list">
        <div v-for="n in notifications" :key="n.id" class="notif-item" :class="{ unread: !n.isRead }" @click="handleClick(n)">
          <div class="notif-left">
            <span class="notif-dot" :class="{ active: !n.isRead }"></span>
            <div>
              <p class="notif-title">{{ n.title }}</p>
              <p class="notif-body">{{ n.body }}</p>
            </div>
          </div>
          <div class="notif-right">
            <span class="notif-type" :class="`nt-${n.type}`">{{ typeLabel(n.type) }}</span>
            <span class="notif-time">{{ formatTime(n.createdAt) }}</span>
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
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { listNotifications, markNotificationRead, markAllNotificationsRead } from "@/api/modules/notification";
import type { Notification, NotificationType } from "@/types/api";

const router = useRouter();
const notifications = ref<Notification[]>([]);
const loading = ref(false); const error = ref("");
const page = ref(1); const limit = 20; const total = ref(0); const totalPages = ref(1);
const markingAll = ref(false);
const hasUnread = computed(() => notifications.value.some((n) => !n.isRead));

const L: Record<string, string> = {
  TASK_ACCEPTED: "📥 有人接单", TASK_SUBMITTED: "✅ 待验收", TASK_CONFIRMED: "💵 已结算",
  TASK_REJECTED: "↩️ 验收被拒", TASK_CANCELLED: "❌ 已取消", TASK_DISPUTED: "⚠️ 争议中",
  DISPUTE_RESOLVED: "🛡️ 争议解决", CHAT_MESSAGE: "💬 新消息", CHAT_READ: "已读",
  SYSTEM_NOTICE: "📢 系统公告", MODERATION_REVIEW: "🔍 审核通知",
};
function typeLabel(t: NotificationType) { return L[t] ?? t; }
function formatTime(iso: string) {
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

async function fetchAll() {
  loading.value = true; error.value = "";
  try {
    const r = await listNotifications({ page: page.value, limit });
    notifications.value = r.data; total.value = r.meta.total; totalPages.value = Math.max(1, Math.ceil(r.meta.total / limit));
  } catch (err: any) { error.value = err?.response?.data?.error?.message || "加载失败"; } finally { loading.value = false; }
}
async function handleClick(n: Notification) {
  if (!n.isRead) { try { await markNotificationRead(n.id); n.isRead = true; } catch { /* */ } }
  if (n.relatedTaskId) router.push(`/tasks/${n.relatedTaskId}`);
}
async function handleMarkAll() {
  markingAll.value = true;
  try { await markAllNotificationsRead(); notifications.value.forEach((n) => { n.isRead = true; }); } catch { /* */ } finally { markingAll.value = false; }
}
function goPage(p: number) { page.value = p; fetchAll(); }
onMounted(fetchAll);
</script>

<style scoped>
.page-root {
  --blue-500: #2556a8; --blue-600: #1f478c; --blue-50: #edf3fb;
  --red-500: #b24a3a; --orange-500: #c67f2f; --green-500: #2f7a41; --purple-500: #7c3aed;
  --gray-50: #f6f1e6; --gray-100: #ece3d2; --gray-300: #b9ad95; --gray-600: #50493f; --gray-800: #202735;
  --bg-start: #fbf7ef; --bg-end: #efe6d6;
  --shadow-sm: 0 2px 6px rgba(23,29,40,0.04); --shadow-md: 0 8px 20px rgba(23,29,40,0.07);
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
.page-container { position: relative; z-index: 1; padding: 40px 20px; max-width: 720px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; margin-bottom: 28px; }
.page-title { font-size: 32px; font-weight: 700; color: var(--gray-800); font-family: 'Nunito','Noto Sans SC',sans-serif; }
.page-subtitle { font-size: 15px; color: var(--gray-600); margin-top: 6px; }
.btn { padding: 10px 20px; font-size: 14px; font-weight: 600; border-radius: var(--radius); cursor: pointer; transition: all 0.25s; border: none; }
.btn-secondary { background: #fff; color: var(--blue-500); border: 1px solid var(--blue-500); }
.btn-secondary:hover:not(:disabled) { background: var(--blue-50); transform: translateY(-1px); box-shadow: 0 6px 16px rgba(37,86,168,0.1); }
.btn-secondary:disabled { opacity: 0.4; cursor: not-allowed; }

.state-box { text-align: center; padding: 80px 20px; color: var(--gray-600); font-size: 15px; }
.state-error { color: var(--red-500); background: #fff5f5; border-radius: var(--radius-lg); }

.notif-list { background: #faf7f1; border: 1px solid rgba(31,42,58,0.04); border-radius: var(--radius-lg); box-shadow: var(--shadow-md); overflow: hidden; }
.notif-item { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--gray-100); cursor: pointer; transition: background 0.2s; gap: 12px; }
.notif-item:last-child { border-bottom: none; }
.notif-item:hover { background: rgba(37,86,168,0.02); }
.notif-item.unread { background: var(--blue-50); }
.notif-left { display: flex; align-items: flex-start; gap: 10px; }
.notif-dot { width: 8px; height: 8px; border-radius: 50%; background: transparent; margin-top: 6px; flex-shrink: 0; }
.notif-dot.active { background: var(--blue-500); animation: pulse 2s ease infinite; }
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.5; }
}
.notif-title { font-size: 14px; font-weight: 600; color: var(--gray-800); }
.notif-body { font-size: 13px; color: var(--gray-600); margin-top: 2px; }
.notif-right { text-align: right; flex-shrink: 0; }
.notif-type { display: inline-block; padding: 2px 8px; border-radius: var(--radius-sm); font-size: 11px; font-weight: 600; margin-bottom: 4px; }
.nt-TASK_ACCEPTED, .nt-TASK_CONFIRMED { background: #dbeafe; color: #1e40af; }
.nt-TASK_SUBMITTED { background: #ede9fe; color: #6b21a8; }
.nt-TASK_REJECTED, .nt-TASK_DISPUTED { background: #fee2e2; color: #991b1b; }
.nt-TASK_CANCELLED, .nt-CHAT_READ { background: #f3f4f6; color: #374151; }
.nt-DISPUTE_RESOLVED { background: #d1fae5; color: #065f46; }
.nt-CHAT_MESSAGE { background: #fef3c7; color: #92400e; }
.nt-SYSTEM_NOTICE { background: #fce7f3; color: #be185d; }
.nt-MODERATION_REVIEW { background: #fff7ed; color: #c2410c; }
.notif-time { display: block; font-size: 11px; color: var(--gray-600); }

.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 32px; font-size: 14px; color: var(--gray-600); }
.pagination button { padding: 8px 18px; border: 1px solid var(--gray-100); border-radius: var(--radius); background: #fff; cursor: pointer; color: var(--gray-800); font-weight: 500; transition: all 0.25s; }
.pagination button:hover:not(:disabled) { border-color: var(--blue-500); color: var(--blue-500); transform: translateY(-1px); box-shadow: var(--shadow-sm); }
.pagination button:disabled { opacity: 0.35; cursor: not-allowed; }
.page-info { font-weight: 600; }
</style>
