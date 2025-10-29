'use client';

import { useState } from "react";
import ProfileDetail from "@/components/cards/ProfileDetail";
import ProfileForm from "@/components/forms/ProfileForm";
import { GlobalButton } from "@/components/buttons/Buttons";
import styles from "@/components/wrappers/ProfileWrapper.module.css";

export default function ProfileWrapper({ userData }) {
  const [isEditing, setIsEditing] = useState(false);

  const handleEditToggle = () => {
    setIsEditing(!isEditing);
  };

  return (
    <div className={styles.ProfileInfoContainer}>
      <div className={styles.ProfileDetailTitle}>
        {isEditing ? "Edit Profile Information" : "Profile Information"}
      </div>
      {isEditing ? (
        <>
          <ProfileForm userData={userData} />
          <div className={styles.ProfileFormButtonContainer}>
            <GlobalButton
              text="Cancel"
              onClick={handleEditToggle}
            />
          </div>
        </>
      ) : (
        <>
          <ProfileDetail userData={userData} />
          <div className={styles.ProfileDetailButtonContainer}>
            <GlobalButton
              text="Edit Profile"
              onClick={handleEditToggle}
            />
          </div>
        </>
      )}
    </div>
  );
}