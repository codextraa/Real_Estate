import styles from "@/styles/Loading.module.css";
import Image from "next/image";

export default function Loading() {
  return (
    <div className={styles.background}>
      <div className={styles.logoContainer}>
        <Image
          src="/assets/loading.svg"
          alt="Loading Logo"
          width={105}
          height={105}
          className={styles.logo}
        />
      </div>
      <div className={styles.text}>
        Loading
        <span className={styles.dots}>...</span>
      </div>
    </div>
  );
}
