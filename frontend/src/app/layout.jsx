import {
  kohSantepheap,
  quando,
  oldStandardTT,
  merriweather,
} from "@/styles/fonts";
import "@/styles/globals.css";
import Loading from "./loading";
import { Suspense } from "react";

const baseUrl = "https://realestate.com";

export const metadata = {
  title: {
    default:
      "Estate — Find Your Dream Property with the help of best AI agents",
    template: "%s | LuxHome Realty",
  },
  description:
    "Browse premium residential and commercial properties. Expert guidance for buying, selling, and investing in real estate.",
  keywords: [
    "Estate",
    "Real Estate",
    "Luxury Homes",
    "Property Search",
    "Homes for Sale",
    "Commercial Real Estate",
  ],
  openGraph: {
    title: "Estate",
    description:
      "Discover the best properties in your area. Modern listings and expert real estate advice.",
    siteName: "LuxHome Realty",
    locale: "en_US",
    url: "https://your-realestate-site.com", // Update this
    images: [
      {
        url: `${baseUrl}/real-estate/real-estate.jpg`,
        width: 1200,
        height: 630,
        alt: "Luxury modern home exterior",
      },
    ],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Estate",
    description: "Find your next home with ease.",
    creator: "@yourbrandhandle", // Update this
    images: [`${baseUrl}/real-estate/real-estate.jpg`],
  },
  robots: {
    index: true,
    follow: true,
    nocache: false, // Changed to false for better performance; only use true if content updates instantly
    googleBot: {
      index: true,
      follow: true,
      "max-snippet": -1,
      "max-image-preview": "large",
      "max-video-preview": -1,
    },
  },
  alternates: {
    canonical: "https://your-realestate-site.com", // Update this
  },
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  interactiveWidget: "resizes-content",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`
      ${kohSantepheap.variable} 
      ${quando.variable} 
      ${oldStandardTT.variable} 
      ${merriweather.variable}
    `}
    >
      <body>
        <Suspense fallback={<Loading />}>{children}</Suspense>
      </body>
    </html>
  );
}
