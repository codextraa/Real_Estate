"use client";

import { useState, useEffect } from "react";
import { NavButton } from "@/components/buttons/Buttons";
import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./Navbar.module.css";
import {
  getUserIdAction,
  getUserRoleAction,
  logoutAction,
} from "@/actions/authActions"; // Assuming authAction.js is in /actions

export default function Navbar() {
  const [userId, setUserId] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const pathname = usePathname();

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const id = await getUserIdAction();
        const role = await getUserRoleAction();
        setUserId(id);
        setUserRole(role);
      } catch (error) {
        console.error("Failed to fetch user session data:", error);
        setUserId(null);
        setUserRole(null);
      }
    };
    fetchUserData();
  }, [pathname]);

  const loggedInBaseButtons = [
    { text: "Profile", href: "/profile" },
    { text: "Logout", onClick: logoutAction },
  ];

  let navButtons = [];

  if (userId && userRole) {
    switch (userRole) {
      case "super_user":
        navButtons = [
          { text: "All Listings", href: "/" },
          { text: "Create Admin", href: "/" },
          ...loggedInBaseButtons,
        ];
        break;
      case "admin":
        navButtons = [
          { text: "All Listings", href: "/" },
          { text: "Create", href: "/" },
          ...loggedInBaseButtons,
        ];
        break;
      case "agent":
        navButtons = [
          { text: "My Listings", href: "/" },
          { text: "Create", href: "/" },
          ...loggedInBaseButtons,
        ];
        break;
      default:
        navButtons = loggedInBaseButtons;
        break;
    }
  } else {
    navButtons = [
      { text: "Sign Up", href: "/auth/signup" },
      { text: "Login", href: "/auth/login" },
    ];
  }

  return pathname === "/auth/login" || pathname === "/auth/signup" ? null : (
    <nav className={styles.navbar}>
      <Link href="/" className={styles.logo}>
        Estate
      </Link>

      <div className={styles.navLinks}>
        {navButtons.map((button, index) => (
          <NavButton
            key={index}
            text={button.text}
            href={button.href}
            onClick={button.onClick}
          />
        ))}
      </div>
    </nav>
  );
}
