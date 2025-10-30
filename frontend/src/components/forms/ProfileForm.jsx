"use client";

import Form from "next/form";
import Link from "next/link";
import { useEffect } from "react";
import { FormButton } from "@/components/buttons/Buttons";
import { EyeButton } from "@/components/buttons/Buttons";
import { updateUserAction } from "@/actions/userActions";
import { useActionState, useState } from "react";
import { GlobalButton } from "@/components/buttons/Buttons";
import styles from "./ProfileForm.module.css";

export default function ProfileForm({ userData, userRole }) {
  const initialState = {
    errors: {},
    success: "",
    formUserData: userData,
  };

  const [state, formActions, isPending] = useActionState(
    updateUserAction.bind(null, userData.id, userRole),
    initialState,
  );

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [displaySuccess, setDisplaySuccess] = useState("");

  const toggleShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const toggleShowConfirmPassword = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  useEffect(() => {
    if (state.success) {
      setDisplaySuccess(state.success);
      const timer = setTimeout(() => {
        setDisplaySuccess("");
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [state.success]);

  return (
    <div className={styles.ProfileFormContainer}>
      <div className={styles.ProfileFormTitle}>Edit Profile Information</div>
      <Form action={formActions} className={styles.Form}>
        <div className={styles.inputContainer}>
          <label htmlFor="email">Email Address</label>
          <input
            type="email"
            id="email"
            disabled={isPending}
            defaultValue={state.formUserData.email || ""}
            className={styles.input}
            readOnly
          />
        </div>
        <div className={styles.inputContainer}>
          <label htmlFor="first_name">First Name</label>
          <input
            type="text"
            id="first_name"
            name="first_name"
            disabled={isPending}
            defaultValue={state.formUserData.first_name || ""}
            className={styles.input}
          />
          {Object.keys(state.errors).length > 0 && state.errors.first_name && (
            <span className={styles.errorText}>{state.errors.first_name}</span>
          )}
        </div>
        <div className={styles.inputContainer}>
          <label htmlFor="last_name">Last Name</label>
          <input
            type="text"
            id="last_name"
            name="last_name"
            disabled={isPending}
            defaultValue={state.formUserData.last_name || ""}
            className={styles.input}
          />
          {Object.keys(state.errors).length > 0 && state.errors.last_name && (
            <span className={styles.errorText}>{state.errors.last_name}</span>
          )}
        </div>
        <div className={styles.inputContainer}>
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            name="username"
            disabled={isPending}
            defaultValue={state.formUserData.username || ""}
            className={styles.input}
          />
          {Object.keys(state.errors).length > 0 && state.errors.username && (
            <span className={styles.errorText}>{state.errors.username}</span>
          )}
        </div>
        <div className={styles.passwordContainer}>
          <h2 className={styles.changePasswordTitle}>Change Password</h2>
          <div className={styles.inputContainer}>
            <div className={styles.passwordInputContainer}>
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
            </div>
            {Object.keys(state.errors).length > 0 && state.errors.password && (
              <span className={styles.errorText}>{state.errors.password}</span>
            )}
          </div>
          <div className={styles.inputContainer}>
            <div className={styles.passwordInputContainer}>
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
            </div>
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
        {displaySuccess && (
          <div className={styles.successContainer}>{displaySuccess}</div>
        )}
        <div className={styles.buttonContainer}>
          <div className={styles.cancelProfileButton}>
            <Link href={`/profile/${state.formUserData.slug}`}>
              <GlobalButton text="Cancel" />
            </Link>
          </div>
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
    </div>
  );
}
