'use server';

import { login } from '@/libs/api';
import {
  getUserIdFromSession,
  getUserRoleFromSession,
  setSessionCookie,
  // deleteSessionCookie,
} from '@/libs/cookie';

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

export const loginAction = async (prevState, formData) => {
  const email = formData.get('email');
  const password = formData.get('password');

  let errors = {};

  if (!email) {
    errors.email = 'Email is required.';
  } else if (!email.includes('@')) {
    errors.email = 'Invalid email format.';
  }

  if (!password) {
    errors.password = 'Password is required';
  }

  if (Object.keys(errors).length > 0) {
    return {
      errors, // {errors : errors}
      success: '',
      formEmail: email || '',
    };
  }

  const data = {
    email,
    password,
  };

  try {
    const response = await login(data);
    if (
      response.access_token &&
      response.refresh_token &&
      response.user_role &&
      response.user_id &&
      response.access_token_expiry
    ) {
      await setSessionCookie(response);

      return {
        errors,
        success: 'Login successful',
        formEmail: '',
      };
    } else {
      errors.general = response.error;
      return {
        errors,
        success: '',
        formEmail: email || '',
      };
    }
  } catch (error) {
    console.error(error);
    errors.general = error.message || 'An unexpected error occurred';
    return {
      errors,
      success: '',
      formEmail: email || '',
    };
  }
};

// export const logoutAction = async () => {
//   /* eslint-disable no-useless-catch */
//   try {
//     // Logout from the backend
//     await logout();
//     // Delete the session cookie
//     await deleteSessionCookie();
//   } catch (error) {
//     // Throw the NEXT REDIRECT error (otherwise it won't work)
//     throw error;
//   }
// };
