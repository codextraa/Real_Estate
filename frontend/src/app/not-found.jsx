"use client";

import Link from "next/link"; // Import Link for navigation
import { GlobalButton } from "@/components/buttons/Buttons";
import styles from "@styles/NotFoundModal.module.css";
import Image from "next/image";

export default function NotFound() {
  return (
    <html>
      <head>
        {/* Set a proper title for the browser tab */}
        <title>Page Not Found - Estate</title>
      </head>
      <body>
        <main className={styles.fullScreenWrapper}>
          <div className={styles.errorContainer}>
            <Image
              src="/assets/global-not-found.svg"
              alt="Not Found"
              width={349}
              height={247}
              className={styles.errorIcon}
              priority
            />
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
        </main>
      </body>
    </html>
  );
}
