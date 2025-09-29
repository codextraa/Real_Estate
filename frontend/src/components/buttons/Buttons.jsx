'use client';

import { useFormStatus } from 'react-dom';
import styles from './Buttons.module.css';

export function FormButton({ text, pendingText, type }) {
  const { pending } = useFormStatus();

  return (
    <button type={type} disabled={pending} className={styles.text}>
      {pending ? pendingText : text}
    </button>
  );
}
