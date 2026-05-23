import LoginForm from "@/components/forms/LoginForm";
import styles from "@/styles/LoginPage.module.css";
import Image from "next/image";

export default async function LoginPage() {
  const imageUrl = "/real-estate/real-estate.jpg";

  return (
    <main className={styles.background}>
      <section className={styles.container}>
        <article className={styles.formContainer}>
          <LoginForm />
        </article>
        <figure className={styles.image}>
          <Image
            src={imageUrl}
            alt="Modern city buildings representing real estate"
            width={669}
            height={746}
            priority
          />
        </figure>
      </section>
    </main>
  );
}
