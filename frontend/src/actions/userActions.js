"use server";

import { createUser } from "@/libs/api";

export const signUpError = (response) => {
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

    if (response.error.phone_number) {
      errorMessages["phone_number"] =
        response.error.phone_number[0][0].toUpperCase() +
        response.error.phone_number[0].slice(1).toLowerCase();
    }

    // Check for each possible attribute and append its messages
    if (response.error.password) {
      const passErrorMessages = [];
      const error = response.error.password;

      if (error.short) {
        passErrorMessages.push(...[error.short]);
      }
      if (error.upper) {
        passErrorMessages.push(...[error.upper]);
      }
      if (error.lower) {
        passErrorMessages.push(...[error.lower]);
      }
      if (error.number) {
        passErrorMessages.push(...[error.number]);
      }
      if (error.special) {
        passErrorMessages.push(...[error.special]);
      }

      if (passErrorMessages.length === 0) {
        passErrorMessages.push(
          ...[error[0][0].toUpperCase() + error[0].slice(1).toLowerCase()],
        );
      }

      errorMessages["password"] = passErrorMessages.join(" ");
    }

    // Combine messages into a single string with \n between each
    return { error: errorMessages };
  }
  // If it's not an object, return the error as is (string or other type)
  return { error: { error: response.error } };
};

export const createUserAction = async (formdata, user = "user") => {
  const email = formdata.get("email");
  const username = formdata.get("username");
  const password = formdata.get("password");
  const c_password = formdata.get("c_password");
  const first_name = formdata.get("first_name");
  const last_name = formdata.get("last_name");
  const address = formdata.get("address");

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

  if (!first_name) {
    errors.first_name = "First name is required";
  }

  if (!last_name) {
    errors.last_name = "Last name is required";
  }

  if (!username) {
    errors.username = "Username is required";
  }

  if (!address) {
    errors.address = "Address is required";
  }

  if (Object.keys(errors).length > 0) {
    return { errors };
  }

  const data = {
    email,
    password,
    c_password,
    ...(first_name && { first_name }),
    ...(last_name && { last_name }),
    ...(address && { address }),
    ...(username && { username }),
    ...(user === "admin" && { is_staff: true }),
  };

  try {
    const response = await createUser(data);
    if (response.error) {
      return signUpError(response);
    }
    return { success: response.success };
  } catch (error) {
    console.error(error);
    return {
      error: error.message || "An error occurred during user creation.",
    };
  }
};
