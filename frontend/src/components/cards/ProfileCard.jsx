import Link from "next/link";
import Image from "next/image";
import styles from "./ProfileCard.module.css";
import { GlobalButton } from "@/components/buttons/Buttons";

export default function ProfileCard({ userData, userRole }) {
  return (
    <div className={styles.profileInfoContainer}>
      <div className={styles.profileDetailTitle}>Profile Information</div>
      {userRole == "Agent" ? (
        <div className={styles.agentProfileContainer}>
          <div className={styles.ImageContainer}>
            <Image
              src={userData.image_url}
              alt="Profile Picture"
              width={500}
              height={500}
              priority
            />
          </div>
          <div className={styles.profileContainer}>
            <div className={styles.bioInfo}>
              <h1 className={styles.subTitle}>
                {userData.user.first_name + " " + userData.user.last_name}
              </h1>
              <div className={styles.storedContent}>{userData.bio}</div>
            </div>
            <div className={styles.profileInfos}>
              <h1 className={styles.subTitle2}>Details</h1>
              <label className={styles.profileLabel}>Email Address</label>
              <div className={styles.storedContent}>{userData.user.email}</div>
              <label className={styles.profileLabel}>First Name</label>
              <div className={styles.storedContent}>
                {userData.user.first_name}
              </div>
              <label className={styles.profileLabel}>Last Name</label>
              <div className={styles.storedContent}>
                {userData.user.last_name}
              </div>
              <label className={styles.profileLabel}>Username</label>
              <div className={styles.storedContent}>
                {userData.user.username}
              </div>
            </div>
            <div className={styles.companyInfo}>
              <h1 className={styles.subTitle2}>Company Information</h1>
              <label className={styles.profileLabel}>Company Name</label>
              <div className={styles.storedContent}>
                {userData.company_name}
              </div>
            </div>
            <div className={styles.agentProfileDetailButtonContainer}>
              <Link
                href={`/profile/${userData.slug}/edit`}
                className={styles.editProfileButton}
              >
                <GlobalButton text="Edit Profile" />
              </Link>
              <Link href={`/my-listings`} className={styles.myListingsButton}>
                <GlobalButton text="My Listings" />
              </Link>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className={styles.profileInfos}>
            <label className={styles.profileLabel}>Email Address</label>
            <div className={styles.storedContent}>{userData.email}</div>
            <label className={styles.profileLabel}>First Name</label>
            <div className={styles.storedContent}>{userData.first_name}</div>
            <label className={styles.profileLabel}>Last Name</label>
            <div className={styles.storedContent}>{userData.last_name}</div>
            <label className={styles.profileLabel}>Username</label>
            <div className={styles.storedContent}>{userData.username}</div>
          </div>
          <div className={styles.profileDetailButtonContainer}>
            <Link
              href={`/profile/${userData.slug}/edit`}
              className={styles.editProfileButton}
            >
              <GlobalButton text="Edit Profile" />
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
