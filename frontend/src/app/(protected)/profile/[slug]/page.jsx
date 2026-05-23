import { notFound } from "next/navigation";
import { getUser, getAgent } from "@/libs/api";
import Image from "next/image";
import { redirect } from "next/navigation";
import { getUserIdAction, getUserRoleAction } from "@/actions/authActions";
import ProfileCard from "@/components/cards/ProfileCard";
import styles from "@/styles/ProfilePage.module.css";

export async function generateMetadata({ searchParams }) {
  const { user_role } = await searchParams;
  const userId = (await searchParams).user_id || (await getUserIdAction());
  const userRole = user_role || (await getUserRoleAction());

  let response;
  if (userRole === "Agent") {
    response = await getAgent(userId);
  } else {
    response = await getUser(userId);
  }

  if (!response || response.error) return { title: "Profile Not Found" };

  const name =
    userRole === "Agent"
      ? `${response.user.first_name} ${response.user.last_name}`.trim() ||
        response.user.username
      : `${response.first_name} ${response.last_name}`.trim() ||
        response.username;

  return {
    title: `${name} | Profile`,
    description: `View the real estate profile of ${name}.`,
    robots: {
      index: false,
      follow: false,
    },
    openGraph: {
      title: `${name}'s Profile`,
      images: [response.image_url || "/assets/default-avatar.png"],
    },
  };
}

export default async function ProfilePage({ params, searchParams }) {
  const urlParams = await params;
  const urlSearchParams = await searchParams;
  const slug = urlParams.slug;
  let userId = urlSearchParams.user_id;
  let userRole = urlSearchParams.user_role;
  const imgUrl = "/real-estate/real-estate.jpg";

  if (!userId && !userRole) {
    userId = await getUserIdAction();
    userRole = await getUserRoleAction();
  }

  let response;
  let response_slug;
  if (userRole === "Agent") {
    response = await getAgent(userId);
    response_slug = response.user.slug;
  } else {
    response = await getUser(userId);
    response_slug = response.slug;
  }

  if (response.error) {
    console.error(response.error);
    return notFound();
  }

  if (slug !== response_slug) {
    redirect(`/profile/${response_slug}`);
  }

  const containerClassStyle = `${styles.profileCardContainer} ${
    userRole === "Agent" ? styles.profileCardContainerAgent : ""
  }`;

  return (
    <main className={styles.profilePageWrapper}>
      <header className={styles.profileImageWrapper}>
        <Image
          className={styles.profilePageBackgroundImage}
          src={imgUrl}
          alt="background"
          fill
          priority
        />
      </header>
      <section className={styles.profilePageWrapper}>
        <div className={containerClassStyle}>
          <ProfileCard
            userData={response}
            userId={userId}
            userRole={userRole}
          />
        </div>
      </section>
    </main>
  );
}
