'use client';

import Form from 'next/form';
import { useState } from 'react';
import { useActionState } from 'react';
import { redirect } from 'next/navigation';
import { loginAction } from '@/actions/authActions';
import { FormButton } from '@/components/buttons/Buttons';
import { DEFAULT_LOGIN_REDIRECT } from '@/route';
import { EyeButton } from '@/components/buttons/Buttons';
import styles from './LoginForm.module.css';

const initialState = {
  errors: {},
  success: '',
  formEmail: '',
};

export default function LoginForm() {
  const [state, formAction, isPending] = useActionState(
    loginAction,
    initialState
  );

  const [showPassword, setShowPassword] = useState(false);

  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
  };

  if (state.success) {
    setTimeout(() => {
      redirect(DEFAULT_LOGIN_REDIRECT);
    }, 1500);
  }

  return (
    <Form action={formAction} className={styles.form}>
      <h1 className={styles.title1}>Estate</h1>
      <div className={styles.mainContainer}>
        <h2 className={styles.title2}>Welcome!</h2>

        {Object.keys(state.errors).length > 0 && state.errors.general && (
          <div className={styles.generalError}>{state.errors.general}</div>
        )}
        {state.success && <div className={styles.success}>{state.success}</div>}

        <div className={styles.formInputContainer}>
          <div className={styles.inputContainer}>
            <input
              id="email"
              name="email"
              placeholder="Email"
              disabled={isPending}
              defaultValue={state.formEmail}
              className={styles.input}
            />
            {Object.keys(state.errors).length > 0 && state.errors.email && (
              <div className={styles.error}>{state.errors.email}</div>
            )}
          </div>

          <div className={styles.inputContainer}>
            <div className={styles.passwordContainer}>
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Password"
                disabled={isPending}
                className={styles.input}
              />
              <EyeButton
                action={togglePasswordVisibility}
                showPassword={showPassword}
                isPending={isPending}
              />
            </div>
            {Object.keys(state.errors).length > 0 && state.errors.password && (
              <div className={styles.error}>{state.errors.password}</div>
            )}
          </div>
        </div>
        <div className={styles.buttonContainer}>
          <FormButton text="Login" pendingText="Logging in..." type="submit" />
        </div>
      </div>
    </Form>
  );
}
