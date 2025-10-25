"use client";

import Link from "next/link";
import { GlobalButton } from "@/components/buttons/Buttons";
import styles from "@/styles/NotFound.module.css";
import Image from "next/image";

export default function NotFound() {
  return (
    <div className={styles.background}>
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
            src="/assets/global-not-found.svg"
            alt="Not Found"
            width={349}
            height={247}
            className={styles.errorIcon}
            priority
          />
        </div>
        <div className={styles.errorTextContainer}>
          <div className={styles.errorTitle}>Error 404</div>
          <div className={styles.errorMessage}>Page Not Found</div>
          <div className={styles.button}>
            <Link href="/">
              <GlobalButton text="Back to Home" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
