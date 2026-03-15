"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import styles from "./PropertyDetailCard.module.css";
import Image from "next/image";
import { DeleteButton } from "@/components/buttons/Buttons";
import DeleteModal from "@/components/modals/DeleteModal";
import { getUserIdAction } from "@/actions/authActions";
import { createReportAction } from "@/actions/reportActions";

const locationIcon = "/assets/location-icon.svg";
export default function PropertyDetailCard({ property }) {
  const [userId, setUserId] = useState(null);
  const [isClient, setIsClient] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");

  const formatAddress = (addressString) => {
    if (!addressString) return "";
    const parts = addressString.split(",").map((p) => p.trim());
    const addressObj = {};

    parts.forEach((part) => {
      const [key, value] = part.split("=");
      if (key && value) {
        addressObj[key.trim()] = value.trim();
      }
    });

    const formattedParts = [];

    if (addressObj.flat_no) formattedParts.push(`Flat ${addressObj.flat_no}`);
    if (addressObj.house_no)
      formattedParts.push(`House ${addressObj.house_no}`);
    if (addressObj.street) formattedParts.push(addressObj.street);
    if (addressObj.area) formattedParts.push(addressObj.area);
    if (addressObj.city) formattedParts.push(addressObj.city);
    if (addressObj.state) formattedParts.push(addressObj.state);
    if (addressObj.country) formattedParts.push(addressObj.country);

    return formattedParts.join(", ") + ".";
  };

  const openDeleteModal = () => {
    setIsDeleteModalOpen(true);
    document.body.style.overflow = "hidden";
  };

  const closeDeleteModal = () => {
    setIsDeleteModalOpen(false);
    document.body.style.overflow = "auto";
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setStatus("idle");

    try {
      const response = await createReportAction(property.id);

      if (response?.success) {
        setStatus("success");
        setMessage(response?.success);
      } else {
        setStatus("error");
        setMessage(response?.error);
      }
    } catch (error) {
      console.error("Report Action Failed:", error);
      setStatus("error");
      setMessage("Report Generation Failed");
    } finally {
      setLoading(false);
      setTimeout(() => {
        setStatus("idle");
      }, 3000);
    }
  };

  async function fetchUserId() {
    try {
      const id = await getUserIdAction();
      setUserId(id);
    } catch (error) {
      console.error("Failed to fetch user ID:", error);
      setUserId(null);
    }
  }

  useEffect(() => {
    setIsClient(true);
    if (isClient) {
      fetchUserId();
    }
  }, [isClient]);
  return (
    <div className={styles.propertyDetailCard}>
      <div className={styles.locationContainer}>
        <div className={styles.location}>
          <Image
            src={locationIcon}
            alt="Location Icon"
            width={100}
            height={100}
            className={styles.locationIcon}
          />
          <div className={styles.locationText}>
            {formatAddress(property.address)}
          </div>
        </div>
      </div>
      <div className={styles.details}>
        <div className={styles.detailText}>Details</div>
        <div className={styles.detailItem}>
          <div className={styles.detailItemContainer}>
            <span className={styles.detailItemBed}>{property.beds}</span>
            <span className={styles.detailItemLabel}>Beds</span>
          </div>
          <div className={styles.detailItemContainer}>
            <span className={styles.detailItemBath}>{property.baths}</span>
            <span className={styles.detailItemLabel}>Baths</span>
          </div>
          <div className={styles.detailItemContainer}>
            <span className={styles.detailItemArea}>{property.area_sqft}</span>
            <span className={styles.detailItemLabel}>Sqft</span>
          </div>
        </div>
      </div>
      <div className={styles.priceContainer}>
        <div className={styles.priceLabel}>Price </div>
        <div className={styles.pricePayment}>
          <span className={styles.priceValue}>${property.price}</span>
          <div className={styles.button}>
            {status === "idle" ? (
              <button
                className={styles.paymentButton}
                onClick={handleAnalyze}
                disabled={loading}
              >
                {loading ? "Analyzing..." : "Analyze"}
              </button>
            ) : (
              <span
                className={
                  status === "success" ? styles.successMsg : styles.errorMsg
                }
              >
                {message || "Report Generation Failed"}
              </span>
            )}
          </div>
        </div>
      </div>
      <div className={styles.agentContainer}>
        <div className={styles.agentLabel}>Agent</div>
        <div className={styles.agentInfo}>
          <div className={styles.agentNameContainer}>
            <div className={styles.agentName}>
              {property.agent.first_name} {property.agent.last_name}
            </div>
            <Link
              href={`/profile/${property.agent.slug}?user_id=${property.agent.user_id}&user_role=${property.agent.user_role}`}
              className={styles.agentContact}
            >
              Contact
            </Link>
          </div>
          <div className={styles.agentImageContainer}>
            <Image
              src={property.agent.image_url}
              alt="Agent Picture"
              width={100}
              height={100}
              className={styles.agentImage}
            />
          </div>
        </div>
      </div>
      {userId == property.agent.user_id && (
        <div className={styles.formProfileButtons}>
          <div className={styles.profileDetailButtonContainer}>
            <Link
              href={`/properties/${property.slug}/edit`}
              className={styles.editProfileButton}
            >
              Update
            </Link>
          </div>
          <div className={styles.deleteProfileButton}>
            <DeleteButton
              text="Delete"
              type="button"
              onClick={openDeleteModal}
              className={styles.deleteButton}
            />
          </div>
        </div>
      )}
      {isDeleteModalOpen && (
        <DeleteModal
          title="Are you sure you want to delete your property?"
          userData={property}
          userRole="Agent"
          actionName="deleteProperty"
          onCancel={closeDeleteModal}
        />
      )}
    </div>
  );
}
