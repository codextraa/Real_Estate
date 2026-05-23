import { notFound, redirect } from "next/navigation";
import { getProperty, getProperties } from "@/libs/api";
import PropertyCard from "@/components/cards/PropertyCard";
import Dropdown from "@/components/dropdowns/Dropdown";
import PropertyImageCard from "@/components/cards/PropertyImageCard";
import PropertyDetailCard from "@/components/cards/PropertyDetailCard";
import styles from "@/styles/PropertySlugPage.module.css";

export async function generateMetadata({ params }) {
  const { slug } = await params;
  const propertyId = slug.split("-").pop();
  const response = await getProperty(propertyId);
  if (!response || response.error) {
    return {
      title: "Property Not Found",
      description: "The property you are looking for does not exist.",
      alternates: {
        canonical: `https://realestate.com/properties/${params.slug}`,
      },
      robots: { index: false },
    };
  }
  return {
    title: `${response.title} | Real Estate Listings`,
    description: `${response.description}`,
    alternates: {
      canonical: `https://realestate.com/properties/${params.slug}`,
    },
    openGraph: {
      title: response.title,
      description: response.description,
      images: [response.image_url],
    },
    robots: {
      index: true,
      follow: true,
      nocache: true,
    },
  };
}

export default async function PropertyPage({ params }) {
  const { slug } = await params;
  const propertyId = slug.split("-").pop();

  if (!propertyId) {
    return notFound();
  }

  const response = await getProperty(propertyId);

  if (response.error) {
    return notFound();
  }

  if (response.slug !== slug) {
    redirect(`/properties/${response.slug}`);
  }

  const recommendedProperties = await getProperties();

  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SingleFamilyResidence",
    name: response.title,
    description: response.description,
    image: response.image_url,
    address: {
      "@type": "PostalAddress",
      streetAddress: response.address,
      addressLocality: response.city,
      addressRegion: response.state,
      postalCode: response.zip_code,
      addressCountry: response.country,
    },
    offers: {
      "@type": "Offer",
      priceCurrency: "USD",
      price: response.price,
      availability: response.availability
        ? "https://schema.org/InStock"
        : "https://schema.org/OutOfStock",
    },
  };

  return (
    <main className={styles.propertyPageBackground}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <article className={styles.propertyPageContainerBackground}>
        <section className={styles.propertyPageContainer1}>
          <header className={styles.propertyHeader}>
            <h1 className={styles.profileDetailTitle}>{response.title}</h1>
          </header>
          <section className={styles.propertyDetailContainer}>
            <figure className={styles.propertyImageCard}>
              <PropertyImageCard image={response.image_url} />
            </figure>
            <article className={styles.propertyDetailCard}>
              <PropertyDetailCard property={response} />
            </article>
          </section>
          <section className={styles.propertyDetailDescription}>
            <h2>{response.description}</h2>
          </section>
        </section>
      </article>
      <section className={styles.propertyPageContainer2}>
        <nav className={styles.propertyDetailDropdowns}>
          <Dropdown />
        </nav>
        <header className={styles.recommendationTitle}>Recommendations</header>
        <article className={styles.recommendationCards}>
          <div className={styles.recommendationGrid}>
            {recommendedProperties.results.slice(0, 6).map((property) => (
              <PropertyCard key={property.id} property={property} />
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}
