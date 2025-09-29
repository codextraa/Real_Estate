'use client';

import Image from 'next/image';
import { useFormStatus } from 'react-dom';
import styles from './Buttons.module.css';

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
      aria-label={showPassword ? 'Hide password' : 'Show password'}
      disabled={isPending}
    >
      <Image
        src={
          showPassword ? '/assets/eye-closed-icon.svg' : '/assets/eye-icon.svg'
        }
        width={20}
        height={14}
        alt={showPassword ? 'Hidden' : 'Visible'}
        className={styles.toggleIcon}
      />
    </button>
  );
}
