import UpdateListingForm from "@/components/forms/UpdateListingForm";
import styles from "@/styles/CreatePropertyPage.module.css";
import { notFound } from "next/navigation";
import { getProperty } from "@/libs/api";

function parseAddress(addressString) {
  const address = {};
  const pairs = addressString.split(", ");

  pairs.forEach((pair) => {
    const [key, value] = pair.split("=");
    address[key] = value;
  });

  return address;
}

export default async function UpdateListingPage({ params }) {
  const propertySlug = await params;
  const parts = propertySlug.slug.split("-");
  const propertyIdString = parts[parts.length - 1];
  const propertyId = parseInt(propertyIdString);

  const propertyData = await getProperty(propertyId);
  if (propertyData.error) {
    return notFound();
  }

  const parsedAddress = parseAddress(propertyData.address);
  const enrichedPropertyData = {
    ...propertyData,
    address: parsedAddress,
  };

  return (
    <div className={styles.background}>
      <div className={styles.form}>
        <UpdateListingForm
          propertyId={propertyId}
          initialData={enrichedPropertyData}
        />
      </div>
    </div>
  );
}
