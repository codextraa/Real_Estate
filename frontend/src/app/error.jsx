"use client";

import { useEffect } from "react";
import Image from "next/image";
import styles from "@/styles/Error.module.css";
import { GlobalButton } from "@/components/buttons/Buttons";

export default function Error({ error, reset }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
        <div>
          <div className={styles.image}>
          <Image
            src="/real-estate/real-estate.jpg"
            alt="Modern city buildings representing real estate"
            fill
            priority
          />
          </div>
          <div className={styles.container}>
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
            </div>
            <div className={styles.errorTextContainer}>
              <div className={styles.errorTitle}>Oops!</div>
              <div className={styles.errorMessage}>Something went wrong</div>
              <div className={styles.button}>
                <GlobalButton text="Go Back" onClick={() => reset()} />
              </div>
            </div>
          </div>
        </div>
        
        
  );
}
