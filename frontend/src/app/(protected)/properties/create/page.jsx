import { getUserRoleAction } from "@/actions/authActions";
import { notFound } from "next/navigation";
import styles from "@/styles/CreatePropertyPage.module.css";
import ListingForm from "@/components/forms/CreateListingForm";

export const metadata = {
  title: "Create Property Listing",
  description: "List your property for sale or rent.",
  robots: {
    index: false,
    follow: false,
  },
};

export default async function CreatePropertyPage() {
  const userRole = await getUserRoleAction();
  if (userRole !== "Agent") {
    {
      return notFound();
    }
  }

  return (
    <main className={styles.background}>
      <article className={styles.form}>
        <ListingForm />
      </article>
    </main>
  );
}
