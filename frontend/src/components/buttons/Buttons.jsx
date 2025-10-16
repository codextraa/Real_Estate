"use client";

import Image from "next/image";
import { useFormStatus } from "react-dom";
import { useRouter } from "next/navigation";
import styles from "./Buttons.module.css";

export function FormButton({ text, pendingText, type }) {
  const { pending } = useFormStatus();
  const textClassName =
    text === "Delete Profile" ? styles.deleteProfileButton : styles.formButton;

  return (
    <button type={type} disabled={pending} className={textClassName}>
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

export function GlobalButton({ text, onClick }) {
  return (
    <button type="button" className={styles.globalButton} onClick={onClick}>
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
    text === "Log In" ? styles.NavLogInButton : styles.NavSignUpButton;

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
