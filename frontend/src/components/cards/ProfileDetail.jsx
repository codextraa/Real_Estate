import styles from "./ProfileDetail.module.css";

export default function ProfileDetail({ userData }) {
  return (
    <div className={styles.storedInfos}>
      <label className={styles.emailLabel}>Email Address</label>
      <div className={styles.storedContent}>{userData.email}</div>
      <></>
      <label className={styles.FirstNameLabel}>First Name</label>
      <div className={styles.storedContent}>{userData.first_name}</div>
      <label className={styles.lastNameLabel}>Last Name</label>
      <div className={styles.storedContent}>{userData.last_name}</div>
      <label className={styles.usernameLabel}>Username</label>
      <div className={styles.storedContent}>{userData.username}</div>
    </div>
  );
}
