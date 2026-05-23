export default function robots() {
  const baseUrl = "https://realestate.com";

  return {
    rules: [
      {
        userAgent: "*",
        allow: [
          "/",
          "/properties",
          "/properties/*", // Assuming you move listings to public   // If you make agent profiles public
        ],
        disallow: [
          "/api/",
          "/dashboard",
          "/login",
          "/signup",
          "/*/edit", // Blocks any edit page under any slug
          "/*/create", // Blocks create pages
        ],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
