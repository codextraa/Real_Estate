import styles from "./ProfileCard.module.css";
import EditProfileForm from "@/components/forms/ProfileForm";
import { GlobalButton } from "@/components/buttons/Buttons";
export default function ProfileCard({ userData }) {
  return (
    <div className={styles.ProfileInfoContainer}>
      <div className={styles.ProfileCardTitle}>Profile Information</div>
      <div className={styles.storedInfos}>
        <label className={styles.emailLabel}>Email Address</label>
        <div className={styles.storedContent}>{userData.email}</div>
        <label className={styles.FirstNameLabel}>First Name</label>
        <div className={styles.storedContent}>{userData.first_name}</div>
        <label className={styles.lastNameLabel}>Last Name</label>
        <div className={styles.storedContent}>{userData.last_name}</div>
        <label className={styles.usernameLabel}>Username</label>
        <div className={styles.storedContent}>{userData.username}</div>
      </div>
      <div className={styles.buttonContainer}>
        <div className={styles.button}>
          <GlobalButton
            text="Edit Profile"
            onClick={() => {
              userData.user ? (
                <EditProfileForm userData={userData.user} />
              ) : (
                <EditProfileForm userData={userData} />
              );
            }}
          />
          {/* agent edit profile                           customer edit profile */}
        </div>
      </div>
    </div>
  );
}
