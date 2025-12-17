"use client";

import { useRouter, useSearchParams } from "next/navigation";
import styles from "./Pagination.module.css";

export default function Pagination({ currentPage, totalPages }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > totalPages || newPage === currentPage) {
      return;
    }

    const params = new URLSearchParams(searchParams.toString());
    params.set("page", newPage.toString());
    router.push(`?${params.toString()}`);
  };

  const hasPrev = currentPage > 1;
  const hasNext = currentPage < totalPages;

  const pageNumbers = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className={styles.pagination}>
      <button
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={!hasPrev}
        className={styles.button}
      >
        Previous
      </button>
      <div className={styles.pageNumbers}>
        {pageNumbers.map((page) => (
          <button
            key={page}
            onClick={() => handlePageChange(page)}
            className={`${styles.button} ${page === currentPage ? styles.active : ""}`}
            disabled={page === currentPage}
          >
            {page}
          </button>
        ))}
      </div>
      <button
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={!hasNext}
        className={styles.button}
      >
        Next
      </button>
    </div>
  );
}
