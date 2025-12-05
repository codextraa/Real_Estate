"use server";

import { createUser, updateUser, deleteUser } from "@/libs/api";
import { deleteSessionCookie } from "@/libs/cookie";
import { revalidatePath } from "next/cache";

const userError = (response) => {
  if (typeof response.error === "object") {
    const errorMessages = {};

    if (response.error.email) {
      errorMessages["email"] =
        response.error.email[0][0].toUpperCase() +
        response.error.email[0].slice(1).toLowerCase();
    }

    if (response.error.username) {
      errorMessages["username"] =
        response.error.username[0][0].toUpperCase() +
        response.error.username[0].slice(1).toLowerCase();
    }

    if (response.error.first_name) {
      errorMessages["first_name"] =
        response.error.first_name[0][0].toUpperCase() +
        response.error.first_name[0].slice(1).toLowerCase();
    }

    if (response.error.last_name) {
      errorMessages["last_name"] =
        response.error.last_name[0][0].toUpperCase() +
        response.error.last_name[0].slice(1).toLowerCase();
    }

    if (response.error.company_name) {
      errorMessages["company_name"] =
        response.error.company_name[0][0].toUpperCase() +
        response.error.company_name[0].slice(1).toLowerCase();
    }

    if (response.error.bio) {
      errorMessages["bio"] =
        response.error.bio[0][0].toUpperCase() +
        response.error.bio[0].slice(1).toLowerCase();
    }

    if (response.error.image_url) {
      errorMessages["image_url"] =
        response.error.image_url[0][0].toUpperCase() +
        response.error.image_url[0].slice(1).toLowerCase();
    }

    // Check for each possible attribute and append its messages
    if (response.error.password) {
      if (Array.isArray(response.error.password)) {
        errorMessages["password"] = response.error.password.join(" ");
      } else {
        errorMessages["password"] = response.error.password;
      }
    }

    // Combine messages into a single string with \n between each
    return errorMessages;
  }
  // If it's not an object, return the error as is (string or other type)
  return { general: response.error };
};

export const createUserAction = async (user, prevState, formData) => {
  const email = formData.get("email");
  const username = formData.get("username");
  const password = formData.get("password");
  const c_password = formData.get("c_password");
  const first_name = formData.get("first_name");
  const last_name = formData.get("last_name");
  const company_name = formData.get("company_name");

  const errors = {};

  if (!email) {
    errors.email = "Email is required";
  } else if (!email.includes("@")) {
    errors.email = "Email is invalid";
  }

  if (!password) {
    errors.password = "Password is required";
  }

  if (!c_password) {
    errors.c_password = "Confirm Password is required";
  }

  if (password !== c_password) {
    errors.c_password = "Passwords do not match";
  }

  if (user === "agent" && !company_name) {
    errors.company_name = "Company Name is required";
  }

  if (Object.keys(errors).length > 0) {
    return {
      errors,
      success: "",
      formEmail: email || "",
      formFirstName: first_name || "",
      formLastName: last_name || "",
      formUsername: username || "",
      formCompanyName: company_name || "",
    };
  }

  const data = {
    email,
    password,
    c_password,
    ...(first_name && { first_name }),
    ...(last_name && { last_name }),
    ...(username && { username }),
    ...(company_name && { company_name }),
    ...(user === "agent" && { is_agent: true }),
  };

  try {
    const response = await createUser(data, user);
    if (response.error) {
      const backend_errors = userError(response);
      return {
        errors: backend_errors,
        success: "",
        formEmail: email || "",
        formFirstName: first_name || "",
        formLastName: last_name || "",
        formUsername: username || "",
        formCompanyName: company_name || "",
      };
    }
    return {
      errors,
      success: response.success,
      formEmail: "",
      formFirstName: "",
      formLastName: "",
      formUsername: "",
      formCompanyName: "",
    };
  } catch (error) {
    console.error(error);
    errors.general = error.message || "An unexpected error occurred";
    return {
      errors,
      success: "",
      formEmail: email || "",
      formFirstName: first_name || "",
      formLastName: last_name || "",
      formUsername: username || "",
      formCompanyName: company_name || "",
    };
  }
};

export const updateUserAction = async (id, userRole, prevState, formData) => {
  const first_name = formData.get("first_name");
  const last_name = formData.get("last_name");
  const username = formData.get("username");
  const password = formData.get("password");
  const c_password = formData.get("c_password");
  const bio = formData.get("bio");
  const company_name = formData.get("company_name");
  const profile_image = formData.get("profile_image");

  const newUserFormData =
    userRole === "Agent"
      ? {
          user: {
            email: prevState.formUserData.user.email,
            first_name: first_name || prevState.formUserData.user.first_name,
            last_name: last_name || prevState.formUserData.user.last_name,
            username: username || prevState.formUserData.user.username,
            slug: prevState.formUserData.user.slug,
          },
          bio: bio || prevState.formUserData.bio,
          company_name: company_name || prevState.formUserData.company_name,
          image_url: prevState.formUserData.image_url,
        }
      : {
          email: prevState.formUserData.email,
          first_name: first_name || prevState.formUserData.first_name,
          last_name: last_name || prevState.formUserData.last_name,
          username: username || prevState.formUserData.username,
          slug: prevState.formUserData.slug,
        };

  const errors = {};

  if (username === "") {
    errors.username = "Username cannot be empty";
  }

  if (userRole === "Agent" && company_name === "") {
    errors.company_name = "Company Name cannot be empty";
  }

  if (password !== c_password) {
    errors.c_password = "Passwords do not match";
  }

  if (Object.keys(errors).length > 0) {
    return {
      errors,
      success: "",
      formUserData: newUserFormData,
    };
  }

  try {
    let response;
    const isNewImageUploaded =
      profile_image && profile_image instanceof File && profile_image.size > 0;

    if (isNewImageUploaded) {
      const keys_to_delete = [];
      for (const [key, value] of formData.entries()) {
        if (
          key.startsWith("$") ||
          key === "" ||
          (key === "password" && value === "") ||
          (key === "c_password" && value === "")
        ) {
          keys_to_delete.push(key);
        }
      }

      for (const key of keys_to_delete) {
        formData.delete(key);
      }

      response = await updateUser(id, formData, userRole, true);
    } else {
      const data = {
        ...((first_name || first_name === "") && { first_name }),
        ...((last_name || last_name === "") && { last_name }),
        ...(username && { username }),
        ...(password && { password }),
        ...(c_password && { c_password }),
        ...((bio || bio === "") && { bio }),
        ...(company_name && { company_name }),
      };
      response = await updateUser(id, data, userRole);
    }

    if (response.error) {
      const backend_errors = userError(response);
      return {
        errors: backend_errors,
        success: "",
        formUserData: newUserFormData,
      };
    }

    const updatedSlug =
      userRole === "Agent" ? response.data.user.slug : response.data.slug;

    revalidatePath(`/profile/${updatedSlug}/edit`);

    return {
      errors,
      success: response.success,
      formUserData: response.data,
    };
  } catch (error) {
    console.error(error);
    errors.general = error.message || "An unexpected error occurred";
    return {
      errors,
      success: "",
      formUserData: newUserFormData,
    };
  }
};

export const deleteUserAction = async (id, userRole) => {
  try {
    const response = await deleteUser(id, userRole);

    if (response.error) {
      return { error: response.error };
    }

    await deleteSessionCookie();

    return { success: response.success };
  } catch (error) {
    console.error(error);
    return { error: error.message || "An unexpected error occurred" };
  }
};
