import { SignUpButton } from "@/components/buttons/Buttons";
import styles from './SignUpPageCard.module.css';
import Link from "next/link";

export default function SignUpPageCard(){
    return(
        <div className={styles.signUpCardContainer}>
          <h1 className={styles.signUpCardTitle}>
            Sign Up
          </h1>
          <h3 className={styles.signUpCardSubTitle}>
            Create an account
          </h3>
          <div className={styles.signUpButtonContainer1}>
            <SignUpButton text="As a Customer"/>
          </div>
          <div className={styles.signUpOr}>
            <div className={styles.signUpLine1}></div>
            <div className={styles.signUpOrText}>
              OR
            </div>
            <div className={styles.signUpLine2}></div>
          </div> 
          <div className={styles.signUpButtonContainer2}>
            <SignUpButton text="As an Agent"/>
          </div>
          <div className={styles.signUpLast}>
            Already have an account? 
            <Link href="/auth/login" className={styles.signUpLink}>
              Login
            </Link>
          </div>
        </div>
    );
}
