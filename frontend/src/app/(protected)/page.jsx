import styles from "@/styles/Interface.module.css";
import { HomePageButton } from "@/components/buttons/Buttons";
import Footer from "@/components/footer/Footer";
import Image from "next/image";
export default function Page() {
  const imageUrl = "/real-estate/real-estate.jpg";

  return (
    <div className={styles.image}>
      <Image
        src={imageUrl}
        alt="Modern city buildings representing real estate"
        fill
        priority
      />
      

      <div className={styles.container}>
        <div className={styles.content}>Estate</div>
        <div className={styles.buttons}>
          <HomePageButton text="Get Started" />
        </div>
      </div>
      <Footer />
    </div>
  );
}
