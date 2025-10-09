"use server";

import { createUser } from "@/libs/api";

const signUpError = (response) => {
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

export const createUserAction = async (user, prevState, formdata) => {
  const email = formdata.get("email");
  const username = formdata.get("username");
  const password = formdata.get("password");
  const c_password = formdata.get("c_password");
  const first_name = formdata.get("first_name");
  const last_name = formdata.get("last_name");
  const company_name = formdata.get("company_name");

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
    throw new Error('Error div testing');
    const response = await createUser(data);
    console.log(response);
    if (response.error) {
      const backend_errors = signUpError(response);
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
