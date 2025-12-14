import { getProperty, getProperties } from "@/libs/api";
import PropertyCard from "@/components/cards/PropertyCard";
import Dropdown from "@/components/dropdowns/Dropdown";
import PropertyImageCard from "@/components/cards/PropertyImageCard";
import PropertyDetailCard from "@/components/cards/PropertyDetailCard";
import styles from "@/styles/PropertyPage.module.css";

export default async function ProfileCard({ searchParams }) {
  const urlSearchParams = await searchParams;
  const propertyId = urlSearchParams.id;
  const response = await getProperty(propertyId);
  const recommendedProperties = await getProperties();

  return (
    <div className={styles.propertyPageBackground}>
      <div className={styles.propertyPageContainer1}>
        <div className={styles.profileDetailTitle}>{response.title}</div>
        <div className={styles.propertyDetailContainer}>
          <div className={styles.propertyImageCard}>
            <PropertyImageCard image={response.image_url} />
          </div>
          <div className={styles.propertyDetailCard}>
            <PropertyDetailCard property={response} />
          </div>
        </div>
        <div className={styles.propertyDetailDescription}>
          <h2>{response.description}</h2>
        </div>
      </div>
      <div className={styles.propertyPageContainer2}>
        <div className={styles.propertyDetailDropdowns}>
          <Dropdown />
        </div>
        <div className={styles.recommendationSection}>
          <h4>Recommendation</h4>
          {recommendedProperties.results.slice(0, 6).map((property) => (
            <PropertyCard key={property.id} property={property} />
          ))}
        </div>
      </div>
    </div>
  );
}
