"use client";

import { usePathname } from "next/navigation";
import { NavButton } from "@/components/buttons/Buttons";
import styles from "./Navbar.module.css";

export default function Navbar() {
  const pathname = usePathname();
  const isHomePage = pathname === "/";

  if (pathname === "/auth/login" || pathname === "/auth/signup") {
    return null;
  }

  return (
    <nav className={styles.navbar}>
      <Link href="/" className={styles.logo}>
        Estate
      </Link>
      <div className={styles.navLinks}>
        {isHomePage && (
          <NavButton
            className={styles.NavButton1}
            text="Sign Up"
            href="/auth/signup"
          />
        )}
        {!isHomePage && (
          <div>
            <NavButton
              className={styles.NavButton1}
              text="My Listing"
              href="/auth/signup"
            />
            <NavButton
              className={styles.NavButton1}
              text="Create"
              href="/auth/signup"
            />
            <NavButton
              className={styles.NavButton1}
              text="Profile"
              href="/profile"
            />
          </div>
        )}

        <NavButton
          className={styles.NavButton2}
          text="Login"
          href="/auth/login"
        />
      </div>
    </nav>
  );
}
