import { ApiClient } from "./apiClient";
import { getRefreshTokenFromSession } from "./cookie";

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
  const refreshToken = await getRefreshTokenFromSession();

  if (refreshToken) {
    await apiClient.post("/auth-api/logout/", { refresh: refreshToken });
  }
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

export const deleteUser = async (id, userRole) => {
  const base_url = userRole === "Agent" ? "agents" : "users";
  return apiClient.delete(`/auth-api/${base_url}/${id}/`);
};

export const getProperties = async (queryParams = {}) => {
  const params = new URLSearchParams(queryParams);
  return apiClient.get(`/property-api/properties/?${params.toString()}`);
};

export const createProperty = async (data, isImage = false) => {
  if (isImage) {
    return apiClient.post("/property-api/properties/", data, {}, true);
  }
  return apiClient.post("/property-api/properties/", data);
};

export const getProperty = async (id) => {
  return apiClient.get(`/property-api/properties/${id}/`);
};

export const updateProperty = async (id, data, isImage = false) => {
  if (isImage) {
    return apiClient.patch(`/property-api/properties/${id}/`, data, {}, true);
  }
  return apiClient.patch(`/property-api/properties/${id}/`, data);
};

export const deleteProperty = async (id) => {
  return apiClient.delete(`/property-api/properties/${id}/`);
};
