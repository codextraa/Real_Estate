import Link from "next/link";
import Image from "next/image";
import { getUserIdAction } from "@/actions/authActions";
import { BackButton } from "@/components/buttons/Buttons";
import styles from "./ProfileCard.module.css";

export default async function ProfileCard({ userData, userId, userRole }) {
  const actionUserId = await getUserIdAction();
  let isOwnProfile = true;

  if (actionUserId != userId) {
    isOwnProfile = false;
  }

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
              <label className={styles.aboutMeLabel}>About Me</label>
              <div className={styles.storedText}>{userData.bio}</div>
            </div>
            <div className={styles.profileDetails}>
              <h1 className={styles.subTitle2}>Details</h1>
              <div className={styles.profileInfos}>
                <div
                  className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
                >
                  <label className={styles.profileLabel}>Email Address</label>
                  <div className={styles.storedContent}>
                    {userData.user.email}
                  </div>
                </div>
                <div
                  className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
                >
                  <label className={styles.profileLabel}>First Name</label>
                  <div className={styles.storedContent}>
                    {userData.user.first_name}
                  </div>
                </div>
                <div
                  className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
                >
                  <label className={styles.profileLabel}>Last Name</label>
                  <div className={styles.storedContent}>
                    {userData.user.last_name}
                  </div>
                </div>
                <div
                  className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
                >
                  <label className={styles.profileLabel}>Username</label>
                  <div className={styles.storedContent}>
                    {userData.user.username}
                  </div>
                </div>
              </div>
            </div>
            <div className={styles.profileDetails}>
              <h1 className={styles.subTitle2}>Company Information</h1>
              <div
                className={`${styles.profileBoxLabel} ${styles.profileBoxLabelAgent}`}
              >
                <label className={styles.profileLabel}>Company Name</label>
                <div className={styles.storedContent}>
                  {userData.company_name}
                </div>
              </div>
            </div>
            <div className={styles.agentProfileButtonContainer}>
              {!isOwnProfile && <BackButton text="Go Back" />}
              {isOwnProfile && (
                <>
                  <Link
                    href={`/profile/${userData.user.slug}/edit`}
                    className={`${styles.editProfileButton} ${styles.editAgentProfileButton}`}
                  >
                    Edit Profile
                  </Link>
                  <Link
                    href={`/dashboard?tab=my-listings`}
                    className={`${styles.editProfileButton} ${styles.myListingsButton}`}
                  >
                    View Listings
                    <Image
                      className={styles.arrowIcon}
                      src="/assets/button-arrow.svg"
                      alt="Right Arrow Icon"
                      width={53}
                      height={45}
                    />
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className={`${styles.profileInfos} ${styles.profileInfosUser}`}>
            <div className={styles.profileBoxLabel}>
              <label className={styles.profileLabel}>Email Address</label>
              <div className={styles.storedContent}>{userData.email}</div>
            </div>
            <div className={styles.profileBoxLabel}>
              <label className={styles.profileLabel}>First Name</label>
              <div className={styles.storedContent}>{userData.first_name}</div>
            </div>
            <div className={styles.profileBoxLabel}>
              <label className={styles.profileLabel}>Last Name</label>
              <div className={styles.storedContent}>{userData.last_name}</div>
            </div>
            <div className={styles.profileBoxLabel}>
              <label className={styles.profileLabel}>Username</label>
              <div className={styles.storedContent}>{userData.username}</div>
            </div>
          </div>
          <div className={styles.profileDetailButtonContainer}>
            {!isOwnProfile && <BackButton text="Go Back" />}
            {isOwnProfile && (
              <Link
                href={`/profile/${userData.slug}/edit`}
                className={styles.editProfileButton}
              >
                Edit Profile
              </Link>
            )}
          </div>
        </>
      )}
    </div>
  );
}
