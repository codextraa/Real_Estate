"use client";
import { getReportAction } from "@/actions/reportActions";
import DeleteModal from "../modals/DeleteModal";
import { DeleteButton } from "../buttons/Buttons";
import { useState } from "react";
import styles from "./ReportCard.module.css";

export default function ReportCard({ report }) {
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false); // New State
  const [details, setDetails] = useState(null); // New State
  const [loading, setLoading] = useState(false);

  const rating = parseFloat(report.investment_rating);
  const handleOpenDetails = async () => {
    setIsDetailsModalOpen(true);
    setLoading(true);
    document.body.style.overflow = "hidden";
    const response = await getReportAction(report.id);
    if (response?.data) setDetails(response.data);
    setLoading(false);
  };

  const closeDetails = () => {
    setIsDetailsModalOpen(false);
    document.body.style.overflow = "auto";
  };

  const openDeleteModal = () => {
    setIsDeleteModalOpen(true);
    document.body.style.overflow = "hidden";
  };

  const closeDeleteModal = () => {
    setIsDeleteModalOpen(false);
    document.body.style.overflow = "auto";
  };

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h3>Report #{report.id}</h3>
        <span
          className={`${styles.statusBadge} ${styles[report.status.toLowerCase()]}`}
        >
          {report.status}
        </span>
      </div>

      <div className={styles.body}>
        <div className={styles.infoRow}>
          <span>Average Price:</span>{" "}
          <strong>${report.avg_market_price}</strong>
        </div>
        <div className={styles.infoRow}>
          <span>Price Per Sqft:</span>{" "}
          <strong>${report.avg_price_per_sqft}</strong>
        </div>
        <div className={styles.infoRow}>
          <span>Area:</span>{" "}
          <strong>
            {report.extracted_area}, {report.extracted_city}
          </strong>
        </div>

        <div className={styles.ratingSection}>
          <span>Investment Rating: {rating}/5.0</span>
          <div className={styles.stars}>
            {[...Array(5)].map((_, i) => (
              <span
                key={i}
                className={
                  i < Math.floor(rating) ? styles.starFilled : styles.starEmpty
                }
              >
                ★
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className={styles.actions}>
        <button className={styles.detailsBtn} onClick={handleOpenDetails}>
          Details
        </button>
        <div className={styles.deleteProfileButton}>
          <DeleteButton
            text="Delete"
            type="button"
            onClick={openDeleteModal}
            className={styles.deleteButton}
          />
        </div>
      </div>
      {isDetailsModalOpen && (
        <div className={styles.overlay}>
          <div className={styles.modalContent}>
            <button className={styles.closeCircle} onClick={closeDetails}>
              X
            </button>

            <div className={styles.modalHeader}>
              <h2 className={styles.modalMainTitle}>Details</h2>
              <span className={styles.modalStatus}>
                Status: {report.status}
              </span>
            </div>

            <p className={styles.modalReportId}>Report ID: #{report.id}</p>

            <section className={styles.modalSection}>
              <h4 className={styles.sectionUnderline}>Property Details:</h4>
              <p>
                Property Title: <strong>{details?.title || "Something"}</strong>
              </p>
              <p>
                Area: <strong>{report.extracted_area}</strong>
              </p>
              <p>
                City: <strong>{report.extracted_city}</strong>
              </p>
              <p>
                Average beds: <strong>{details?.beds || 2}</strong>
              </p>
              <p>
                Average Baths: <strong>{details?.baths || 2}</strong>
              </p>
            </section>

            <section className={styles.modalSection}>
              <h4 className={styles.sectionUnderline}>Market Details:</h4>
              <p>
                Average Market Price:{" "}
                <strong>${report.avg_market_price}</strong>
              </p>
              <p>
                Average Price Per sqft:{" "}
                <strong>${report.avg_price_per_sqft}</strong>
              </p>
              <p>
                Investment Rating: <strong>{rating}/5.00</strong>
              </p>
            </section>

            <section className={styles.modalSection}>
              <h4 className={styles.sectionUnderline}>AI Summary:</h4>
              <div className={styles.aiSummaryBox}>
                {loading
                  ? "Analyzing data..."
                  : details?.ai_summary || "No summary available."}
              </div>
            </section>

            <div className={styles.modalFooter}>
              <span>Created By: {details?.username || "username"}</span>
              <span>Created At: {report.created_at || "12/12/2012"}</span>
            </div>
          </div>
        </div>
      )}
      {isDeleteModalOpen && (
        <DeleteModal
          title="Are you sure you want to delete your report?"
          userData={report}
          userRole="Agent"
          actionName="deleteReport"
          onCancel={closeDeleteModal}
        />
      )}
    </div>
  );
}
