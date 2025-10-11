"use client";

import Image from "next/image";
import { useFormStatus } from "react-dom";
import { useRouter } from "next/navigation";
import styles from "./Buttons.module.css";

export function FormButton({ text, pendingText, type }) {
  const { pending } = useFormStatus();

  return (
    <button type={type} disabled={pending} className={styles.formButton}>
      {pending ? pendingText : text}
    </button>
  );
}

export function EyeButton({ action, showPassword, isPending }) {
  return (
    <button
      type="button"
      onClick={action}
      className={styles.passwordToggle}
      aria-label={showPassword ? "Hide password" : "Show password"}
      disabled={isPending}
    >
      <Image
        src={
          showPassword ? "/assets/eye-closed-icon.svg" : "/assets/eye-icon.svg"
        }
        width={20}
        height={14}
        alt={showPassword ? "Hidden" : "Visible"}
        className={styles.toggleIcon}
      />
    </button>
  );
}

export function SignUpButton({ text }) {
  return (
    <button type="button" className={styles.signUpButton}>
      {text}
    </button>
  );
}

export function NavButton({ text, href }) {
  const router = useRouter();

  const handleClick = () => {
    if (href) {
      router.push(href);
    }
  };

  const buttonClass =
    text === "Sign Up" ? styles.NavSignUpButton : styles.NavLogInButton;

  return (
    <button type="button" className={buttonClass} onClick={handleClick}>
      {text}
    </button>
  );
}

export function HomePageButton({ text }) {
  const router = useRouter();
  const status = useFormStatus();
  const handleClick = () => {
    router.push("/auth/login");
  };
  return (
    <button
      type="button"
      className={styles.HomePageButton}
      onClick={handleClick}
      disabled={status === "loading"}
    >
      {text}
    </button>
  );
}
