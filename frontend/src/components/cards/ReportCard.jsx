"use client";

import Image from "next/image";
import DeleteModal from "@/components/modals/DeleteModal";
import ChatOverlay from "@/components/modals/ChatModal";
import { getAIChatSessionAction } from "@/actions/chatActions";
import ReportDetailsModal from "@/components/modals/ReportDetailsModal";
import { DeleteButton } from "@/components/buttons/Buttons";
import { useState, useEffect } from "react";
import styles from "./ReportCard.module.css";

export default function ReportCard({ report }) {
  const botIcon = "/assets/Robot-Head-icon.svg";
  const star = "/assets/star-icon.svg";
  const starFilled = "/assets/star-icon-dark.svg";
  const starHalf = "/assets/half-star-icon.svg";
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);

  const [activeChatSession, setActiveChatSession] = useState(null);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");

  const rating = parseFloat(report.investment_rating);

  useEffect(() => {
    if (chatError) {
      const timer = setTimeout(() => setChatError(""), 3000);
      return () => clearTimeout(timer);
    }
  }, [chatError]);

  const handleOpenChat = async () => {
    setChatError("");
    setIsChatLoading(true);

    const response = await getAIChatSessionAction(report.id);

    if (response && !response.error) {
      setActiveChatSession(response);
      setIsChatLoading(false);
    } else {
      setIsChatLoading(false);
      setChatError(response.error);
    }
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
        <div className={styles.infoRow}>
          Average Price: $ {report.avg_market_price}
        </div>
        <div className={styles.infoRow}>
          Average Price Per Sqft: ${report.avg_price_per_sqft}
        </div>
        <div className={styles.infoRow}>Area: {report.extracted_area}</div>
        <div className={styles.infoRow}>City: {report.extracted_city}</div>
        <div className={styles.ratingSection}>
          <span>Investment Rating: {rating.toFixed(2)}/5.00</span>
          <div className={styles.stars}>
            {[...Array(5)].map((_, i) => {
              const starValue = i + 1;
              let iconSrc;
              let altText;

              if (rating >= starValue) {
                iconSrc = starFilled;
                altText = "Full Star";
              } else if (rating > i && rating < starValue) {
                iconSrc = starHalf;
                altText = "Half Star";
              } else {
                iconSrc = star;
                altText = "Empty Star";
              }

              return (
                <Image
                  key={i}
                  src={iconSrc}
                  width={20}
                  height={18}
                  alt={altText}
                />
              );
            })}
          </div>
        </div>
      </div>
      <div className={styles.actions}>
        <div className={styles.aiButton}>
          {chatError ? (
            <div className={styles.chatErrorBubble}>{chatError}</div>
          ) : (
            <button
              className={styles.aiBtn}
              onClick={handleOpenChat}
              disabled={isChatLoading}
            >
              <Image
                src={botIcon}
                width={50}
                height={50}
                className={styles.aiIcon}
                alt="AI Assistant Icon"
              />
              {isChatLoading ? "Opening..." : "Smart Assistant"}
            </button>
          )}
        </div>
        <div className={styles.buttons}>
          <button
            className={styles.detailsBtn}
            onClick={() => setIsDetailsModalOpen(true)}
          >
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
        <ReportDetailsModal
          reportID={report.id}
          onClose={() => setIsDetailsModalOpen(false)}
        />
      )}
      {activeChatSession && (
        <ChatOverlay
          sessionData={activeChatSession}
          onClose={() => setActiveChatSession(null)}
        />
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
