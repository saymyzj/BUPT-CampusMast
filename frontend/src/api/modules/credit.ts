import apiClient from "@/api/client";
import type { CreditProfile, Rating } from "@/types/api";

export async function getMyCreditProfile(): Promise<CreditProfile> {
  const response = await apiClient.get("/api/credit/profile/me");
  return response.data.data;
}

export async function getUserCreditProfile(userId: string): Promise<CreditProfile> {
  const response = await apiClient.get(`/api/credit/profile/${userId}`);
  return response.data.data;
}

export async function listReceivedRatings(userId: string): Promise<Rating[]> {
  const response = await apiClient.get(`/api/credit/ratings/${userId}`);
  return response.data.data;
}
