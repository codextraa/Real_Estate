import Image from "next/image";
import Link from "next/link";
import styles from "./PropertyCard.module.css";
export default function PropertyCard({ property }) {
  return (
    <div className={styles.cardContainer}>
      <Link href={`/properties/${property.slug}`} className={styles.cardLink}>
        <div className={styles.cardContainer}>
          <div className={styles.imageContainer}>
            <Image
              src={property.image_url}
              alt={property.title}
              width={339}
              height={444}
              className={styles.propertyImage}
            />
          </div>
          <div className={styles.cardContent}>
            <h3 className={styles.propertyTitle}>{property.title}</h3>
            <p className={styles.propertyDescription}>{property.description}</p>
            <span className={styles.learnMore}>Learn More</span>
          </div>
        </div>
      </Link>
    </div>
  );
}
