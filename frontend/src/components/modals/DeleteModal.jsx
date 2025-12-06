"use client";

import styles from "./DeleteModal.module.css";
import { useState } from "react";
import { deleteUserAction } from "@/actions/userActions";
export default function DeleteModal({
  title,
  userData,
  userRole,
  actionName,
  onCancel,
}) {
  // const router = useRouter();
  const [deletionError, setDeletionError] = useState(null);
  const handleDeleteAction = async () => {
    try {
      if (actionName === "deleteUser") {
        if (!userData || !userRole) {
          throw new Error("Missing userData or userRole");
        } else {
          const userId = userRole === "Agent" ? userData.user.id : userData.id;
          const response = await deleteUserAction(userId, userRole);
          if (response && response.error) {
            setDeletionError(
              response.error ||
                "Account deletion failed due to an unknown server error.",
            );
          }
        }
      }
    } catch (error) {
      console.error("Error deleting account:", error);
      setDeletionError(
        error.message || "A client-side error occurred during deletion.",
      );
    }
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <div className={styles.modalText}>{title}</div>
        <div className={styles.buttonContainer}>
          <button
            type="button"
            onClick={handleDeleteAction}
            className={styles.yesButton}
          >
            Yes
          </button>
          <button type="button" onClick={onCancel} className={styles.noButton}>
            No
          </button>
        </div>
        {deletionError && (
          <div className={styles.errorMessage}>{deletionError}</div>
        )}
      </div>
    </div>
  );
}
