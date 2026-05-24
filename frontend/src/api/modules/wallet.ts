/**
 * 文件说明：
 * 这是钱包模块的 API 封装占位文件。
 * A 同学后续应在这里继续维护余额、流水、充值、提现等请求，不要在页面里直接访问 axios。
 */
import apiClient from "@/api/client";

export async function fetchWalletBalance() {
  const response = await apiClient.get("/api/wallet/balance");
  return response.data;
}

