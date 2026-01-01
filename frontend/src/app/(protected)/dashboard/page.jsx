import { getListings } from "@/libs/api";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import { redirect, notFound } from "next/navigation";
import Searchbar from "@/components/searchbar/Searchbar";
import PropertyCard from "@/components/cards/PropertyCard";
import DashboardTabs from "@/components/dashboardTabs/DashboardTabs";
import Dropdown from "@/components/dropdowns/Dropdown";
import Pagination from "@/components/pagination/Pagination";
import styles from "@/styles/PropertyPage.module.css";
import Image from "next/image";
import { DEFAULT_LOGIN_REDIRECT } from "@/route";

const imageUrl = "/real-estate/real-estate.jpg";

export default async function DashboardPage({ searchParams }) {
  const userId = await getUserIdAction();
  const userRole = await getUserRoleAction();
  if (!userId || !userRole) {
    redirect(DEFAULT_LOGIN_REDIRECT);
  }
  if (userRole !== "Agent") {
    return notFound();
  }
  const query = await searchParams;
  const currentTab = query.tab || "my-listings";
  const currentPage = parseInt(query.page) || 1;

  let response = [];
  if (currentTab === "my-listings") {
    response = await getListings({
      page: currentPage,
      ...query,
    });
  }

  return (
    <div className={styles.background}>
      <div className={styles.image}>
        <div className={styles.imageWrapper}>
          <Image
            src={imageUrl}
            alt="Modern city buildings representing real estate"
            priority
            fill
            className={styles.imageStyle}
          />
        </div>
        <div className={styles.container}>
          <div className={styles.content2}>My Dashboard</div>
        </div>
      </div>
      <div className={styles.tabs}>
        <DashboardTabs currentTab={currentTab} />
      </div>
      {currentTab === "my-listings" ? (
        <div className={styles.propertiesContainer}>
          <div className={styles.searchbar}>
            <Searchbar />
          </div>
          <div className={styles.dropdowns}>
            <Dropdown />
          </div>
          <div className={styles.propertiesContent}>
            <div className={styles.propertiesTitle}>Properties</div>
            <div className={styles.propertiesDescription}>
              Explore the most current and comprehensive collection of real
              estate listings available right now. We showcase properties that
              capture the diversity and quality of the local market, from cozy
              starter homes to luxurious family estates. Each listing below is
              curated with detailed information, high-resolution imagery, and
              all the essential data you need to compare and evaluate your
              options. Our goal is to streamline your search, making it
              effortless to navigate diverse neighborhoods, compare property
              features, and connect with the perfect home that meets your unique
              needs.
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
      ) : (
        <div className={styles.reportsContent}>
          {/* My Reports Content (Null for now) */}
          <p>No reports available yet.</p>
        </div>
      )}
    </div>
  );
}
