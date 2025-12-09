"use client";

import styles from "./DeleteModal.module.css";
import { useState } from "react";
import { deleteUserAction } from "@/actions/userActions";
import { useRouter } from "next/navigation";
import { DEFAULT_LOGIN_REDIRECT } from "@/route";
export default function DeleteModal({
  title,
  userData,
  userRole,
  actionName,
  onCancel,
}) {
  const router = useRouter();
  const [deletionError, setDeletionError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const handleDeleteAction = async () => {
    if (isDeleting) return; // Prevent multiple clicks
    try {
      setIsDeleting(true);
      if (actionName === "deleteUser") {
        if (!userData || !userRole) {
          throw new Error("Missing userData or userRole");
        }

        const userId = userRole === "Agent" ? userData.user.id : userData.id;
        const response = await deleteUserAction(userId, userRole);
        if (response && response.error) {
          setDeletionError(
            response.error ||
              "Account deletion failed due to an unknown server error.",
          );
          setIsDeleting(false);
        } else if (response && response.success) {
          setSuccessMessage(
            response.success || "Account deleted successfully.",
          );
          setTimeout(async () => {
            router.push(DEFAULT_LOGIN_REDIRECT);
          }, 5500);
        }
      }
    } catch (error) {
      console.error("Error deleting account:", error);
      setDeletionError(
        error.message || "A client-side error occurred during deletion.",
      );
      setIsDeleting(false);
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
        {successMessage && (
          <div className={styles.successMessage}>{successMessage}</div>
        )}
      </div>
    </div>
  );
}
