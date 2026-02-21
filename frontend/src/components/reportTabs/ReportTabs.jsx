"use client";

import { useRouter, useSearchParams } from "next/navigation";
import styles from "./ReportTabs.module.css";

export default function ReportFilterTabs({ currentStatus }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const statuses = ["ALL", "PENDING", "PROCESSING", "COMPLETED", "FAILED"];

  const handleStatusChange = (status) => {
    const params = new URLSearchParams(searchParams);
    params.set("status", status);
    params.set("page", "1");
    router.push(`/dashboard?${params.toString()}`);
  };

  return (
    <div className={styles.filterContainer}>
      {statuses.map((status) => (
        <button
          key={status}
          onClick={() => handleStatusChange(status)}
          className={`${styles.filterBtn} ${currentStatus === status ? styles.active : ""}`}
        >
          {status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()}
        </button>
      ))}
    </div>
  );
}
