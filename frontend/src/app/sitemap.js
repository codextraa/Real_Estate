import { getProperties } from "@/libs/api";

export default async function sitemap() {
  const baseUrl = "https://realestate.com";
  const response = await getProperties();
  const properties = response.results || [];

  const propertyEntries = properties.map((property) => ({
    url: `${baseUrl}/properties/${property.slug}`,
    lastModified: property.updated_at || new Date().toISOString(),
    changeFrequency: "weekly",
    priority: 0.8,
  }));

  return [
    {
      url: `${baseUrl}/`,
      lastModified: new Date().toISOString(),
      changeFrequency: "daily",
      priority: 1.0,
    },
    {
      url: `${baseUrl}/properties`,
      lastModified: new Date().toISOString(),
      changeFrequency: "daily",
      priority: 0.9,
    },
    ...propertyEntries,
  ];
}
