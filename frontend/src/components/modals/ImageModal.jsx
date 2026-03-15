"use client";

import Image from "next/image";
import styles from "./ImageModal.module.css";
import { CloseButton } from "@/components/buttons/Buttons";

export default function ImageModal({ image, isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <CloseButton onClick={onClose} />
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
