"use client";

import Image from "next/image";
import { useFormStatus } from "react-dom";
import { useRouter } from "next/navigation";
import styles from "./Buttons.module.css";

const crossIcon = "/assets/cross-icon.svg";
export function FormButton({ text, pendingText, type, className }) {
  const { pending } = useFormStatus();

  return (
    <button
      type={type}
      disabled={pending}
      className={`${styles.formButton} ${className}`}
    >
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

export function NavButton({ text, href, onClick }) {
  const router = useRouter();

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else if (!onClick && href) {
      router.push(href);
    }
  };

  const buttonClass =
    text === "Login" || text === "Log Out"
      ? styles.NavLogInButton
      : styles.NavSignUpButton;

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

export function DeleteButton({ type, text, onClick, className, disabled }) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`${styles.deleteButton} ${className}`}
    >
      {text}
    </button>
  );
}

export function BackButton({ text }) {
  const router = useRouter();
  return (
    <div className={styles.cancelProfileButton}>
      <button
        onClick={() => router.back()}
        className={styles.cancelProfileButtonLink}
        type="submit"
      >
        {text}
      </button>
    </div>
  );
}

export function CloseButton({ onClick, className }) {
  return (
    <button
      className={className ? `${className}` : styles.closeButton}
      onClick={onClick}
    >
      <Image src={crossIcon} alt="Close Icon" width={30} height={30} />
    </button>
  );
}
