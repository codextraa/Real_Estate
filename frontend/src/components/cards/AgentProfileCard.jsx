import styles from "./AgentProfileCard.module.css";
import EditProfileForm2 from "@/components/forms/ProfileForm";
import { GlobalButton } from "@/components/buttons/Buttons";
import { Home } from "next/navigation";

export default function AgentProfileCard({ userData }) {
  const name = userData.user.first_name + " " + userData.user.last_name;
  return (
    <div className={styles.ProfileInfoContainer}>
      <div className={styles.storedContent1}>
        <div className={styles.ProfileCardTitle}>Profile Information</div>
        <div className={styles.img}>image</div>
        <div className={styles.agentName}>{name}</div>
        <label className={styles.aboutMeLabel}>About Me</label>
        <div className={styles.aboutMe}>{userData.bio}</div>
      </div>

      <div className={styles.storedContent2}>
        <h1 className={styles.details}>Details</h1>
        <div className={styles.storedInfos}>
          <label className={styles.emailLabel}>Email Address</label>
          <div className={styles.storedContent2}>{userData.user.email}</div>
          <label className={styles.FirstNameLabel}>First Name</label>
          <div className={styles.storedContent2}>
            {userData.user.first_name}
          </div>
          <label className={styles.lastNameLabel}>Last Name</label>
          <div className={styles.storedContent2}>{userData.user.last_name}</div>
          <label className={styles.usernameLabel}>Username</label>
          <div className={styles.storedContent2}>{userData.user.username}</div>
          <h1 className={styles.companyInfod}>Company Information</h1>
          <label className={styles.usernameLabel}>Company Name</label>
          <div className={styles.storedContent2}>{userData.company_name}</div>
        </div>

        <div className={styles.buttonContainer}>
          <div className={styles.button}>
            <GlobalButton
              text="Edit Profile"
              onClick={() => {
                <EditProfileForm2 userData={userData.user} />;
              }}
            />
          </div>
          <div className={styles.viewListingsButton}>
            <GlobalButton
              text="View Listings"
              onClick={() => {
                Home;
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
