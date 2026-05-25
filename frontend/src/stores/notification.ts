/**
 * 文件说明：
 * 这是通知状态仓库。
 * 当前先预留未读数和通知列表状态，A 同学后续可以把 HTTP 拉取与 WebSocket 推送
 * 都接入这里，避免散落在多个页面里。
 */
import { defineStore } from "pinia";
import { listChatConversations } from "@/api/modules/chat";
import { listNotifications } from "@/api/modules/notification";

export const useNotificationStore = defineStore("notification", {
  state: () => ({
    chatUnreadCount: 0,
    notificationUnreadCount: 0,
    items: [] as Array<Record<string, unknown>>,
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

