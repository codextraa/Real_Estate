"use client";

import Form from "next/form";
import { FormButton } from "@/components/buttons/Buttons";
import { EyeButton } from "@/components/buttons/Buttons";
import styles from "./ProfileForm.module.css";
import { updateUserAction } from "@/actions/userActions";
import { useActionState, useState } from "react";
import { redirect } from "next/navigation";

export default function EditProfileForm({ userData }) {
  const initialState = {
    errors: {},
    success: "",
    formEmail: userData.email,
    formFirstName: userData.first_name,
    formLastName: userData.last_name,
    formUsername: userData.username,
  };

  const [state, formActions, isPending] = useActionState(
    updateUserAction.bind(null, userData.id, userData),
    initialState,
  );

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const toggleShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const toggleShowConfirmPassword = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  if (state.success) {
    setTimeout(() => {
      redirect("/auth/login");
    }, 1500);
  }

  return (
    <Form action={formActions} className={styles.Form}>
      <div className={styles.inputContainer}>
        <label htmlFor="email">Email Address</label>
        <input
          type="email"
          id="email"
          name="email"
          disabled={isPending}
          defaultValue={state.formEmail}
          className={styles.input}
        />
        {Object.keys(state.errors).length > 0 && state.errors.email && (
          <span className={styles.errorText}>{state.errors.email}</span>
        )}
      </div>
      <div className={styles.inputContainer}>
        <label htmlFor="first_name">First Name</label>
        <input
          type="text"
          id="first_name"
          name="first_name"
          disabled={isPending}
          defaultValue={state.formFirstName}
          className={styles.input}
        />
      </div>
      <div className={styles.inputContainer}>
        <label htmlFor="last_name">Last Name</label>
        <input
          type="text"
          id="last_name"
          name="last_name"
          disabled={isPending}
          defaultValue={state.formLastName}
          className={styles.input}
        />
      </div>
      <div className={styles.inputContainer}>
        <label htmlFor="username">Username</label>
        <input
          type="text"
          id="username"
          name="username"
          disabled={isPending}
          defaultValue={state.formUsername}
          className={styles.input}
        />
        {Object.keys(state.errors).length > 0 && state.errors.username && (
          <span className={styles.errorText}>{state.errors.email}</span>
        )}
      </div>
      <h2 className={styles.changePasswordTitle}>Change Password</h2>
      <div className={styles.inputContainer}>
        <div className={styles.passwordContainer}>
          <input
            type={showPassword ? "text" : "password"}
            id="password"
            name="password"
            disabled={isPending}
            className={styles.input}
          />
          <EyeButton
            action={toggleShowPassword}
            showPassword={showPassword}
            isPending={isPending}
          />
          {Object.keys(state.errors).length > 0 && state.errors.password && (
            <span className={styles.errorText}>{state.errors.password}</span>
          )}
        </div>
      </div>
      <div className={styles.inputContainer}>
        <div className={styles.passwordContainer}>
          <input
            type={showConfirmPassword ? "text" : "password"}
            id="c_password"
            name="c_password"
            disabled={isPending}
            className={styles.input}
          />
          <EyeButton
            action={toggleShowConfirmPassword}
            showPassword={showConfirmPassword}
            isPending={isPending}
          />
          {Object.keys(state.errors).length > 0 &&
            state.errors.c_password && (
              <span className={styles.errorText}>
                {state.errors.c_password}
              </span>
            )}
        </div>
      </div>
      {Object.keys(state.errors).length > 0 && state.errors.general && (
        <div className={styles.errorContainer}>{state.errors.general}</div>
      )}
      {state.success && (
        <div className={styles.successContainer}>{state.success}</div>
      )}
      <div className={styles.buttonContainer}>
        <div className={styles.updateProfileButton}>
          <FormButton
            text="Update Profile"
            pendingText="Updating..."
            type="submit"
          />
        </div>
        <div className={styles.deleteProfileButton}>
          <FormButton
            text="Delete Profile"
            pendingText="Deleting..."
            type="submit"
          />
        </div>
      </div>
    </Form>
  );
}
