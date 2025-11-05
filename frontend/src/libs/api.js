import { ApiClient } from "./apiClient";
// import { getRefreshTokenFromSession } from './cookie';

const HTTPS = process.env.HTTPS === "true";
const API_URL = HTTPS
  ? process.env.API_BASE_HTTPS_URL
  : process.env.API_BASE_URL;
const apiClient = new ApiClient(API_URL);

export const refreshToken = async (refreshToken) => {
  return await apiClient.post("/auth-api/refresh-token/", {
    refresh: refreshToken,
  });
};

export const login = async (data) => {
  return apiClient.post("/auth-api/login/", data);
};

export const logout = async () => {
  return await apiClient.post("/auth-api/logout/");
};

export const getUser = async (id) => {
  return apiClient.get(`/auth-api/users/${id}/`, {
    next: { revalidate: 60 },
  });
};

export const getAgent = async (id) => {
  return apiClient.get(`/auth-api/agents/${id}/`, {
    next: { revalidate: 60 },
  });
};

export const createUser = async (data, userRole) => {
  if (userRole === "agent") {
    return apiClient.post("/auth-api/agents/", data);
  }
  return apiClient.post("/auth-api/users/", data);
};

export const updateUser = async (id, data, userRole, isImage = false) => {
  const base_url = userRole === "Agent" ? "agents" : "users";

  if (isImage) {
    return apiClient.patch(`/auth-api/${base_url}/${id}/`, data, {}, true);
  }
  return apiClient.patch(`/auth-api/${base_url}/${id}/`, data);
};
