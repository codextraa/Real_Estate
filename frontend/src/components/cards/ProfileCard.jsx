import styles from "./ProfileCard.module.css";
import ProfileForm from "@/components/forms/ProfileForm";

export default function ProfileCard() {
  return (
    <div className={styles.ProfileInfoContainer}>
      <div className={styles.ProfileCardTitle}>Profile Information</div>
      <div className={styles.ProfileFormContainer}>
        <ProfileForm />
      </div>
    </div>
  );
}
