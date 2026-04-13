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

export async function generateMetadata() {
  const userId = await getUserIdAction();
  if (!userId) {
    return {
      title: "Estate — Discover Your Dream Home",
      description:
        "Explore the most comprehensive collection of real estate listings, from cozy starter homes to luxurious family estates.",
      robots: {
        index: true,
        follow: true,
      },
      openGraph: {
        title: "Estate — Modern Real Estate Solutions",
        description:
          "Effortlessly navigate diverse neighborhoods and find the perfect home.",
        images: ["/real-estate/real-estate.jpg"],
        type: "website",
      },
    };
  }

  return {
    title: "Property Dashboard",
    description:
      "Browse and manage the latest real estate listings curated for you.",
    robots: {
      index: false,
      follow: false,
    },
  };
}
export default async function Page({ searchParams }) {
  const imageUrl = "/real-estate/real-estate.jpg";
  const eIcon = "/assets/E.svg";
  const userId = await getUserIdAction();
  let currentPage, response;

  if (userId) {
    const urlSearchParams = await searchParams;
    currentPage = parseInt(urlSearchParams.page) || 1;
    response = await getProperties({
      page: currentPage,
      ...urlSearchParams,
    });
  }

  return !userId ? (
    <main className={stylesHome.image}>
      <Image
        src={imageUrl}
        alt="Modern city buildings representing real estate"
        fill
        priority
      />

      <section className={stylesHome.container}>
        <figure className={stylesHome.content}>
          <Image
            src={eIcon}
            width={500}
            height={500}
            alt="E"
            className={stylesHome.ieicon}
          />
          <span>state</span>
        </figure>
        <div className={stylesHome.buttons}>
          <HomePageButton text="Get Started" />
        </div>
      </section>
      <footer>
        <Footer />
      </footer>
    </main>
  ) : (
    <main className={styles.background}>
      <header className={styles.image}>
        <figure className={styles.imageWrapper}>
          <Image
            src={imageUrl}
            alt="Modern city buildings representing real estate"
            priority
            fill
            className={styles.imageStyle}
          />
        </figure>
        <div className={styles.container}>
          <figure className={styles.content}>
            <Image
              src={eIcon}
              width={500}
              height={500}
              alt="E"
              className={styles.meicon}
            />
            <span>state</span>
          </figure>
        </div>
      </header>
      <section className={styles.propertiesContainer}>
        <aside>
          <div className={styles.searchbar}>
            <Searchbar />
          </div>
          <div className={styles.dropdowns}>
            <Dropdown />
          </div>
        </aside>
        <article className={styles.propertiesContent}>
          <h1 className={styles.propertiesTitle}>Properties</h1>
          <p className={styles.propertiesDescription}>
            Explore the most current and comprehensive collection of real estate
            listings available right now. We showcase properties that capture
            the diversity and quality of the local market, from cozy starter
            homes to luxurious family estates. Each listing below is curated
            with detailed information, high-resolution imagery, and all the
            essential data you need to compare and evaluate your options. Our
            goal is to streamline your search, making it effortless to navigate
            diverse neighborhoods, compare property features, and connect with
            the perfect home that meets your unique needs.
          </p>
        </article>
        <section className={styles.propertyCards}>
          {response.error ? (
            <div className={styles.errorContainer}>{response.error}</div>
          ) : response.count === 0 ? (
            <div className={styles.noResultsContainer}>No Properties Found</div>
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
        </section>
      </section>
    </main>
  );
}
