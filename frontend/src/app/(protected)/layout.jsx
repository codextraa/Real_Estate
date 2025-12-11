import Navbar from "@/components/navbar/Navbar";
import styles from "@/styles/ProtectedLayout.module.css";
export default function ProtectedLayout({ children }) {
  return (
    <div className={styles.protectedLayout}>
      <Navbar />
      {children}
    </div>
  );
}
