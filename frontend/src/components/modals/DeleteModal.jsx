"use client";

import styles from "./DeleteModal.module.css";
import { deleteUserAction } from "@/actions/userActions";
import { redirect } from "next/navigation";
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
          await deleteUserAction(userId, userRole);
          setTimeout(() => {
            redirect("/auth/login");
          }, 1500);
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
          <button type="button" onClick={onCancel} className={styles.noButton}>
            No
          </button>
          <button
            type="button"
            onClick={handleDeleteAction}
            className={styles.yesButton}
          >
            Yes
          </button>
        </div>
      </div>
    </div>
  );
}
