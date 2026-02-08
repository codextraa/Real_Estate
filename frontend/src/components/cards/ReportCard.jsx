"use client";
import Image from "next/image";
import { getReportAction } from "@/actions/reportActions";
import DeleteModal from "../modals/DeleteModal";
import { DeleteButton } from "../buttons/Buttons";
import { useState } from "react";
import styles from "./ReportCard.module.css";

export default function ReportCard({ report }) {
  const botIcon = "/assets/Robot-Head-icon.svg";
  const closeIcon = "/assets/cross-icon.svg";
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [details, setDetails] = useState(null);
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
      <div className={styles.cardContent}>
        <div className={styles.reportId}>Report #{report.id}</div>
        <div className={styles.infoRow}>Average Price: ${report.avg_price}</div>
        <div className={styles.infoRow}>
          Price Per sqft: ${report.avg_price_per_sqft}
        </div>
        <div className={styles.infoRow}>Area: {report.extracted_area} sqft</div>
        <div className={styles.ratingSection}>
          <span>Investment Rating: {rating.toFixed(2)}/5.0</span>
          <div className={styles.stars}>
            {[...Array(5)].map((_, i) => {
              const starValue = i + 1;

              if (rating >= starValue) {
                return (
                  <span key={i} className={styles.starFilled}>
                    ★
                  </span>
                );
              } else if (rating > i && rating < starValue) {
                return (
                  <span key={i} className={styles.starHalf}>
                    ★
                  </span>
                );
              } else {
                return (
                  <span key={i} className={styles.starEmpty}>
                    ★
                  </span>
                );
              }
            })}
          </div>
        </div>
      </div>
      <div className={styles.actions}>
        <div className={styles.aiButton}>
          <button className={styles.aiBtn}>
            <Image
              src={botIcon}
              width={30}
              height={30}
              alt="AI Assistant Icon"
            />
            Smart Assistant
          </button>
        </div>
        <div className={styles.buttons}>
          <button className={styles.detailsBtn} onClick={handleOpenDetails}>
            Details
          </button>
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
              <Image src={closeIcon} width={20} height={20} alt="Close" />
            </button>
            <div className={styles.modalBody}>
              <div className={styles.modalHeader}>
                <div className={styles.modalMainTitle}>Details</div>
                <div className={styles.modalStatus}>
                  Status: {report.status}
                </div>
              </div>

              <div className={styles.modalReportId}>
                Report ID: #{report.id}
              </div>

              <div className={styles.modalSection}>
                <div className={styles.sectionUnderline}>Property Details:</div>
                <div>
                  Property Title:{" "}
                  <strong>{details?.title || "Something"}</strong>
                </div>
                <div>
                  Area: <strong>{report.extracted_area}</strong>
                </div>
                <div>
                  City: <strong>{report.extracted_city}</strong>
                </div>
                <div>
                  Average beds: <strong>{details?.beds || 2}</strong>
                </div>
                <div>
                  Average Baths: <strong>{details?.baths || 2}</strong>
                </div>
              </div>

              <div className={styles.modalSection}>
                <div className={styles.sectionUnderline}>Market Details:</div>
                <div>
                  Average Market Price:{" "}
                  <strong>${report.avg_market_price}</strong>
                </div>
                <div>
                  Average Price Per sqft:{" "}
                  <strong>${report.avg_price_per_sqft}</strong>
                </div>
                <div>
                  Investment Rating: <strong>{rating}/5.00</strong>
                </div>
              </div>

              <div className={styles.modalSection}>
                <div className={styles.sectionUnderline}>AI Summary:</div>
                <div className={styles.aiSummaryBox}>
                  {loading
                    ? "Analyzing data..."
                    : details?.ai_summary || "No summary available."}
                </div>
              </div>

              <div className={styles.modalFooter}>
                <span>Created By: {details?.username || "username"}</span>
                <span>Created At: {report.created_at || "12/12/2012"}</span>
              </div>
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
