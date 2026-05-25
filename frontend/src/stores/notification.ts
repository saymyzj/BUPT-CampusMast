/**
 * 文件说明：
 * 这是通知状态仓库。
 * 当前先预留未读数和通知列表状态，A 同学后续可以把 HTTP 拉取与 WebSocket 推送
 * 都接入这里，避免散落在多个页面里。
 */
import { defineStore } from "pinia";
import { listChatConversations } from "@/api/modules/chat";
import { listNotifications } from "@/api/modules/notification";

type RealtimeMessage = {
  event: string;
  payload?: Record<string, unknown>;
};

export const useNotificationStore = defineStore("notification", {
  state: () => ({
    chatUnreadCount: 0,
    notificationUnreadCount: 0,
    items: [] as Array<Record<string, unknown>>,
    socket: null as WebSocket | null,
    realtimeUserId: "" as string,
    reconnectTimer: 0,
  }),
  getters: {
    unreadCount: (state) => state.notificationUnreadCount,
    totalUnreadCount: (state) => state.chatUnreadCount + state.notificationUnreadCount,
  },
  actions: {
    setUnreadCount(count: number) {
      this.notificationUnreadCount = count;
    },
    setChatUnreadCount(count: number) {
      this.chatUnreadCount = count;
    },
    setNotificationUnreadCount(count: number) {
      this.notificationUnreadCount = count;
    },
    setItems(items: Array<Record<string, unknown>>) {
      this.items = items;
    },
    connectRealtime(userId: string) {
      if (!userId) return;
      if (this.socket && this.realtimeUserId === userId) return;
      this.disconnectRealtime();
      this.realtimeUserId = userId;
      const base = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:9000/ws";
      const token = sessionStorage.getItem("campusmast.accessToken") ?? "";
      const socket = new WebSocket(`${base}/notification:${userId}?accessToken=${encodeURIComponent(token)}`);
      this.socket = socket;
      socket.onmessage = (event) => this.handleRealtimeMessage(event);
      socket.onclose = () => {
        if (this.realtimeUserId === userId) {
          this.socket = null;
          window.clearTimeout(this.reconnectTimer);
          this.reconnectTimer = window.setTimeout(() => this.connectRealtime(userId), 1800);
        }
      };
    },
    disconnectRealtime() {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = 0;
      this.realtimeUserId = "";
      if (this.socket) {
        this.socket.onclose = null;
        this.socket.close();
        this.socket = null;
      }
    },
    handleRealtimeMessage(event: MessageEvent) {
      let message: RealtimeMessage;
      try {
        message = JSON.parse(event.data) as RealtimeMessage;
      } catch {
        return;
      }
      const payload = message.payload ?? {};
      if (message.event === "NOTIFICATION_CREATED") {
        this.items = [payload, ...this.items];
        this.notificationUnreadCount += 1;
        return;
      }
      if (message.event === "UNREAD_SYNC") {
        const count = Number(payload.unreadCount ?? 0);
        if (payload.scope === "chat") {
          this.chatUnreadCount = count;
        } else {
          this.notificationUnreadCount = count;
        }
      }
    },
    async refreshUnreadCounts() {
      const [conversations, notifications] = await Promise.all([
        listChatConversations().catch(() => []),
        listNotifications({ page: 1, limit: 1 }).catch(() => null),
      ]);
      this.chatUnreadCount = conversations.reduce((sum, item) => sum + item.unreadCount, 0);
      if (notifications) {
        this.notificationUnreadCount =
          notifications.meta.unreadCount ?? notifications.data.filter((item) => !item.isRead).length;
      }
    },
  },
});
