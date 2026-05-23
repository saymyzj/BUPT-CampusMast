import apiClient from "@/api/client";
import type { GetUploadSignedUrlRequest, UploadSignedUrlData } from "@/types/api";

export async function getUploadSignedUrl(payload: GetUploadSignedUrlRequest): Promise<UploadSignedUrlData> {
  const response = await apiClient.post("/api/upload/sign", payload);
  return response.data.data;
}
