import SignUpPageCard from "@/components/cards/SignUpPageCard";
import SignUpForm from "@/components/forms/SignUpForm";
import Image from "next/image";
import styles from "@/styles/SignUpPage.module.css";

const baseUrl = "https://your-realestate-site.com";

export const metadata = {
  title: "Join Estate — Create Your Account",
  description:
    "Sign up for a Real Estate account to save listings, track property prices, and connect with expert real estate agents.",

  openGraph: {
    title: "Start Your Property Search with LuxHome",
    description:
      "Create an account to get exclusive access to new listings and market insights.",
    url: `${baseUrl}/auth/signup`,
    siteName: "Estate",
    images: [
      {
        url: `${baseUrl}/real-estate/real-estate.jpg`,
        width: 1200,
        height: 630,
        alt: "Sign up for Real Estate",
      },
    ],
    type: "website",
  },

  twitter: {
    card: "summary_large_image",
    title: "Join Estate",
    description: "Your dream home is just a click away. Sign up today.",
    images: [`${baseUrl}/real-estate/real-estate.jpg`],
  },
  robots: {
    index: false,
    follow: true,
  },

  alternates: {
    canonical: `${baseUrl}/auth/signup`,
  },
};

export default async function SignUpPage({ searchParams }) {
  const imgUrl = "/real-estate/real-estate.jpg";
  const { user } = await searchParams;
  // const params = await searchParams;
  // user = params.user

  return user && (user === "customer" || user === "agent") ? (
    <main className={styles.signUpBackground}>
      <section className={styles.signUpPageContainer}>
        <figure className={styles.signUpPictureContainer}>
          <Image
            src={imgUrl}
            alt="Modern city buildings representing real estate"
            width={669}
            height={900}
            priority
          />
        </figure>
        <article className={styles.signUpPageFormContainer}>
          <SignUpForm userType={user} />
        </article>
      </section>
    </main>
  ) : (
    <main className={styles.background}>
      <Image src={imgUrl} alt="background" fill priority />
      <article className={styles.signUpPageCardContainer}>
        <SignUpPageCard />
      </article>
    </main>
  );
}
