/**
 * 文件说明：
 * 这是前端 WebSocket 连接的基础封装。
 * 它为通知与任务内聊天提供统一入口。
 */
import { ref, onMounted, onUnmounted } from "vue";

export function useWebSocket(path: string) {
  const socket = ref<WebSocket | null>(null);
  const isConnected = ref(false);

  function connect() {
    const base = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:9000/ws";
    const token = sessionStorage.getItem("campusmast.accessToken") ?? "";
    socket.value = new WebSocket(`${base}${path}?accessToken=${token}`);

    socket.value.onopen = () => {
      isConnected.value = true;
    };

    socket.value.onclose = () => {
      isConnected.value = false;
    };
  }

  function disconnect() {
    socket.value?.close();
    socket.value = null;
  }

  onMounted(connect);
  onUnmounted(disconnect);

  return { socket, isConnected, connect, disconnect };
}
