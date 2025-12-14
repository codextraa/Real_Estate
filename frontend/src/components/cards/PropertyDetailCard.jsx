"use client";
import styles from "./PropertyImageCard.module.css";
import Image from "next/image";
import { FormButton } from "../buttons/Buttons";

const locationIcon = "/assets/location-icon.svg";
export default function PropertyDetailCard({ property }) {
  return (
    <div className={styles.propertyDetailCard}>
      <div className={styles.location}>
        <Image
          src={locationIcon}
          alt="Location Icon"
          width={20}
          height={20}
          className={styles.locationIcon}
        />
        <div className={styles.locationText}>{property.address}</div>
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
        <div className={styles.price}>
          <span className={styles.priceLabel}>Price </span>
          <span className={styles.priceValue}>${property.price}</span>
        </div>
        <div className={styles.payment}>
          <FormButton
            text="Payment Options >"
            onClick={() => {}}
            type="button"
            className={styles.paymentButton}
          />
        </div>
      </div>
      <div className={styles.agentContainer}>
        <div className={styles.agentLabel}>Agent</div>
        <div className={styles.agentInfo}>
          <div className={styles.agentNameContainer}>
            <div className={styles.agentName}>
              {property.agent.first_name} {property.agent.last_name}
            </div>
            <div className={styles.agentContact}>Contact</div>
          </div>
          <div className={styles.agentImageContainer}>
            <Image
              src={property.agent.image_url}
              alt="Agent Picture"
              width={60}
              height={60}
              className={styles.agentImage}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
