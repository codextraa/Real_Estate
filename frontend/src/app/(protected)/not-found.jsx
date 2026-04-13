"use client";

import Link from "next/link";
import { GlobalButton } from "@/components/buttons/Buttons";
import styles from "@/styles/NotFound.module.css";
import Image from "next/image";

export default function NotFound() {
  return (
    <main className={styles.background}>
      <figure className={styles.image}>
        <Image
          src="/real-estate/real-estate.jpg"
          alt="Modern city buildings representing real estate"
          fill
          priority
        />
      </figure>
      <section className={styles.container}>
        <figure className={styles.errorContainer}>
          <Image
            src="/assets/global-not-found.svg"
            alt="Not Found"
            width={349}
            height={247}
            className={styles.errorIcon}
            priority
          />
        </figure>
        <article className={styles.errorTextContainer}>
          <h1 className={styles.errorTitle}>Error</h1>
          <p className={styles.errorMessage}>Page Not Found</p>
          <div className={styles.button}>
            <Link href="/">
              <GlobalButton text="Back to Home" />
            </Link>
          </div>
        </article>
      </section>
    </main>
  );
}
