import axios from "axios";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20_000,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("trackit_token");
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
  }
  return config;
});
