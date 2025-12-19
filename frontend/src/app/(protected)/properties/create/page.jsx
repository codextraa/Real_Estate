import { getUserRoleAction } from "@/actions/authActions";
import { notFound } from "next/navigation";
import styles from "@/styles/CreatePropertyPage.module.css";
import ListingForm from "@/components/forms/ListingForm";

export default async function CreatePropertyPage() {
  const userRole = await getUserRoleAction();
  if (userRole !== "Agent") {
    {
      return notFound();
    }
  }
  return (
    <div className={styles.background}>
      <div className={styles.form}>
        <ListingForm />
      </div>
    </div>
  );
}
