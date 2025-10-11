"use client";

import { NavButton } from "@/components/buttons/Buttons";
import styles from "./Navbar.module.css";

export default function Navbar() {
  return (
    <nav className={styles.navbar}>
      <div className={styles.logo}>Estate</div>
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
