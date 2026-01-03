"use client";

import styles from "./DeleteModal.module.css";
import { useState } from "react";
import { deleteUserAction } from "@/actions/userActions";
import { deletePropertyAction } from "@/actions/propertyActions";
import { deleteReportAction } from "@/actions/reportActions";
import { logoutAction } from "@/actions/authActions";
import { redirect } from "next/navigation";
export default function DeleteModal({
  title,
  userData,
  userRole,
  actionName,
  onCancel,
}) {
  const [deletionError, setDeletionError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const handleDeleteAction = async () => {
    try {
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
        } else if (response && response.success) {
          setSuccessMessage(
            response.success || "Account deleted successfully.",
          );
          setTimeout(async () => {
            onCancel();
            await logoutAction(false);
          }, 2000);
        }
      } else if (actionName === "deleteProperty") {
        const propertyId = userData.id;
        const response = await deletePropertyAction(propertyId);
        if (response && response.error) {
          setDeletionError(
            response.error ||
              "Property deletion failed due to an unknown server error.",
          );
        } else if (response && response.success) {
          setSuccessMessage(
            response.success || "Property deleted successfully.",
          );
          setTimeout(async () => {
            onCancel();
            redirect("/");
          }, 2000);
        }
      } else if (actionName === "deleteReport") {
        const reportId = userData.id;
        const response = await deleteReportAction(reportId);
        if (response && response.error) {
          setDeletionError(
            response.error ||
              "Report deletion failed due to an unknown server error.",
          );
        } else if (response && response.success) {
          setSuccessMessage(response.success || "Report deleted successfully.");
          setTimeout(async () => {
            onCancel();
            redirect("/dashboard");
          }, 2000);
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
        {successMessage && (
          <div className={styles.successMessage}>{successMessage}</div>
        )}
      </div>
    </div>
  );
}
