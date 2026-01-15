"use client";

import Link from "next/link";
import styles from "./DashboardTabs.module.css";

export default function DashboardTabs({ currentTab, userRole }) {
  // Define helper to check active state
  const isActive = (tab) => (currentTab === tab ? styles.active : "");

  return (
    <div className={styles.tabWrapper}>
      {/* SUPERUSER VIEW */}
      {userRole === "Superuser" && (
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
          <Link
            href="/dashboard?tab=create-admin"
            className={`${styles.tabLink} ${isActive("create-admin")}`}
          >
            Create Admin
          </Link>
        </>
      )}

      {/* AGENT VIEW */}
      {userRole === "Agent" && (
        <>
          <Link
            href="/dashboard?tab=my-listings"
            className={`${styles.tabLink} ${isActive("my-listings")}`}
          >
            My Listings
          </Link>
          <Link
            href="/dashboard?tab=my-reports"
            className={`${styles.tabLink} ${isActive("my-reports")}`}
          >
            My Reports
          </Link>
          <Link
            href="/properties/create"
            className={`${styles.tabLink} ${isActive("create-listing")}`}
          >
            Create Listing
          </Link>
        </>
      )}

      {/* STAFF VIEW */}
      {userRole === "Staff" && (
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
        </>
      )}

      {/* DEFAULT VIEW (Else) */}
      {!["Superuser", "Agent", "Staff"].includes(userRole) && (
        <Link
          href="/dashboard?tab=my-reports"
          className={`${styles.tabLink} ${isActive("my-reports")}`}
        >
          My Reports
        </Link>
      )}
    </div>
  );
}
