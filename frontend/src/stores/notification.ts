/**
 * 文件说明：
 * 这是通知状态仓库。
 * 当前先预留未读数和通知列表状态，A 同学后续可以把 HTTP 拉取与 WebSocket 推送
 * 都接入这里，避免散落在多个页面里。
 */
import { defineStore } from "pinia";

export const useNotificationStore = defineStore("notification", {
  state: () => ({
    unreadCount: 0,
    items: [] as Array<Record<string, unknown>>,
  }),
  actions: {
    setUnreadCount(count: number) {
      this.unreadCount = count;
    },
    setItems(items: Array<Record<string, unknown>>) {
      this.items = items;
    },
  },
});

