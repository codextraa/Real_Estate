import stylesHome from "@/styles/Interface.module.css";
import { HomePageButton } from "@/components/buttons/Buttons";
import { getUserIdAction } from "@/actions/authActions";
import Footer from "@/components/footer/Footer";
import Image from "next/image";
import { getProperties } from "@/libs/api";
import PropertyCard from "@/components/cards/PropertyCard";
import Dropdown from "@/components/dropdowns/Dropdown";
import Searchbar from "@/components/searchbar/Searchbar";
import Pagination from "@/components/pagination/Pagination";
import styles from "@/styles/PropertyPage.module.css";

export default async function Page({ searchParams }) {
  const imageUrl = "/real-estate/real-estate.jpg";
  const userId = await getUserIdAction();
  let currentPage, response;

  if (userId) {
    const urlSearchParams = await searchParams;
    currentPage = urlSearchParams.page || 1;
    response = await getProperties({
      page: currentPage,
      ...urlSearchParams,
    });
  }

  return !userId ? (
    <div className={stylesHome.image}>
      <Image
        src={imageUrl}
        alt="Modern city buildings representing real estate"
        fill
        priority
      />

      <div className={stylesHome.container}>
        <div className={stylesHome.content}>Estate</div>
        <div className={stylesHome.buttons}>
          <HomePageButton text="Get Started" />
        </div>
      </div>
      <Footer />
    </div>
  ) : (
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
        <div className={styles.searchbar}>
          <Searchbar />
        </div>
        <div className={styles.propertyDropdowns}>
          <Dropdown />
        </div>
        <div className={styles.propertiesContent}>
          <div className={styles.propertiesTitle}>Properties</div>
          <div className={styles.propertiesDescription}>
            Explore the most current and comprehensive collection of real estate
            listings available right now. We showcase properties that capture
            the diversity and quality of the local market, from cozy starter
            homes to luxurious family estates. Each listing below is curated
            with detailed information, high-resolution imagery, and all the
            essential data you need to compare and evaluate your options. Our
            goal is to streamline your search, making it effortless to navigate
            diverse neighborhoods, compare property features, and connect with
            the perfect home that meets your unique needs.
          </div>
        </div>
        <div className={styles.propertyCards}>
          {response.error ? (
            <div className={styles.errorContainer}>
              <div>{response.error}</div>
            </div>
          ) : response.count === 0 ? (
            <div className={styles.noResultsContainer}>
              <div>No Properties Found</div>
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
