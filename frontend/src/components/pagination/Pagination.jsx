"use client";

import { useRouter, useSearchParams } from "next/navigation";
import styles from "./Pagination.module.css";

export default function Pagination({ currentPage, totalPages }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handlePageChange = (newPage) => {
    // Validate the page number
    if (newPage < 1 || newPage > totalPages || newPage === currentPage) {
      return;
    }

    const params = new URLSearchParams(searchParams.toString());
    params.set("page", newPage.toString());
    router.push(`?${params.toString()}`);
  };

  const renderPageNumbers = () => {
    const pages = [];

    if (totalPages <= 6) {
      // Show all pages if 6 or less
      for (let i = 1; i <= totalPages; i++) {
        pages.push(renderButton(i));
      }
    } else {
      // Show 1, 2, 3, 4, 5, ..., totalPages
      for (let i = 1; i <= 5; i++) {
        pages.push(renderButton(i));
      }

      pages.push(
        <span key="dots" className={styles.dots}>
          ...
        </span>,
      );

      // Show the final page number
      pages.push(renderButton(totalPages));
    }
    return pages;
  };

  const renderButton = (page) => (
    <button
      key={page}
      onClick={() => handlePageChange(page)}
      className={`${styles.pageButton} ${page === currentPage ? styles.active : ""}`}
      disabled={page === currentPage}
    >
      {page}
    </button>
  );

  const canGoPrev = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  return (
    <div className={styles.paginationWrapper}>
      {/* PREVIOUS BUTTON */}
      <button
        type="button"
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={!canGoPrev}
        className={styles.arrowButton}
      >
        {"<"}
      </button>

      <div className={styles.pageNumbers}>{renderPageNumbers()}</div>

      {/* NEXT BUTTON */}
      <button
        type="button"
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={!canGoNext}
        className={styles.arrowButton}
      >
        {">"}
      </button>
    </div>
  );
}
