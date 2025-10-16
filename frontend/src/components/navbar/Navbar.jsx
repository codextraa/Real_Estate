"use client";

import { NavButton } from "@/components/buttons/Buttons";
import Link from "next/link";
import styles from "./Navbar.module.css";

export default function Navbar() {
  return (
    <nav className={styles.navbar}>
      <Link href="/" className={styles.logo}>
        Estate
      </Link>

      <div className={styles.navLinks}>
        <NavButton
          className={styles.NavButton1}
          text="Sign Up"
          href="/auth/signup"
        />

        <NavButton
          className={styles.NavButton2}
          text="Login"
          href="/auth/login"
        />
      </div>
    </nav>
  );
}
