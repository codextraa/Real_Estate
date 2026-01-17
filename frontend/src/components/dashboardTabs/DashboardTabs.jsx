"use client";

import Link from "next/link";
import styles from "./DashboardTabs.module.css";

export default function DashboardTabs({ currentTab, userRole }) {
  const isActive = (tab) => (currentTab === tab ? styles.active : "");

  return (
    <div className={styles.tabWrapper}>
      {(userRole === "Superuser" || userRole === "Admin") && (
        <>
          <Link
            href="/dashboard?tab=all-listings"
            className={`${styles.tabLink} ${isActive("all-listings")}`}
          >
            All Listings
          </Link>
          <Link
            href="/dashboard?tab=all-reports"
            className={`${styles.tabLink} ${isActive("all-reports")}`}
          >
            All Reports
          </Link>
          {userRole === "Superuser" && (
            <Link
              href="/dashboard?tab=create-admin"
              className={`${styles.tabLink} ${isActive("create-admin")}`}
            >
              Create Admin
            </Link>
          )}
        </>
      )}

      {(userRole === "Agent" || userRole === "Default") && (
        <>
          {userRole === "Agent" && (
            <Link
              href="/dashboard?tab=my-listings"
              className={`${styles.tabLink} ${isActive("my-listings")}`}
            >
              My Listings
            </Link>
          )}
          <Link
            href="/dashboard?tab=my-reports"
            className={`${styles.tabLink} ${isActive("my-reports")}`}
          >
            My Reports
          </Link>
          {userRole === "Agent" && (
            <Link
              href="/properties/create"
              className={`${styles.tabLink} ${isActive("create-listing")}`}
            >
              Create Listing
            </Link>
          )}
        </>
      )}
    </div>
  );
}
