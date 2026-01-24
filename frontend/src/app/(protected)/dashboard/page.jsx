import {
  getProperties,
  getListings,
  getReports,
  getMyReports,
} from "@/libs/api";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import { redirect } from "next/navigation";
import Searchbar from "@/components/searchbar/Searchbar";
import PropertyCard from "@/components/cards/PropertyCard";
import DashboardTabs from "@/components/dashboardTabs/DashboardTabs";
import Dropdown from "@/components/dropdowns/Dropdown";
import Pagination from "@/components/pagination/Pagination";
import ReportCard from "@/components/cards/ReportCard";
import ReportFilterTabs from "@/components/reportTabs/ReportTabs";
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
  const urlSearchParams = await searchParams;
  const currentTab =
    urlSearchParams.tab ||
    (userRole === "Default"
      ? "my-reports"
      : userRole === "Agent"
        ? "my-listings"
        : "all-listings");
  const currentPage = parseInt(urlSearchParams.page) || 1;
  const currentStatus = urlSearchParams.status || "PENDING";

  let response = { results: [], total_pages: 0, count: 0 };

  if (currentTab === "my-listings") {
    response = await getListings({
      page: currentPage,
      ...urlSearchParams,
    });
  } else if (currentTab === "all-listings") {
    response = await getProperties({
      page: currentPage,
      ...urlSearchParams,
    });
  } else if (currentTab === "my-reports") {
    response = await getMyReports({
      page: currentPage,
      ...urlSearchParams,
    });
  } else if (currentTab === "all-reports") {
    response = await getReports({
      page: currentPage,
      ...urlSearchParams,
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
        <DashboardTabs currentTab={currentTab} userRole={userRole} />
      </div>
      {currentTab === "my-listings" || currentTab === "all-listings" ? (
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
        <div className={styles.reportsWrapper}>
          <div className={styles.reportHeader}>
            <ReportFilterTabs currentStatus={currentStatus} />
            <div className={styles.propertiesTitle}>Reports</div>
          </div>

          <div className={styles.reportGrid}>
            {(() => {
              const safeResults = response.results;

              const filteredReports = safeResults.filter(
                (r) => r?.status === currentStatus,
              );

              if (filteredReports.length === 0) {
                return (
                  <div className={styles.noResultsContainer}>
                    No {currentStatus} Reports Found
                  </div>
                );
              }
              return filteredReports.map((report) => (
                <ReportCard key={report.id} report={report} />
              ));
            })()}
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
  );
}
