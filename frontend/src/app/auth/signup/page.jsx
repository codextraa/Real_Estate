import SignUpPageCard from "@/components/cards/SignUpPageCard";
import Image from "next/image";
import styles from "@/styles/SignUpPage.module.css";

export default function SignUpPage() {
  const imgUrl = "/real-estate/real-estate.jpg";
  return (
    <div className={styles.background}>
      <Image src={imgUrl} alt="background" fill priority />
      <div className={styles.signUpPageCardContainer}>
        <SignUpPageCard />
      </div>
    </div>
  );
}
