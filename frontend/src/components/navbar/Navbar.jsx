import { NavButton } from "@/components/buttons/Buttons";
import Link from "next/link";
import Image from "next/image";
import styles from "./Navbar.module.css";
import {
  getUserIdAction,
  getUserRoleAction,
  logoutAction,
} from "@/actions/authActions";

export default async function Navbar() {
  const eIcon = "/assets/E.svg";
  const userId = await getUserIdAction();
  const userRole = await getUserRoleAction();

  const loggedInBaseButtons = [
    { text: "Dashboard", href: "/dashboard" },
    { text: "Profile", href: "/profile" },
    { text: "Log Out", onClick: logoutAction },
  ];

  let navButtons = [];

  if (userId && userRole) {
    navButtons = loggedInBaseButtons;
  } else {
    navButtons = [
      { text: "Sign Up", href: "/auth/signup" },
      { text: "Login", href: "/auth/login" },
    ];
  }

  return (
    <nav className={styles.navbar}>
      <Link href="/" className={styles.logo}>
        <Image
          src={eIcon}
          width={500}
          height={500}
          alt="E"
          className={styles.icon}
        />
        <span>state</span>
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
