import { NavButton } from "@/components/buttons/Buttons";
import Link from "next/link";
import styles from "./Navbar.module.css";
import {
  getUserIdAction,
  getUserRoleAction,
  logoutAction,
} from "@/actions/authActions"; // Assuming authAction.js is in /actions

export default async function Navbar() {
  const userId = await getUserIdAction();
  const userRole = await getUserRoleAction();

  const loggedInBaseButtons = [
    { text: "Profile", href: "/profile" },
    { text: "Logout", onClick: logoutAction },
  ];

  let navButtons = [];

  if (userId && userRole) {
    if (userRole === "Superuser") {
      navButtons = [
        { text: "All Listings", href: "/" },
        { text: "Create Admin", href: "/" },
        ...loggedInBaseButtons,
      ];
    } else if (userRole === "Admin") {
      navButtons = [
        { text: "All Listings", href: "/" },
        ...loggedInBaseButtons,
      ];
    } else if (userRole === "Agent") {
      navButtons = [
        { text: "My Listings", href: "/" },
        { text: "Create", href: "/properties/create" },
        ...loggedInBaseButtons,
      ];
    } else {
      navButtons = loggedInBaseButtons;
    }
  } else {
    navButtons = [
      { text: "Sign Up", href: "/auth/signup" },
      { text: "Login", href: "/auth/login" },
    ];
  }

  return (
    <nav className={styles.navbar}>
      <Link href="/" className={styles.logo}>
        Estate
      </Link>

      <div className={styles.navLinks}>
        {navButtons.map((button, index) => (
          <NavButton
            key={index}
            text={button.text}
            href={button.href ? button.href : null}
            onClick={button.onClick ? button.onClick : null}
          />
        ))}
      </div>
    </nav>
  );
}
