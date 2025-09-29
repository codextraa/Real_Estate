"use client";

import Form from "next/form";
import { redirect } from "next/navigation";
import { useActionState } from "react";
import { loginAction } from "@/actions/authActions";
import { FormButton } from "@/components/buttons/Buttons";
import { DEFAULT_LOGIN_REDIRECT } from "@/route";
import styles from "./LoginForm.module.css";

const initialState = {
  errors: {},
  success: "",
};

export default function LoginForm() {
  const [state, formAction, isPending] = useActionState(
    loginAction,
    initialState,
  );

  if (state.success) {
    redirect(DEFAULT_LOGIN_REDIRECT);
  }

  return (
    <Form action={formAction} className={styles.form}>
      <h2 className={styles.title}>Welcome!</h2>

      {Object.keys(state.errors).length > 0 && state.errors.general && (
        <div className={styles.generalError}>{state.errors.general}</div>
      )}
      {state.success && <div className={styles.success}>{state.success}</div>}

      <div className={styles.inputContainer}>
        <input
          id="email"
          name="email"
          type="email"
          placeholder="Email"
          disabled={isPending}
          className={styles.input}
        />
        {Object.keys(state.errors).length > 0 && state.errors.email && (
          <div className={styles.error}>{state.errors.email}</div>
        )}
      </div>

      <div className={styles.inputContainer}>
        <input
          id="password"
          name="password"
          type="password"
          placeholder="Password"
          disabled={isPending}
          className={styles.input}
        />
        {Object.keys(state.errors).length > 0 && state.errors.password && (
          <div className={styles.error}>{state.errors.password}</div>
        )}
      </div>

      <div className={styles.buttonContainer}>
        <FormButton text="Login" pendingText="Logging in..." type="submit" />
      </div>
    </Form>
  );
}
