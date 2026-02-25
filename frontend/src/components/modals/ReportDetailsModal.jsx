"use client";

import { useEffect, useState } from "react";
import { getReportAction } from "@/actions/reportActions";
import { CloseButton } from "@/components/buttons/Buttons";
import styles from "./ReportDetailsModal.module.css";

export default function ReportDetailsModal({ reportID, onClose }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.body.style.overflow = "hidden";
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await getReportAction(reportID);
        console.log("insight: ", response.ai_insight_summary);
        const reportData = response;
        setDetails(reportData);
      } catch (error) {
        console.error("Failed to fetch report details:", error);
      } finally {
        setLoading(false);
      }
    };

    if (reportID) fetchData();
    return () => {
      document.body.style.overflow = "auto";
    };
  }, [reportID]);

  if (!details) return null;

  return (
    <div className={styles.overlay}>
      <div className={styles.modalContent}>
        <CloseButton onClick={onClose} className={styles.closeButton} />
        {loading ? (
          <div className={styles.modalBodyX}>
            <p>Loading report details...</p>
          </div>
        ) : (
          <div className={styles.modalBody}>
            <div className={styles.modalHeader}>
              <div className={styles.modalMainTitle}>Details</div>
              <div className={styles.modalStatus}>Status: {details.status}</div>
            </div>

            <div className={styles.modalReportId}>Report ID: #{details.id}</div>

            <div className={styles.modalSection}>
              <div className={styles.sectionUnderline}>Property Details:</div>
              <div className={styles.insideSection}>
                Property Title: {details.property?.title}
              </div>
              <div className={styles.insideSection}>
                Area: {details.extracted_area}
              </div>
              <div className={styles.insideSection}>
                City: {details.extracted_city}
              </div>
              <div className={styles.insideSection}>
                Average Beds: {details.avg_beds}
              </div>
              <div className={styles.insideSection}>
                Average Baths: {details.avg_baths}
              </div>
            </div>

            <div className={styles.modalSection}>
              <div className={styles.sectionUnderline}>Market Details:</div>
              <div className={styles.insideSection}>
                Average Market Price: ${details.avg_market_price}
              </div>
              <div className={styles.insideSection}>
                Average Price Per Sqft: ${details.avg_price_per_sqft}
              </div>
              <div className={styles.insideSection}>
                Investment Rating:{" "}
                {details.investment_rating
                  ? parseFloat(details.investment_rating).toFixed(2)
                  : "N/A"}
                /5.00
              </div>
            </div>

            <div className={styles.modalSection}>
              <div className={styles.sectionUnderline}>AI Summary:</div>
              <div className={styles.aiSummaryBox}>
                {details.ai_insight_summary || "No summary available."}
                {console.log("details insight: ", details.ai_insight_summary)}
              </div>
            </div>

            <div className={styles.modalFooter}>
              <span>Created By: {details.user?.username}</span>
              <span suppressHydrationWarning>
                Created At: {new Date(details.created_at).toLocaleDateString()},{" "}
                {new Date(details.created_at).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
