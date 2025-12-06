"use client";

import styles from "./DeleteModal.module.css";
import { deleteUserAction } from "@/actions/userActions";
export default function DeleteModal({
  title,
  userData,
  userRole,
  actionName,
  onCancel,
}) {
  const handleDeleteAction = async () => {
    try {
      if (actionName === "deleteUser") {
        if (!userData || !userRole) {
          throw new Error("Missing userData or userRole");
        } else {
          const userId = userRole === "Agent" ? userData.user.id : userData.id;
          const response = await deleteUserAction(userId, userRole);
          console.log(response.success);
        }
      }
    } catch (error) {
      console.error("Error deleting account:", error);
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
      </div>
    </div>
  );
}
