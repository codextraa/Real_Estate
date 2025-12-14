// components/cards/PropertyImageCard.jsx
"use client";

import { useState } from "react";
import Image from "next/image";
import styles from "./PropertyImageCard.module.css"; // Create this CSS file

export default function PropertyImageCard({ image }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const openModal = () => setIsModalOpen(true);
  const closeModal = () => setIsModalOpen(false);

  return (
    <>
      <div className={styles.imageCard} onClick={openModal}>
        <Image
          src={image}
          alt="Property Image"
          width={700}
          height={400}
          className={styles.propertyImage}
        />
        <div className={styles.clickOverlay}>Click to Enlarge</div>
      </div>

      {isModalOpen && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div
            className={styles.modalContent}
            onClick={(e) => e.stopPropagation()}
          >
            <button className={styles.closeButton} onClick={closeModal}>
              &times;
            </button>
            <Image
              src={image}
              alt="Enlarged Property Image"
              layout="responsive"
              width={1600}
              height={900}
              className={styles.modalImage}
            />
          </div>
        </div>
      )}
    </>
  );
}
