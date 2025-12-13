import { getProperties } from "@/libs/api";
import PropertyCard from "@/components/cards/PropertyCard";
import Dropdown from "@/components/dropdowns/Dropdown";
import Pagination from "@/components/pagination/Pagination";
import styles from "@/styles/PropertyPage.module.css";
import Image from "next/image";

export default async function PropertiesPage({ searchParams }) {
  const urlSearchParams = await searchParams;
  const currentPage = urlSearchParams.page || 1;
  const imageUrl = "/real-estate/real-estate.jpg";
  const response = await getProperties({
    page: currentPage,
    ...urlSearchParams,
  });

  return (
    <div className={styles.background}>
      <div className={styles.image}>
        <div className={styles.imageWrapper}>
          <Image
            src={imageUrl}
            alt="Modern city buildings representing real estate"
            priority
            className={styles.imageStyle}
            width={100}
            height={100}
          />
        </div>
        <div className={styles.container}>
          <div className={styles.content}>Estate</div>
        </div>
      </div>
      <div className={styles.propertiesContainer}>
        <div className={styles.propertyDropdowns}>
          <Dropdown />
        </div>
        <div className={styles.propertiesContent}>
          <div className={styles.propertiesTitle}>Properties</div>
          <div className={styles.propertiesDescription}>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin ac
            finibus mi, sit amet finibus dui. Vivamus vel nulla risus. Ut in
            neque aliquet, lacinia est ac, efficitur ex. Proin tempor eros eget
            nibh malesuada eleifend. Maecenas ac porttitor erat.
          </div>
        </div>
        <div className={styles.propertyCards}>
          {response.error ? (
            <div className={styles.errorContainer}>
              <div>{response.error}</div>
            </div>
          ) : (
            <div className={styles.propertyGridPagination}>
              <div className={styles.propertyGrid}>
                {response.results.map((property) => (
                  <PropertyCard key={property.id} property={property} />
                ))}
              </div>
              <div className={styles.paginationContainer}>
                <Pagination
                  currentPage={currentPage}
                  totalPages={response.total_pages}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
