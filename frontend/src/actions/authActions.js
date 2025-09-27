"use server";

import { login, logout } from "@/libs/api";
import {
  getUserIdFromSession,
  getUserRoleFromSession,
  deleteSessionCookie,
} from "@/libs/cookie";

export const getUserIdAction = async () => {
  try {
    return await getUserIdFromSession();
  } catch (error) {
    console.error(error);
    return null;
  }
};

export const getUserRoleAction = async () => {
  try {
    return await getUserRoleFromSession();
  } catch (error) {
    console.error(error);
    return null;
  }
};

export async function loginAction(formData) {
  const email = formData.get("email");
  const password = formData.get("password");

  const data = {
    email,
    password,
  };

  try {
    return await login(data);
  } catch (error) {
    // Handle any network or unexpected error
    console.error(error);
    return { error: error.message || "An error occurred during login." };
  }
}

export const logoutAction = async () => {
  /* eslint-disable no-useless-catch */
  try {
    // Logout from the backend
    await logout();
    // Delete the session cookie
    await deleteSessionCookie();
  } catch (error) {
    // Throw the NEXT REDIRECT error (otherwise it won't work)
    throw error;
  }
};
