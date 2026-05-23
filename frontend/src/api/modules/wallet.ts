import apiClient from "@/api/client";
import type { Wallet, Transaction, TopUpRequest, WithdrawRequest, PaginationMeta } from "@/types/api";

export async function getWalletBalance(): Promise<Wallet> {
  const response = await apiClient.get("/api/wallet/balance");
  return response.data.data;
}

export async function listWalletTransactions(params?: {
  page?: number;
  limit?: number;
}): Promise<{ data: Transaction[]; meta: PaginationMeta }> {
  const response = await apiClient.get("/api/wallet/transactions", { params });
  return { data: response.data.data, meta: response.data.meta };
}

export async function topUpWallet(payload: TopUpRequest): Promise<Wallet> {
  const response = await apiClient.post("/api/wallet/topup", payload);
  return response.data.data;
}

export async function withdrawWallet(payload: WithdrawRequest): Promise<Wallet> {
  const response = await apiClient.post("/api/wallet/withdraw", payload);
  return response.data.data;
}
