import SignUpPageCard from "@/components/cards/SignUpPageCard";
import SignUpForm from "@/components/forms/SignUpForm";
import Image from "next/image";
import styles from "@/styles/SignUpPage.module.css";

export default async function SignUpPage({ searchParams }) {
  const imgUrl = "/real-estate/real-estate.jpg";
  const { user } = await searchParams;
  // const params = await searchParams;
  // user = params.user

  return user && (user === "customer" || user === "agent") ? (
    <main className={styles.signUpBackground}>
      <section className={styles.signUpPageContainer}>
        <figure className={styles.signUpPictureContainer}>
          <Image
            src={imgUrl}
            alt="Modern city buildings representing real estate"
            width={669}
            height={900}
            priority
          />
        </figure>
        <article className={styles.signUpPageFormContainer}>
          <SignUpForm userType={user} />
        </article>
      </section>
    </main>
  ) : (
    <main className={styles.background}>
      <Image src={imgUrl} alt="background" fill priority />
      <article className={styles.signUpPageCardContainer}>
        <SignUpPageCard />
      </article>
    </main>
  );
}
