import apiClient from "@/api/client";
import type { UploadImageData } from "@/types/api";

export async function uploadTaskImage(file: File): Promise<UploadImageData> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiClient.post("/api/upload/images", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data.data;
}
