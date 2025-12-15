import styles from "./UpdateAlert.module.css";
import Image from "next/image";
import { useEffect, useState } from "react";

const updateAlertIcon = "/assets/update-alert-icon.svg";

export default function UpdateAlert({ hasUnsavedChanges }) {
  const [isAlertVisible, setIsAlertVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    let exitTimer;

    if (hasUnsavedChanges) {
      setIsAlertVisible(true);
      setIsExiting(false);
    } else if (isAlertVisible) {
      setIsExiting(true);
      exitTimer = setTimeout(() => {
        setIsAlertVisible(false);
        setIsExiting(false);
      }, 300);
    }

    return () => clearTimeout(exitTimer);
  }, [hasUnsavedChanges, isAlertVisible]);

  return (
    <>
      {isAlertVisible && (
        <div
          className={`${styles.unsavedChangesAlert} ${isExiting ? styles.exiting : ""}`}
        >
          <Image
            src={updateAlertIcon}
            alt="Warning Icon"
            width={20}
            height={20}
            className={styles.warningIcon}
          />
          <span>You have unsaved changes.</span>
        </div>
      )}
    </>
  );
}
