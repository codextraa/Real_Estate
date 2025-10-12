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
    <div className={styles.signUpBackground}>
      <div className={styles.signUpPageContainer}>
        <div className={styles.signUpPictureContainer}>
          <Image
            src={imgUrl}
            alt="Modern city buildings representing real estate"
            width={669}
            height={900}
            priority
          />
        </div>
        <div className={styles.signUpPageFormContainer}>
          <SignUpForm userType={user} />
        </div>
      </div>
    </div>
  ) : (
    <div className={styles.background}>
      <Image src={imgUrl} alt="background" fill priority />
      <div className={styles.signUpPageCardContainer}>
        <SignUpPageCard />
      </div>
    </div>
  );
}
