"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import ImageModal from "@/components/modals/ImageModal";
import styles from "./PropertyImageCard.module.css";

export default function PropertyImageCard({ image }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    if (isModalOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "auto";
    }

    return () => {
      document.body.style.overflow = "auto";
    };
  }, [isModalOpen]);

  return (
    <>
      <div className={styles.imageCard} onClick={() => setIsModalOpen(true)}>
        <Image
          src={image}
          alt="Property Image"
          width={960}
          height={700}
          className={styles.propertyImage}
        />
      </div>

      <ImageModal
        image={image}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
}
