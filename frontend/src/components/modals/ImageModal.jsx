"use client";

import Image from "next/image";
import styles from "./ImageModal.module.css";

const crossIcon = "/assets/cross-icon.svg";

export default function ImageModal({ image, isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <button className={styles.closeButton} onClick={onClose}>
          <Image src={crossIcon} alt="Close Icon" width={30} height={30} />
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
  );
}
