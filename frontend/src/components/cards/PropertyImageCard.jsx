"use client";

import { useState } from "react";
import Image from "next/image";
import styles from "./PropertyImageCard.module.css";

const crossIcon = "/assets/cross-icon.svg";
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
          width={960}
          height={700}
          className={styles.propertyImage}
        />
      </div>

      {isModalOpen && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div
            className={styles.modalContent}
            onClick={(e) => e.stopPropagation()}
          >
            <button className={styles.closeButton} onClick={closeModal}>
              <Image
                src={crossIcon}
                alt="Close Icon"
                width={100}
                height={100}
                className={styles.crossIcon}
              />
            </button>
            <Image
              src={image}
              alt="Enlarged Property Image"
              layout="responsive"
              width={2400}
              height={1200}
              className={styles.modalImage}
            />
          </div>
        </div>
      )}
    </>
  );
}
