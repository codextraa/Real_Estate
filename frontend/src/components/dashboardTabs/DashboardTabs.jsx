"use client";

import Link from "next/link";
import styles from "./DashboardTabs.module.css";

export default function DashboardTabs({ currentTab }) {
  return (
    <div className={styles.tabWrapper}>
      <Link
        href="/dashboard?tab=my-listings"
        className={`${styles.tabLink} ${currentTab === "my-listings" ? styles.active : ""}`}
      >
        My Listings
      </Link>

      <Link
        href="/dashboard?tab=reports"
        className={`${styles.tabLink} ${currentTab === "reports" ? styles.active : ""}`}
      >
        My Reports
      </Link>
    </div>
  );
}
