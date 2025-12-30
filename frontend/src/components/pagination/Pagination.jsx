"use client";

import { useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import styles from "./Pagination.module.css";

const rightArrowIcon = "/assets/right-arrow.svg";
const leftArrowIcon = "/assets/left-arrow.svg";
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
    // maxVisibleButtons controls the "buffer" around the current page
    const buffer = 1;

    if (totalPages <= 7) {
      // If total pages are few, show them all
      for (let i = 1; i <= totalPages; i++) {
        pages.push(renderButton(i));
      }
    } else {
      // First Page
      pages.push(renderButton(1));

      // Calculate window
      let startPage = Math.max(2, currentPage - buffer);
      let endPage = Math.min(totalPages - 1, currentPage + buffer);

      // Consistent amount of pages in edges
      if (currentPage <= 2) {
        endPage = 4;
      } else if (currentPage >= totalPages - 1) {
        startPage = totalPages - 3;
      }

      // Start Dots
      if (startPage > 2) {
        pages.push(
          <span key="start-dots" className={styles.dots}>
            ...
          </span>,
        );
      }

      // Middle Window
      for (let i = startPage; i <= endPage; i++) {
        pages.push(renderButton(i));
      }

      // End Dots
      if (endPage < totalPages - 1) {
        pages.push(
          <span key="end-dots" className={styles.dots}>
            ...
          </span>,
        );
      }

      // Always show Last Page
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
      <button
        type="button"
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={!canGoPrev}
        className={styles.arrowButton}
      >
        <Image
          src={leftArrowIcon}
          alt="Previous"
          width={24}
          height={24}
          // style={{ opacity: canGoPrev ? 1 : 0.3 }} //! Why the hell is there inline css
          className={`${styles.navArrow} ${canGoPrev ? styles.arrowEnabled : styles.arrowDisabled}`}
        />
      </button>

      <div className={styles.pageNumbers}>{renderPageNumbers()}</div>

      <button
        type="button"
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={!canGoNext}
        className={styles.arrowButton}
      >
        <Image
          src={rightArrowIcon}
          alt="Next"
          width={24}
          height={24}
          // style={{ opacity: canGoNext ? 1 : 0.3 }} //! Why the hell is there inline css
          className={`${styles.navArrow} ${canGoNext ? styles.arrowEnabled : styles.arrowDisabled}`}
        />
      </button>
    </div>
  );
}
