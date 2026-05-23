import styles from "@/styles/Loading.module.css";
import Image from "next/image";

export default function Loading() {
  const gifUrl = "/assets/loading-anime.gif";

  return (
    <main className={styles.background}>
      <figure className={styles.logoContainer}>
        <Image
          src={gifUrl}
          alt="Loading Animation"
          width={200}
          height={200}
          className={styles.gif}
          unoptimized
        />
      </figure>
      <h1 className={styles.text}>
        Loading
        <span className={styles.dots}>.</span>
      </h1>
    </main>
  );
}
