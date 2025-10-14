"use client";

import { GlobalButton } from "@/components/buttons/Buttons"; 
import { useEffect } from 'react'
import styles from "@/styles/GlobalErrorModal.module.css";
import Image from "next/image";


export default function GlobalError({ error, reset }) {
  
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className={styles.errorContainer}>
      <Image
        src="/assets/global-error.svg"
        alt="Error"
        width={359}
        height={352}
        className={styles.errorIcon}
        priority
        loading="eager"
      />
      <div className={styles.errorTextContainer}>
        <div className={styles.errorTitle}>
          Oops! 
        </div>
        <div className={styles.errorMessage}>
          Something went wrong
        </div>
        <div className={styles.button}>
          <GlobalButton
            text="Go Back" 
            onClick={() => reset()} 
          /> 
        </div>
      </div>
    </div>
  );
}
