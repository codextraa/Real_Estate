"use client";

import { useActionState, useState } from "react";
import styles from "./SignUpForm.module.css";
import { EyeButton, FormButton } from "@/components/buttons/Buttons";
import { createUserAction } from "@/actions/userActions";
import Form from "next/form";
import { redirect } from "next/navigation";
import Link from "next/link";

export default function SignUpForm({ userType }) {
  const initialState = {
    errors: {},
    success: "",
    formEmail: "",
    formFirstName: "",
    formLastName: "",
    formUsername: "",
    formCompanyName: "",
  };

  const [state, formAction, isPending] = useActionState(
    createUserAction.bind(null, userType),
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
    <Form action={formAction} className={styles.form}>
      <h1 className={styles.title}>Estate</h1>
      <div className={styles.mainContainer}>
        <h2 className={styles.subTitle}>Welcome!</h2>

        {Object.keys(state.errors).length > 0 && state.errors.general && (
          <div className={styles.errorContainer}>{state.errors.general}</div>
        )}
        {state.success && (
          <div className={styles.successContainer}>{state.success}</div>
        )}

        <div className={styles.formInputContainer}>
          <div className={styles.inputContainer}>
            <input
              type="email"
              id="email"
              name="email"
              placeholder="Email*"
              disabled={isPending}
              defaultValue={state.formEmail}
              className={styles.input}
            />
            {Object.keys(state.errors).length > 0 && state.errors.email && (
              <span className={styles.errorText}>{state.errors.email}</span>
            )}
          </div>
          <div className={styles.inputContainer}>
            <input
              type="text"
              id="first_name"
              name="first_name"
              placeholder="First Name"
              disabled={isPending}
              defaultValue={state.formFirstName}
              className={styles.input}
            />
            {Object.keys(state.errors).length > 0 &&
              state.errors.first_name && (
                <span className={styles.errorText}>
                  {state.errors.first_name}
                </span>
              )}
          </div>
          <div className={styles.inputContainer}>
            <input
              type="text"
              id="last_name"
              name="last_name"
              placeholder="Last Name"
              disabled={isPending}
              defaultValue={state.formLastName}
              className={styles.input}
            />
            {Object.keys(state.errors).length > 0 && state.errors.last_name && (
              <span className={styles.errorText}>{state.errors.last_name}</span>
            )}
          </div>
          {userType === "agent" && (
            <div className={styles.inputContainer}>
              <input
                type="text"
                id="company_name"
                name="company_name"
                placeholder="Company Name"
                disabled={isPending}
                defaultValue={state.formCompanyName}
                className={styles.input}
              />
              {Object.keys(state.errors).length > 0 &&
                state.errors.company_name && (
                  <span className={styles.errorText}>
                    {state.errors.company_name}
                  </span>
                )}
            </div>
          )}

          <div className={styles.inputContainer}>
            <input
              type="text"
              id="username"
              name="username"
              placeholder="Username"
              disabled={isPending}
              defaultValue={state.formUsername}
              className={styles.input}
            />
            <span className={styles.inputHint}>
              Username must be at least 6 characters long, and cannot contain
              spaces. Username can only contain letters, numbers, periods,
              underscores, hyphens, and @ signs.
            </span>
            {Object.keys(state.errors).length > 0 && state.errors.username && (
              <span className={styles.errorText}>{state.errors.username}</span>
            )}
          </div>

          <div className={styles.inputContainer}>
            <div className={styles.passwordContainer}>
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                name="password"
                placeholder="Password*"
                disabled={isPending}
                className={styles.input}
              />
              <EyeButton
                action={toggleShowPassword}
                showPassword={showPassword}
                isPending={isPending}
              />
            </div>
            <span className={styles.inputHint}>
              Password must be at least 8 characters.
            </span>
            <span className={styles.inputHint}>
              Must include at least one uppercase letter, one lowercase letter,
              one number, one special character..
            </span>
            {Object.keys(state.errors).length > 0 && state.errors.password && (
              <span className={styles.errorText}>{state.errors.password}</span>
            )}
          </div>
          <div className={styles.inputContainer}>
            <div className={styles.passwordContainer}>
              <input
                type={showConfirmPassword ? "text" : "password"}
                id="c_password"
                name="c_password"
                placeholder="Confirm Password*"
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
        <div className={styles.buttonContainer}>
          <FormButton
            text="Create CustomerAccount"
            pendingText="Creating Account..."
            type="submit"
          />
        </div>
        <div className={styles.signUpLast}>
          Already have an account?
          <Link href="/auth/login" className={styles.signUpLink}>
            Login
          </Link>
        </div>
      </div>
    </Form>
  );
}
