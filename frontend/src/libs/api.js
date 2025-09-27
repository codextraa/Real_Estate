import { ApiClient } from './apiClient';
// import { getRefreshTokenFromSession } from './cookie';

const HTTPS = process.env.HTTPS === 'true';
const API_URL = HTTPS
  ? process.env.API_BASE_HTTPS_URL
  : process.env.API_BASE_URL;
const apiClient = new ApiClient(API_URL);

export const refreshToken = async (refreshToken) => {
  return await apiClient.post('/auth-api/token/refresh/', {
    refresh: refreshToken,
  });
};

export const login = async (data) => {
  return apiClient.post('/auth-api/login/', data);
};
