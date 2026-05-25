import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:9000";

export const apiClient = axios.create({
  baseURL,
  timeout: 10000,
});

apiClient.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("campusmast.accessToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    const refreshToken = sessionStorage.getItem("campusmast.refreshToken");
    if (!refreshToken) {
      return Promise.reject(error);
    }

    if (!isRefreshing) {
      isRefreshing = true;
      try {
        const { data } = await axios.post(`${baseURL}/api/auth/refresh`, { refreshToken });
        const newAccessToken = data.data.accessToken;
        sessionStorage.setItem("campusmast.accessToken", newAccessToken);
        onRefreshed(newAccessToken);
        isRefreshing = false;

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        originalRequest._retry = true;
        return apiClient(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        refreshSubscribers = [];
        sessionStorage.removeItem("campusmast.accessToken");
        sessionStorage.removeItem("campusmast.refreshToken");
        sessionStorage.removeItem("campusmast.currentUser");
        localStorage.removeItem("campusmast.accessToken");
        localStorage.removeItem("campusmast.refreshToken");
        localStorage.removeItem("campusmast.currentUser");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return new Promise((resolve) => {
      subscribeTokenRefresh((newToken: string) => {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        originalRequest._retry = true;
        resolve(apiClient(originalRequest));
      });
    });
  },
);

export default apiClient;

