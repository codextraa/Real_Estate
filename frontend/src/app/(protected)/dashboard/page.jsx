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
import SignUpForm from "@/components/forms/SignUpForm";

const imageUrl = "/real-estate/real-estate.jpg";

export default async function DashboardPage({ searchParams }) {
  const userId = await getUserIdAction();
  const userRole = await getUserRoleAction();
  if (!userId || !userRole) {
    redirect(DEFAULT_LOGIN_REDIRECT);
  }
  const urlSearchParams = await searchParams;
  const validSearchParams = { ...urlSearchParams };
  const currentTab =
    urlSearchParams.tab ||
    (userRole === "Default"
      ? "my-reports"
      : userRole === "Agent"
        ? "my-listings"
        : "all-listings");
  const currentPage = parseInt(urlSearchParams.page) || 1;
  const currentStatus = urlSearchParams.status || "ALL";

  let response = { results: [], total_pages: 0, count: 0 };

  if (currentTab === "my-listings") {
    response = await getListings({
      page: currentPage,
      ...validSearchParams,
    });
  } else if (currentTab === "all-listings") {
    response = await getProperties({
      page: currentPage,
      ...validSearchParams,
    });
  } else if (currentTab === "my-reports") {
    let statusFilter = urlSearchParams.status;
    if (statusFilter === "ALL") {
      delete validSearchParams.status;
    }
    response = await getMyReports({
      page: currentPage,
      ...validSearchParams,
    });
  } else if (currentTab === "all-reports") {
    let statusFilter = urlSearchParams.status;
    if (statusFilter === "ALL") {
      delete validSearchParams.status;
    }
    response = await getReports({
      page: currentPage,
      ...validSearchParams,
    });
  }

  return (
    <main className={styles.background}>
      <header className={styles.image}>
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
      </header>
      <nav className={styles.tabs}>
        <DashboardTabs currentTab={currentTab} userRole={userRole} />
      </nav>
      {currentTab === "my-listings" || currentTab === "all-listings" ? (
        <section className={styles.propertiesContainer}>
          <aside className={styles.searchFilterSection}>
            <div className={styles.searchbar}>
              <Searchbar />
            </div>
            <div className={styles.dropdowns}>
              <Dropdown />
            </div>
          </aside>
          <article className={styles.propertiesContent}>
            <h2 className={styles.propertiesTitle}>Properties</h2>
            <p className={styles.propertiesDescription}>
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
            </p>
          </article>
          <div className={styles.propertyCards}>
            {response.error ? (
              <p className={styles.errorContainer}>{response.error}</p>
            ) : response.count === 0 ? (
              <p className={styles.noResultsContainer}>No Properties Found</p>
            ) : (
              <div className={styles.propertyGridPagination}>
                <div className={styles.propertyGrid}>
                  {response.results.map((property) => (
                    <PropertyCard key={property.id} property={property} />
                  ))}
                </div>
                <footer className={styles.paginationContainer}>
                  <Pagination
                    currentPage={currentPage}
                    totalPages={response.total_pages}
                  />
                </footer>
              </div>
            )}
          </div>
        </section>
      ) : currentTab === "create-admin" ? (
        <section className={styles.createAdminForm}>
          <SignUpForm userType="admin" />
        </section>
      ) : (
        <section className={styles.reportsWrapper}>
          <nav className={styles.reportHeader}>
            <ReportFilterTabs currentStatus={currentStatus} />
          </nav>
          <div className={styles.reportContent}>
            <h2 className={styles.reportTitle}>Reports</h2>
            <div className={styles.reportGrid}>
              {(() => {
                if (response.results && response.results?.length === 0) {
                  return (
                    <p className={styles.noResultsContainer}>
                      No {currentStatus} Reports Found
                    </p>
                  );
                }
                return response.results.map((report) => (
                  <ReportCard key={report.id} report={report} />
                ));
              })()}
            </div>
          </div>
          <footer className={styles.paginationContainer}>
            <Pagination
              currentPage={currentPage}
              totalPages={response.total_pages}
            />
          </footer>
        </section>
      )}
    </main>
  );
}
